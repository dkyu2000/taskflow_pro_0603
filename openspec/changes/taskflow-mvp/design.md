## Context

그린필드 TaskFlow MVP의 첫 구현이다. 단일 진실 공급원은 `docs/`의 PDF 2개와 `CLAUDE.md`다. 스택은 확정(FastAPI + SQLite/Neon + Vanilla JS/Tailwind + Vercel)이며, 라이브러리·디렉토리 구조·마이그레이션 도구·FE 파일구조는 클로드코드 판단에 위임됐다. 본 문서는 그 위임 영역의 기술 결정과, 탐색에서 확정한 7건 + 스코프 추가 2건(Swagger·테스트)의 구현 방식을 정한다.

## Goals / Non-Goals

**Goals:**
- 18개 API·4테이블·9화면을 명세 그대로 구현하고 로컬에서 단일 명령으로 실행.
- 로컬 SQLite ↔ 운영 Neon을 `DATABASE_URL`만으로 전환(코드 양쪽 호환).
- `/docs`(Swagger)에서 전 엔드포인트 수동 테스트 가능.
- `pytest`로 핵심 규칙 자동 검증 가능.
- Vercel(FE+BE) 자동 배포 가능한 구조.

**Non-Goals:**
- 알림·파일첨부·전문검색·다국어·WebSocket·JWT 갱신/블랙리스트·팀 추방/역할변경/초대코드 재발급(전부 범위 외).
- 폴링 고급 복원력(exponential backoff·offline 큐·pull-to-refresh) — MVP 제외.
- 측정 도구 기반 성능 검증(드래그 50ms 등은 정성 검증).

## Decisions

### D1. ORM·검증·인증 라이브러리
- **SQLAlchemy 2.x (async) + Alembic** 마이그레이션. 대안 Tortoise ORM은 Postgres/SQLite 양쪽 성숙도·자료량에서 SQLAlchemy가 우위.
- **pydantic v2** 요청/응답 스키마(= Swagger 모델 + 서버 검증 동시 충족).
- **passlib[bcrypt]** 해시, **python-jose[cryptography]** JWT(HS256). 대안 PyJWT도 가능하나 jose가 명세 예시와 일치.
- SQLite/Postgres 호환을 위해 타입은 `Integer`/`String`/`Text`/`DateTime(timezone=True)`만 사용. Postgres 전용 타입 회피.

### D2. 디렉토리 구조 (모놀리식, Vercel 호환)
```
/
├─ api/                 # Vercel Serverless 진입점 (FastAPI app export)
│  └─ index.py
├─ app/
│  ├─ main.py           # FastAPI 인스턴스, 라우터 등록, 에러 핸들러, CORS
│  ├─ config.py         # DATABASE_URL 등 설정
│  ├─ db.py             # 엔진/세션 (sqlite ↔ postgres 분기)
│  ├─ models.py         # SQLAlchemy 4테이블
│  ├─ schemas.py        # pydantic 모델 (Swagger 예시 포함)
│  ├─ security.py       # JWT 발급/검증, bcrypt
│  ├─ deps.py           # get_current_user, require_membership 의존성
│  ├─ errors.py         # 표준 에러 + 예외→{error:{...}} 핸들러
│  └─ routers/          # auth.py, teams.py, tasks.py, messages.py
├─ frontend/            # 정적 파일 (MPA)
│  ├─ login.html, signup.html, team-select.html, kanban.html, chat.html ...
│  ├─ js/api.js         # fetch 래퍼: Bearer 자동첨부, 401→/login
│  └─ js/*.js           # 화면별 스크립트
├─ tests/               # pytest
├─ requirements.txt
├─ vercel.json          # FE 정적 + /api 라우팅
└─ taskflow.db          # (git ignore)
```
- 로컬 BE: `uvicorn app.main:app --reload`. 로컬 FE: `python -m http.server`(frontend/). 운영: `api/index.py`가 동일 `app`을 Vercel Functions로 노출.

