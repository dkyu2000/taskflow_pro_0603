## ADDED Requirements

### Requirement: 에러 응답 표준
The system SHALL return all error responses in the shape `{ "error": { "code", "message", "meta"? } }` where `code` is SCREAMING_SNAKE and `message` is Korean user-facing text.

#### Scenario: 표준 형태 준수
- **WHEN** 임의의 4xx/5xx 에러가 발생
- **THEN** 응답 본문은 `{ error: { code, message } }` 형태이며 필요 시 `meta`를 포함한다

#### Scenario: 코드 매핑
- **WHEN** 표준 에러 상황이 발생
- **THEN** `VALIDATION_ERROR`(400), `TOO_LONG`(400), `INVALID_CREDENTIALS`(401), `TOKEN_EXPIRED`(401), `FORBIDDEN`(403), `NOT_OWNER`(403), `NOT_FOUND`(404), `EMAIL_TAKEN`(409), `OWNER_CANNOT_LEAVE`(409) 매핑을 사용한다

### Requirement: JWT + 멤버십 인가
The system SHALL protect every `/teams/{id}/*` route with JWT validation and a `user.team_id == {id}` membership check.

#### Scenario: 비멤버 전 메서드 차단
- **WHEN** 비멤버가 `/teams/{id}/*`에 GET/POST/PATCH/DELETE 중 무엇이든 요청
- **THEN** `403 FORBIDDEN`을 반환한다

#### Scenario: 토큰 누락
- **WHEN** `Authorization` 헤더 없이 보호된 라우트에 요청
- **THEN** `401 TOKEN_EXPIRED`를 반환한다

### Requirement: DB 스키마 및 인덱스
The system SHALL define 4 tables (`users`, `teams`, `tasks`, `messages`) with the agreed columns, foreign keys, and indexes.

#### Scenario: 테이블·컬럼
- **WHEN** 스키마가 생성된다
- **THEN** `users(id, email UNIQUE, password_hash, team_id FK nullable, created_at)`, `teams(id, name, invite_code UNIQUE, owner_id FK, created_at)`, `tasks(id, team_id FK, title, status, creator_id FK, assignee_id FK nullable, created_at)`, `messages(id, team_id FK, user_id FK, content, created_at)`가 존재한다

#### Scenario: 인덱스
- **WHEN** 스키마가 생성된다
- **THEN** `tasks(team_id, created_at)`, `messages(team_id, id)`, `teams(invite_code)`, `users(team_id)` 인덱스가 존재한다

### Requirement: 시간대 직렬화 (KST)
The system SHALL serialize timestamps as KST with an explicit `+09:00` offset and MUST NOT use a `Z` (UTC) suffix.

#### Scenario: 응답 타임스탬프
- **WHEN** `created_at`이 포함된 응답을 반환
- **THEN** 값은 `2026-05-13T14:30:00+09:00` 형태이며 `Z` 표기를 쓰지 않는다

### Requirement: 환경 전환 (DATABASE_URL)
The system SHALL select the database via the `DATABASE_URL` environment variable, defaulting to a local SQLite file and using Neon PostgreSQL in production, with code compatible across both.

#### Scenario: 로컬 기본값
- **WHEN** `DATABASE_URL`이 설정되지 않음
- **THEN** 로컬 SQLite 파일(`sqlite:///./taskflow.db`)을 사용한다

#### Scenario: 운영 전환
- **WHEN** `DATABASE_URL`이 Neon PostgreSQL 문자열로 설정됨
- **THEN** 동일 코드가 PostgreSQL에 연결된다

### Requirement: OpenAPI / Swagger 문서
The system SHALL expose FastAPI's built-in `/docs` (Swagger UI) and `/redoc`, with all 18 endpoints documented via pydantic models, tags, and examples.

#### Scenario: 문서 접근
- **WHEN** `/docs`에 접근
- **THEN** 18개 엔드포인트가 그룹(Auth/Team/Task/Chat)별 태그와 요청/응답 모델·예시와 함께 표시되어 직접 호출/테스트할 수 있다

### Requirement: 자동 테스트 하니스
The system SHALL provide a runnable pytest suite using FastAPI `TestClient` and an in-memory SQLite database, covering all 18 endpoints and key rules.

#### Scenario: 테스트 실행
- **WHEN** 개발자가 `pytest`를 실행
- **THEN** 18개 API와 핵심 규칙(인증, 403 권한격리, validation, id커서 폴링 누락 0건, owner leave 거부, task/message DELETE 권한)에 대한 테스트가 격리된 인메모리 DB에서 실행된다
