## ADDED Requirements

### Requirement: 태스크 목록 조회 및 필터
The system SHALL return team tasks from `GET /teams/{id}/tasks`, sorted by `created_at` descending, with filters `all` / `@me` / `미할당`.

#### Scenario: 전체 조회
- **WHEN** 멤버가 필터 없이 `GET /teams/{id}/tasks` 요청
- **THEN** `200`과 해당 팀의 모든 태스크를 `created_at` 내림차순으로 반환한다

#### Scenario: 내 태스크 필터
- **WHEN** 멤버가 `@me` 필터로 요청
- **THEN** `WHERE assignee_id = current_user_id` 결과만 반환한다(creator 기준 아님)

#### Scenario: 미할당 필터
- **WHEN** 멤버가 `미할당` 필터로 요청
- **THEN** `assignee_id IS NULL`인 태스크만 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 태스크 목록을 요청
- **THEN** `403 FORBIDDEN`을 반환한다

### Requirement: 태스크 생성
The system SHALL create a task via `POST /teams/{id}/tasks` with default status `TODO`.

#### Scenario: 정상 생성
- **WHEN** 멤버가 1–100자 제목으로 태스크 생성 요청
- **THEN** `201`과 생성된 태스크(status=`TODO`, creator_id=요청자)를 반환한다

#### Scenario: 제목 검증
- **WHEN** 제목이 비었거나 100자를 초과
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: assignee는 같은 팀 멤버만
- **WHEN** 같은 팀 멤버가 아닌 사용자를 assignee로 지정
- **THEN** `400 VALIDATION_ERROR`를 반환한다

### Requirement: 태스크 상세 조회
The system SHALL return a single task from `GET /tasks/{id}` to members of the task's team.

#### Scenario: 멤버 조회
- **WHEN** 태스크가 속한 팀의 멤버가 `GET /tasks/{id}` 요청
- **THEN** `200`과 태스크 상세(제목·상태·assignee·creator·created_at)를 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 태스크가 속한 팀의 비멤버가 요청
- **THEN** `403 FORBIDDEN`을 반환한다

#### Scenario: 존재하지 않음
- **WHEN** 존재하지 않는 태스크 id로 요청
- **THEN** `404 NOT_FOUND`를 반환한다

### Requirement: 태스크 수정 (제목·담당자)
The system SHALL update a task's title and/or assignee via `PUT /tasks/{id}`.

#### Scenario: 정상 수정
- **WHEN** 멤버가 제목 또는 assignee를 수정 요청
- **THEN** `200`과 수정된 태스크를 반환한다

#### Scenario: assignee 검증
- **WHEN** 같은 팀 멤버가 아닌 사용자로 assignee 변경 시도
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 수정 요청
- **THEN** `403 FORBIDDEN`을 반환한다

### Requirement: 태스크 상태 전이
The system SHALL change a task's status via `PATCH /tasks/{id}/status` accepting only `TODO`|`DOING`|`DONE`.

#### Scenario: 정상 전이
- **WHEN** 멤버가 유효한 상태로 `PATCH /tasks/{id}/status` 요청(예: 드래그 후 DOING)
- **THEN** `200`과 갱신된 상태를 반환한다

#### Scenario: 잘못된 상태값
- **WHEN** 허용되지 않은 상태 문자열로 요청
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 상태 변경 요청
- **THEN** `403 FORBIDDEN`을 반환한다

### Requirement: 태스크 삭제 (creator 또는 owner)
The system SHALL delete a task via `DELETE /tasks/{id}` only when the requester is the task creator or the team owner.

#### Scenario: creator 삭제
- **WHEN** 카드 생성자가 `DELETE /tasks/{id}` 요청
- **THEN** `200`/`204`로 삭제된다

#### Scenario: owner 오버라이드 삭제
- **WHEN** team owner가 타인이 만든 카드를 삭제 요청
- **THEN** 삭제가 허용된다

#### Scenario: 권한 없는 멤버 차단
- **WHEN** creator도 owner도 아닌 멤버가 삭제 요청
- **THEN** `403 FORBIDDEN`을 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 삭제 요청
- **THEN** `403 FORBIDDEN`을 반환한다