### D3. 인가 모델 (횡단)
- `get_current_user`: JWT 검증 실패/만료 → `401 TOKEN_EXPIRED`.
- `require_membership(team_id)`: `current_user.team_id == team_id` 아니면 `403 FORBIDDEN`. 모든 `/teams/{id}/*`에 적용.
- `/tasks/{id}`·`/messages/{id}`(팀 id 미포함 경로)는 리소스 로드 후 그 리소스의 `team_id`로 멤버십 검증 → 비멤버 403, 없으면 404. (존재 노출 최소화 위해 멤버십 우선)
- task DELETE: creator_id == me OR team.owner_id == me. message DELETE: user_id == me(owner 예외 없음 → `NOT_OWNER`).

### D4. 채팅 폴링 — id 커서
- `since`는 정수 message.id. 쿼리 `WHERE team_id=? AND id > :since ORDER BY id ASC`. `since` 없으면 `ORDER BY id DESC LIMIT 50` 후 역순 반환.
- 인덱스 `messages(team_id, id)`로 커서 조회 O(log n). "메시지 누락 0건"은 id 단조증가로 보장(같은 초 충돌 무관).

### D5. 시간대 직렬화 — KST
- 저장: `DateTime(timezone=True)`에 KST(`+09:00`) aware datetime 저장. 서버 기본 tz를 Asia/Seoul로 고정(`now()` 헬퍼 사용).
- 직렬화: pydantic이 ISO8601 오프셋 포함 출력 → `...+09:00`. `Z` 출력 경로(naive UTC) 금지.

### D6. 초대코드 생성
- `random` 4 대문자 + `-` + 4 숫자. UNIQUE 충돌 시 재생성(최대 N회). 형식·존재 검증은 join 시 클라+서버 양쪽.

### D7. 프론트엔드 — MPA
- 화면별 독립 HTML. 공통 `api.js`가 localStorage 토큰 관리·`Authorization` 자동 첨부·401 응답 시 토큰 삭제 후 `location.href='/login'`(직전 URL 저장 X).
- 페이지 진입 시 가드: 토큰 없으면 즉시 `/login`; 로그인 후 `team_id` NULL이면 `team-select`, 아니면 `kanban`.
- 칸반 드래그: HTML5 native drag → drop 시 `PATCH /tasks/{id}/status`. 채팅: `setInterval` 5초 + `since=<lastId>`.
- Tailwind: MVP는 CDN(빌드 단계 생략, 단순성). 운영 최적화는 범위 외.

### D8. Swagger/OpenAPI
- FastAPI 기본 `/docs`·`/redoc` 유지. 각 라우트에 `tags`, `response_model`, `responses`(에러 코드 예시), pydantic `examples` 부여. 18개 전부 모델 명시.

### D9. 테스트 (스코프 추가)
- pytest + `TestClient`. `conftest.py`에서 인메모리 SQLite(`sqlite://` + StaticPool) 엔진을 의존성 오버라이드로 주입, 테스트별 격리.
- 커버: 회원가입/로그인(열거 방지)·JWT 만료·팀 생성/합류/leave(owner 거부)·태스크 CRUD/상태/필터/assignee 검증·삭제 권한·메시지 1000자/폴링 id커서 누락0·삭제 권한·비멤버 403 격리·에러 표준 형태.

## Risks / Trade-offs

- **Vercel Serverless + SQLite 비호환** → 운영은 반드시 Neon(Postgres). SQLite는 로컬 전용. 코드가 Postgres 전용 기능을 쓰지 않도록 D1 타입 제약 유지.
- **Serverless 콜드스타트로 폴링 지연 체감** → MVP 허용. 폴링 주기 5초로 흡수.
- **async SQLAlchemy + SQLite 드라이버(aiosqlite) 엣지** → 테스트는 StaticPool/단일 연결로 안정화. 문제 시 동기 SQLAlchemy로 폴백 가능(라우트 시그니처 영향 최소).
- **KST aware datetime 누락 시 `Z` 새어나감** → `created_at`은 공통 `now_kst()` 헬퍼로만 생성하고, 모델 default도 동일 헬퍼 사용. 직렬화 회귀 테스트 1건 포함.
- **스코프 추가(테스트·Swagger)가 PDF "범위 외"와 충돌** → proposal에 명시 기록. 구현 후 `CLAUDE.md` 범위 외 목록에서 해당 2건 제외하도록 갱신.
- **`/tasks/{id}` 404 vs 403 순서** → 멤버십 우선(403) 후 존재(404)로 정보 노출 최소화. 단 같은 팀 리소스의 미존재는 404 반환.
