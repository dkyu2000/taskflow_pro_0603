# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 현재 상태

코드 이전 단계의 그린필드 프로젝트다. 아직 소스 코드·커밋이 없고, `docs/`에 기획 문서 PDF 2개만 있다. 이 두 PDF가 **구현의 단일 진실 공급원(source of truth)** 이며, 구현 시 임의 결정을 추가하지 말고 명세를 그대로 따른다.

- `docs/TaskFlow_프로그램정의.pdf` — 미션·페르소나·기능 5종·범위 외·ACME·비기능 요구사항
- `docs/TaskFlow_스토리보드.pdf` — 화면 상태/에러 케이스, ER·API·권한 명세, **PDF 원본 대비 8건의 결정(통합본 변경점)**

스토리보드가 프로그램정의 PDF보다 우선한다(빈틈을 메운 8건의 결정을 반영). 충돌 시 스토리보드 + 아래 "확정된 결정 8건" 기준.

## 미션 / 범위

소규모 팀(팀당 ~5명)이 칸반 + 실시간 채팅(5초 폴링)으로 업무 진행을 한 화면에서 추적하는 MVP.

**범위 외 (구현하지 말 것):** 이메일/SMS/푸시 알림, 파일·이미지 첨부, 전문 검색(단순 SELECT만), 페이지별 세분화 권한(admin/member 구분만), 다국어(한국어 UI만), WebSocket(5초 폴링으로 대체), 자동 테스트(pytest/jest — 수동 동작 확인만), JWT 갱신 토큰, 토큰 블랙리스트, 팀 추방·역할 변경, 초대코드 재발급.

## 기술 스택 (확정 — 임의 변경 금지)

- **Backend:** FastAPI (Python, async). 로컬은 `uvicorn main:app --reload`로 단일 서버 실행, 운영은 Vercel Serverless Functions.
- **DB:** 로컬 SQLite 파일(`sqlite:///./taskflow.db`), 운영 Neon(PostgreSQL). `DATABASE_URL` 환경변수로만 전환 — 코드는 양쪽 호환되게 작성. 로컬 SQLite 파일은 git에서 제외.
- **Frontend:** Vanilla JS(프레임워크 없음, ES6+, fetch API) + Tailwind CSS. 정적 파일은 로컬에서 `python -m http.server` 또는 live-server로 서빙.
- **배포:** GitHub `main` push → Vercel이 프론트+백엔드 자동 배포.

다음 항목은 명세에서 **클로드코드 판단에 위임**한다: 라이브러리 선택(SQLAlchemy/Tortoise·pydantic·bcrypt·python-jose 등), 디렉토리 구조, 마이그레이션 도구, FE 파일 구조(SPA vs MPA)·라우팅·CSS 빌드(CDN vs 빌드)·상태 관리 방식.

## 아키텍처 핵심

### DB 4테이블 (★ = PDF 원본 대비 추가된 결정)

- `users`: id PK, email UNIQUE, password_hash, **★ team_id FK→teams (nullable, 1인 1팀)**, created_at
- `teams`: id PK, name(1–30자), invite_code UNIQUE, owner_id FK→users, created_at
- `tasks`: id PK, team_id FK, title(1–100자), status(`TODO`|`DOING`|`DONE`), creator_id FK, **★ assignee_id FK→users (nullable)**, **★ created_at(정렬용)**
- `messages`: id PK, team_id FK, user_id FK, content(1–1000자), created_at

인덱스: `tasks(team_id, created_at)`, `messages(team_id, created_at)`, `teams(invite_code)`, `users.team_id`.

### API 18개

- **Auth(4):** `POST /auth/signup`(→201+JWT), `POST /auth/login`(→200+JWT 24h), `POST /auth/logout`(stateless, 200만), `GET /auth/me`
- **Team(5):** `POST /teams`(생성+초대코드 발급), `POST /teams/join`(invite_code), `GET /teams/{id}`, `GET /teams/{id}/members`, `DELETE /teams/{id}/leave`
- **Task(6):** `GET /teams/{id}/tasks`(filter: @me/미할당), `POST /teams/{id}/tasks`, `GET /tasks/{id}`, `PUT /tasks/{id}`(title·assignee), `PATCH /tasks/{id}/status`, `DELETE /tasks/{id}`
- **Chat(3):** `GET /teams/{id}/messages?since=`(폴링), `POST /teams/{id}/messages`, `DELETE /messages/{id}`

