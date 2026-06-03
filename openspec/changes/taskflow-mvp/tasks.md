## 1. 프로젝트 셋업

- [ ] 1.1 디렉토리 구조 생성(`app/`, `app/routers/`, `frontend/`, `frontend/js/`, `tests/`, `api/`)
- [ ] 1.2 `requirements.txt` 작성(fastapi, uvicorn, sqlalchemy, alembic, aiosqlite, asyncpg, pydantic, passlib[bcrypt], python-jose[cryptography], pytest, httpx)
- [ ] 1.3 `.gitignore`에 `taskflow.db`, `__pycache__`, 가상환경 추가
- [ ] 1.4 `app/config.py`: `DATABASE_URL` 기본값 `sqlite:///./taskflow.db`, JWT 시크릿·만료(24h), CORS 도메인 설정 로드

## 2. DB·모델·스키마 (platform-foundation)

- [ ] 2.1 `app/db.py`: `DATABASE_URL`로 엔진/세션 생성, sqlite↔postgres 분기(SQLite/Postgres 호환 타입만)
- [ ] 2.2 `app/models.py`: `users`/`teams`/`tasks`/`messages` 4테이블 + FK(`team_id` nullable, `assignee_id` nullable) + `DateTime(timezone=True)`
- [ ] 2.3 인덱스 추가: `tasks(team_id, created_at)`, `messages(team_id, id)`, `teams(invite_code)`, `users(team_id)`
- [ ] 2.4 `now_kst()` 헬퍼(+09:00 aware) 작성, 모델 `created_at` default에 적용
- [ ] 2.5 Alembic 초기 마이그레이션 생성·적용(또는 startup create_all)
- [ ] 2.6 `app/schemas.py`: 요청/응답 pydantic 모델 + Swagger `examples`(에러 표준, 사용자, 팀, 태스크, 메시지)

## 3. 공통 인증·인가·에러 (auth · platform-foundation)

- [ ] 3.1 `app/security.py`: bcrypt 해시/검증, JWT 발급(24h)·디코드
- [ ] 3.2 `app/errors.py`: 표준 예외 클래스 + 핸들러로 `{ error: { code, message, meta } }` 통일, 코드 매핑(VALIDATION_ERROR/TOO_LONG/INVALID_CREDENTIALS/TOKEN_EXPIRED/FORBIDDEN/NOT_OWNER/NOT_FOUND/EMAIL_TAKEN/OWNER_CANNOT_LEAVE)
- [ ] 3.3 `app/deps.py`: `get_current_user`(만료/누락→401 TOKEN_EXPIRED), `require_membership(team_id)`(비멤버→403 FORBIDDEN)
- [ ] 3.4 `app/main.py`: FastAPI 인스턴스, 라우터 등록, 예외 핸들러·CORS 등록, `/docs`·`/redoc` 유지

## 4. Auth API (auth)

- [ ] 4.1 `POST /auth/signup`: 이메일 형식·비번 8자 검증, 중복→409 EMAIL_TAKEN, 성공 201+JWT
- [ ] 4.2 `POST /auth/login`: 검증 후 200+JWT(24h), 실패는 INVALID_CREDENTIALS 통일(이메일 열거 방지)
- [ ] 4.3 `POST /auth/logout`: stateless 200
- [ ] 4.4 `GET /auth/me`: 현재 사용자 반환, 토큰 만료/누락→401

## 5. Team API (team-membership)

- [ ] 5.1 초대코드 생성기(`^[A-Z]{4}-[0-9]{4}$`, UNIQUE 충돌 재생성)
- [ ] 5.2 `POST /teams`: 이름 1–30 검증, 이미 소속→409, 생성+owner 지정+`team_id` 갱신, 201
- [ ] 5.3 `POST /teams/join`: 형식 400 / 미존재 404 / 이미 소속 409 / 성공 200+팀정보
- [ ] 5.4 `GET /teams/{id}`: 멤버만, 비멤버 403
- [ ] 5.5 `GET /teams/{id}/members`: owner/member 구분 포함, 비멤버 403
- [ ] 5.6 `DELETE /teams/{id}/leave`: owner→409 OWNER_CANNOT_LEAVE, member→team_id NULL + 본인 작성물 보존 + 본인 assignee 카드 assignee_id NULL

## 6. Task API (kanban-tasks)

