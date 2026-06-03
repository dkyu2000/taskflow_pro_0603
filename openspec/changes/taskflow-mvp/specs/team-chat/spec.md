## ADDED Requirements

### Requirement: 메시지 전송
The system SHALL create a message via `POST /teams/{id}/messages` with a 1–1000 character limit validated on the server.

#### Scenario: 정상 전송
- **WHEN** 멤버가 1–1000자 내용으로 메시지 전송 요청
- **THEN** `201`과 생성된 메시지(`{ id, user_id, user_email, content, created_at }`)를 반환한다

#### Scenario: 1000자 초과
- **WHEN** 1000자를 초과하는 내용으로 전송 요청
- **THEN** `400 TOO_LONG`(`meta`에 `limit`/`actual` 포함)을 반환한다

#### Scenario: 빈 메시지
- **WHEN** 빈 내용으로 전송 요청
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 메시지 전송 요청
- **THEN** `403 FORBIDDEN`을 반환한다

### Requirement: 메시지 폴링 조회 (id 커서)
The system SHALL return messages from `GET /teams/{id}/messages` supporting incremental polling via an integer `since` cursor (last received `message.id`).

#### Scenario: 최초 진입
- **WHEN** 멤버가 `since` 없이 조회
- **THEN** 최근 50개를 시간순으로 반환한다

#### Scenario: 증분 폴링
- **WHEN** 멤버가 `?since=<id>`로 조회
- **THEN** `WHERE id > :since`인 메시지만 반환한다

#### Scenario: 같은 초 메시지 누락 0건
- **WHEN** 동일한 `created_at`(같은 초)에 여러 메시지가 존재하고 `since`로 증분 조회
- **THEN** id 기준 비교로 누락·중복 없이 새 메시지를 모두 반환한다

#### Scenario: 새 메시지 없음
- **WHEN** `since` 이후 새 메시지가 없는 상태로 조회
- **THEN** `200`과 빈 배열을 반환한다

#### Scenario: 비멤버 차단
- **WHEN** 비멤버가 메시지 조회 요청
- **THEN** `403 FORBIDDEN`을 반환한다

### Requirement: 메시지 삭제 (본인만)
The system SHALL delete a message via `DELETE /messages/{id}` only when the requester is the message author. Team owner MUST NOT delete others' messages.

#### Scenario: 본인 메시지 삭제
- **WHEN** 작성자가 본인 메시지를 삭제 요청
- **THEN** `200`/`204`로 삭제된다

#### Scenario: 타인 메시지 차단
- **WHEN** 작성자가 아닌 멤버가 메시지 삭제 요청
- **THEN** `403 NOT_OWNER`를 반환한다

#### Scenario: owner도 타인 메시지 불가
- **WHEN** team owner가 타인의 메시지를 삭제 요청
- **THEN** `403 NOT_OWNER`를 반환한다

#### Scenario: 존재하지 않음
- **WHEN** 존재하지 않는 메시지 id로 삭제 요청
- **THEN** `404 NOT_FOUND`를 반환한다