주의: 프로그램정의 PDF의 초기 목록과 다르다(결정 #3/#8 반영). 위 목록이 최종이다. 상태 변경은 `PUT`이 아니라 별도 `PATCH /tasks/{id}/status`.

### 핵심 동작 규칙

- **인증:** JWT 24h 만료, 갱신 없음. bcrypt 해시 의무(평문 저장 금지). FE는 JWT를 localStorage에 저장, 요청에 `Authorization: Bearer` 자동 첨부, 401 응답 시 토큰 삭제 후 `/login` redirect(직전 URL 저장 X).
- **로그인 분기:** 로그인 후 `users.team_id`가 NULL이면 팀 선택 화면 강제, 아니면 칸반.
- **'내 태스크' 정의:** `WHERE assignee_id = current_user_id` (creator_id 아님 — 결정 #4).
- **초대코드 형식:** 정규식 `^[A-Z]{4}-[0-9]{4}$` (예: `FRNT-2026`). 클라+서버 양쪽 검증, 서버가 자동 생성.
- **채팅 폴링:** 진입 시 최근 50개, 이후 5초마다 `?since=<마지막 메시지 시각>`로 증분. 빈 배열이면 화면 변화 없음.
- **시간대:** 서버·클라이언트 모두 KST. UTC 변환 안 함.

### 권한 모델 (결정 #6 — 반드시 지킬 것)

- 모든 `/teams/{id}/*` 라우트: JWT + `user.team_id == {id}` 검증. 비멤버는 **403 FORBIDDEN** (GET·POST·PATCH·DELETE 전부).
- `DELETE /tasks/{id}`: 카드 creator **또는** team owner만.
- `DELETE /messages/{id}`: **본인만**. owner여도 타인 메시지 삭제 불가.
- 메시지 1000자 제한·이메일 형식·필수 필드는 클라+서버 **양쪽** 검증.

### 에러 응답 표준 (전 응답 통일)

```json
{ "error": { "code": "<SCREAMING_SNAKE>", "message": "<한국어>", "meta": { } } }
```

`code`는 기계 친화 대문자, `message`는 사용자 노출용 한국어, `meta`는 옵션. 로그인 실패는 이메일 존재 여부를 노출하지 않고 `INVALID_CREDENTIALS` 한 메시지로 통일. 주요 코드: `VALIDATION_ERROR`(400), `TOO_LONG`(400), `INVALID_CREDENTIALS`(401), `TOKEN_EXPIRED`(401), `FORBIDDEN`(403), `NOT_OWNER`(403), `NOT_FOUND`(404), `EMAIL_TAKEN`(409).

## 확정된 결정 8건 (PDF 원본 → 통합본)

1. 멤버십을 `users.team_id`로 표현(1인 1팀, nullable).
2. 신규 합류자는 채팅 이력 '검색'이 아니라 시간순 '스크롤'(검색은 범위 외).
3. `PUT /tasks/{id}` 중복 제거 → 상태 변경은 `PATCH /tasks/{id}/status`로 분리.
4. `tasks.assignee_id`(nullable) 추가 — '내 태스크'는 assignee 기준.
5. logout은 stateless — 200만 반환, 블랙리스트 없음.
6. 권한: 비멤버 403, task DELETE는 creator/owner, message DELETE는 본인만.
7. 측정 불가 NFR(드래그 50ms·1분 파악)은 정성(수동) 검증으로 처리.
8. 모호하던 `GET /messages/{id}` 제거 → `GET /teams/{id}`로 교체.

## 빌드 / 실행 (구현 후 기준)

아직 코드가 없으므로 명령은 미정이다. 명세상 예상 형태:

- 백엔드: `uvicorn main:app --reload`
- 프론트: `python -m http.server` 또는 live-server로 정적 파일 서빙
- 환경 전환: `DATABASE_URL` 환경변수 (로컬 SQLite ↔ 운영 Neon)

실제 코드가 생기면 이 섹션을 실제 명령(의존성 설치, lint, 단일 실행 등)으로 갱신할 것. 자동 테스트는 범위 외이므로 수동 동작 확인으로 검증한다.