- [ ] 6.1 `GET /teams/{id}/tasks`: created_at desc, 필터 all/@me(assignee)/미할당, 비멤버 403
- [ ] 6.2 `POST /teams/{id}/tasks`: title 1–100, 기본 TODO, assignee 같은 팀 검증, 201
- [ ] 6.3 `GET /tasks/{id}`: 리소스 team_id로 멤버십 검증(비멤버 403, 미존재 404)
- [ ] 6.4 `PUT /tasks/{id}`: title/assignee 수정, assignee 같은 팀 검증
- [ ] 6.5 `PATCH /tasks/{id}/status`: TODO|DOING|DONE만, 잘못된 값 400
- [ ] 6.6 `DELETE /tasks/{id}`: creator 또는 owner만, 그 외 403

## 7. Chat API (team-chat)

- [ ] 7.1 `POST /teams/{id}/messages`: 1–1000자 검증(초과 400 TOO_LONG+meta), 비멤버 403, 201
- [ ] 7.2 `GET /teams/{id}/messages`: since 없으면 최근 50, `since=<id>`면 `id > since`, 빈 배열 허용, 비멤버 403
- [ ] 7.3 `DELETE /messages/{id}`: 본인만(owner 예외 없음)→타인 403 NOT_OWNER, 미존재 404

## 8. 프론트엔드 (MPA · 9화면)

- [ ] 8.1 `frontend/js/api.js`: fetch 래퍼(Bearer 자동첨부, 401→토큰삭제+`/login`), 토큰 localStorage 관리
- [ ] 8.2 로그인/회원가입 화면: 클라 검증(이메일·8자·1000자 등) + 에러 인라인 표시
- [ ] 8.3 팀 선택 화면: team_id NULL 강제 진입, 팀 만들기/초대코드 합류(형식 검증)
- [ ] 8.4 칸반 화면: 3컬럼·필터(전체/@me/미할당)·카드, HTML5 드래그→`PATCH status`, empty state
- [ ] 8.5 카드 상세/수정 모달: 제목·상태·assignee 수정, 삭제(권한자만 버튼 노출)
- [ ] 8.6 채팅 화면: 최근 50 로드 + 5초 폴링(`since=<lastId>`), 1000자 카운터, 본인 메시지 삭제, 연결 끊김 표시/재시도(최소)
- [ ] 8.7 멤버 패널 + 진입 가드(토큰/team_id 분기), Tailwind CDN 반응형
- [ ] 8.8 403/404 페이지(비멤버 접근 등 결정 #6 시각화)

## 9. 자동 테스트 (스코프 추가 · platform-foundation)

- [ ] 9.1 `tests/conftest.py`: 인메모리 SQLite(StaticPool) + 의존성 오버라이드 픽스처, 테스트별 격리
- [ ] 9.2 auth 테스트: 가입(중복/약비번/형식), 로그인(성공/실패 통일·열거 방지), me, JWT 만료→401
- [ ] 9.3 team 테스트: 생성/합류(형식·404·409), members, leave(member 정리·owner 거부), 비멤버 403
- [ ] 9.4 task 테스트: 생성·필터(@me/미할당)·상태전이(잘못된값)·assignee 같은팀 검증·삭제 권한(creator/owner/타인/비멤버)
- [ ] 9.5 chat 테스트: 1000자 초과 TOO_LONG, id커서 폴링(같은 초 누락0·증분·빈배열), 삭제 본인만/owner 불가
- [ ] 9.6 횡단 테스트: 에러 응답 표준 형태, KST `+09:00` 직렬화 회귀, `/teams/{id}/*` 비멤버 403 격리

## 10. Swagger·배포·문서 마무리

- [ ] 10.1 18개 라우트에 `tags`·`response_model`·`responses`(에러 예시) 부여, `/docs`에서 그룹별 노출·호출 확인
- [ ] 10.2 `api/index.py`(Vercel 진입점) + `vercel.json`(정적 FE + `/api` 라우팅) 작성
- [ ] 10.3 로컬 실행 확인: `uvicorn app.main:app --reload` + `python -m http.server`(frontend) 수동 스모크
- [ ] 10.4 `pytest` 전체 통과 확인
- [ ] 10.5 `CLAUDE.md` "빌드/실행" 섹션을 실제 명령으로 갱신, 범위 외 목록에서 테스트·Swagger 2건 제외 반영
