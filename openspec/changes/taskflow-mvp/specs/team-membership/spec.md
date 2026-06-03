## ADDED Requirements

### Requirement: 팀 생성
The system SHALL create a team via `POST /teams`, auto-generate an invite code, set the creator as owner, and set the creator's `team_id`.

#### Scenario: 정상 생성
- **WHEN** 팀 미소속 사용자가 1–30자 이름으로 `POST /teams` 요청
- **THEN** `201`과 `{ id, name, invite_code, owner_id, created_at }`를 반환하고 `users.team_id`를 생성된 팀으로 설정한다

#### Scenario: 이름 검증
- **WHEN** 이름이 비었거나 30자를 초과
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: 이미 팀 소속
- **WHEN** 이미 팀에 소속된 사용자가 팀 생성을 시도
- **THEN** `409`를 반환한다(1인 1팀)

### Requirement: 초대코드 형식 및 생성
The system SHALL generate a unique invite code matching `^[A-Z]{4}-[0-9]{4}$` on the server.

#### Scenario: 형식 준수
- **WHEN** 팀이 생성된다
- **THEN** `invite_code`는 정규식 `^[A-Z]{4}-[0-9]{4}$`(예: `FRNT-2026`)를 만족하고 전역적으로 유일하다

### Requirement: 팀 합류
The system SHALL let a user join a team via `POST /teams/join` with an invite code, updating their `team_id`.

#### Scenario: 정상 합류
- **WHEN** 팀 미소속 사용자가 유효한 `invite_code`로 합류 요청
- **THEN** `200`과 `{ team: { id, name, member_count }, redirect }`를 반환하고 `users.team_id`를 갱신한다

#### Scenario: 형식 오류
- **WHEN** 정규식에 맞지 않는 코드로 합류 요청
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: 존재하지 않는 코드
- **WHEN** 형식은 맞지만 존재하지 않는 코드로 합류 요청
- **THEN** `404 NOT_FOUND`를 반환한다

#### Scenario: 이미 다른 팀 소속
- **WHEN** 이미 팀에 소속된 사용자가 합류 요청
- **THEN** `409`를 반환한다

### Requirement: 팀 정보 조회
The system SHALL return team info from `GET /teams/{id}` for members only.

#### Scenario: 멤버 조회
- **WHEN** 해당 팀 멤버가 `GET /teams/{id}` 요청
- **THEN** `200`과 팀 정보를 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 `GET /teams/{id}` 요청
- **THEN** `403 FORBIDDEN`을 반환한다

### Requirement: 멤버 목록 조회
The system SHALL return the member list from `GET /teams/{id}/members` with owner distinction.

#### Scenario: 멤버 목록
- **WHEN** 멤버가 `GET /teams/{id}/members` 요청
- **THEN** `200`과 각 멤버의 이메일·역할(owner/member)·합류일을 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 멤버 목록을 요청
- **THEN** `403 FORBIDDEN`을 반환한다

### Requirement: 팀 떠나기
The system SHALL let a member leave via `DELETE /teams/{id}/leave`, but MUST reject the owner leaving.

#### Scenario: 멤버 떠나기
- **WHEN** owner가 아닌 멤버가 `DELETE /teams/{id}/leave` 요청
- **THEN** `users.team_id`를 `NULL`로 설정하고, 그 사용자가 작성한 task/message는 보존하며, 그 사용자가 assignee인 카드의 `assignee_id`는 `NULL`(미할당)로 변경한다

#### Scenario: owner는 떠날 수 없음
- **WHEN** team owner가 `DELETE /teams/{id}/leave` 요청
- **THEN** `409 OWNER_CANNOT_LEAVE`를 반환한다(소유권 이전은 범위 외)

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 leave 요청
- **THEN** `403 FORBIDDEN`을 반환한다
