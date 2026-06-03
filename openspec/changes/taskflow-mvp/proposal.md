## Why

TaskFlow는 소규모 팀(팀당 ~5명)이 칸반 + 실시간 채팅(5초 폴링)으로 업무 진행을 한 화면에서 추적하는 MVP다. 현재 저장소는 기획 PDF 2개와 `CLAUDE.md`만 있는 그린필드 상태이며, 실제 동작하는 백엔드·프론트엔드가 없다. 이 변경은 명세(스토리보드의 결정 8건 + 탐색에서 확정한 추가 결정)를 그대로 구현하여 배포 가능한 첫 버전을 만든다.

## What Changes

- **FastAPI 백엔드 신규 구축**: API 18개(Auth 4 + Team 5 + Task 6 + Chat 3), DB 4테이블(`users`/`teams`/`tasks`/`messages`), JWT 인증(24h·갱신 없음)·bcrypt 해시.
- **Vanilla JS + Tailwind 프론트엔드 신규 구축(MPA)**: 화면 9종(로그인/회원가입/팀선택/칸반/채팅/멤버 등), 페이지별 401 라우트가드로 `/login` redirect.
- **환경 분리**: `DATABASE_URL` 환경변수로 로컬 SQLite ↔ 운영 Neon(PostgreSQL) 전환. 코드는 양쪽 호환.
- **권한 모델 적용**: 모든 `/teams/{id}/*`는 JWT + 멤버십 검증, 비멤버 403. task DELETE는 creator/owner, message DELETE는 본인만.
- **에러 응답 표준**: 전 응답 `{ error: { code, message, meta } }` 통일.
- **탐색 확정 결정 반영**:
  - 시간대는 KST + 오프셋(`+09:00`) 명시, `Z`(UTC) 표기 폐기.
  - 채팅 폴링 커서 `since`는 마지막 수신 `message.id`(정수) 기반(`WHERE id > :since`)으로 "메시지 누락 0건" 보장.
  - owner의 `DELETE /teams/{id}/leave`는 거부(409 `OWNER_CANNOT_LEAVE`).
  - member leave 시 `users.team_id=NULL`, 작성한 task/message는 보존, 그 사람이 assignee인 카드는 `assignee_id=NULL`.
  - `assignee_id`는 같은 팀 멤버에게만 배정 가능(서버 검증).
- **스코프 추가 (원래 PDF 범위 외였으나 사용자 명시 요청)**:
  - **Swagger/OpenAPI 문서**: FastAPI 내장 `/docs`·`/redoc` 활성화, 18개 엔드포인트 전부에 pydantic 모델·태그·예시 부여 → `/docs`에서 API 테스트 가능. (**BREAKING** 대비: PDF "관측성/테스트 범위 외" 항목을 부분 번복)
  - **자동 테스트**: pytest + FastAPI `TestClient` + 인메모리 SQLite. 18개 API + 핵심 규칙(인증, 403 권한격리, validation, id커서 폴링, owner leave 거부, task/message DELETE 권한) 커버. (**BREAKING** 대비: PDF "pytest 없음, 수동 확인만" 번복)

## Capabilities

### New Capabilities

- `auth`: 회원가입·로그인·로그아웃·현재 사용자 조회. JWT 발급/검증(24h, stateless), bcrypt 해시, 로그인 실패 `INVALID_CREDENTIALS` 통일.
- `team-membership`: 팀 생성·초대코드 발급(정규식 `^[A-Z]{4}-[0-9]{4}$`)·합류·멤버 목록·팀 떠나기. 1인 1팀(`users.team_id`), owner leave 거부, member leave 시 정리 규칙.
- `kanban-tasks`: 태스크 CRUD, 상태 전이(`PATCH /tasks/{id}/status`), 필터(@me/미할당), nullable assignee(같은 팀 검증), `created_at` 정렬.
- `team-chat`: 팀 메시지 전송·삭제(본인만)·5초 폴링 조회. id 커서(`since`) 기반 증분, 1000자 제한 양쪽 검증, 연결 끊김 표시/재시도(최소).
- `platform-foundation`: 횡단 관심사 — 에러 응답 표준, JWT+멤버십 인가 미들웨어, DB 4테이블·인덱스 스키마, `DATABASE_URL` 환경 전환, OpenAPI/Swagger 문서 노출, KST 시간대 직렬화 규칙, pytest 자동 테스트 하니스.

### Modified Capabilities

<!-- 기존 spec 없음(그린필드). 변경할 기존 capability 없음. -->

## Impact

- **신규 코드(백엔드)**: FastAPI 앱, ORM 모델/스키마(라이브러리 선택은 design에서), 라우터 18개, 인증·인가 의존성, 에러 핸들러, 설정(env), 마이그레이션.
- **신규 코드(프론트엔드)**: 화면별 HTML 9종, fetch 래퍼(JWT 자동 첨부·401 처리), Tailwind, 칸반 드래그, 채팅 폴링.
- **테스트**: `tests/` 디렉토리, pytest 설정, 인메모리 SQLite 픽스처.
- **의존성**: FastAPI, ASGI 서버(uvicorn), DB 드라이버(SQLite/PostgreSQL), JWT·bcrypt 라이브러리, pytest·httpx. (구체 선택은 design.md)
- **배포**: Vercel(프론트+백엔드 Serverless Functions) + Neon. `main` push 자동 배포. 로컬 SQLite는 git 제외.
- **문서**: `CLAUDE.md` "빌드/실행" 섹션을 실제 명령으로 갱신 필요(구현 후).
