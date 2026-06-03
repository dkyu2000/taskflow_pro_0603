## ADDED Requirements

### Requirement: 회원가입
The system SHALL allow a new user to register with email and password and return `201` with a JWT on success.

#### Scenario: 정상 회원가입
- **WHEN** 미가입 이메일과 8자 이상 비밀번호로 `POST /auth/signup` 요청
- **THEN** `201`과 JWT, 그리고 `{ id, email, team_id: null }` 사용자 정보를 반환한다

#### Scenario: 이메일 형식 오류
- **WHEN** 형식이 올바르지 않은 이메일로 가입 요청
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: 비밀번호 약함
- **WHEN** 8자 미만 비밀번호로 가입 요청
- **THEN** `400 VALIDATION_ERROR`를 반환한다

#### Scenario: 이메일 중복
- **WHEN** 이미 가입된 이메일로 가입 요청
- **THEN** `409 EMAIL_TAKEN`을 반환한다

### Requirement: 비밀번호 해시
The system SHALL store passwords as bcrypt hashes and MUST NOT store plaintext passwords.

#### Scenario: 해시 저장
- **WHEN** 사용자가 가입한다
- **THEN** `users.password_hash`는 입력 평문과 다른 bcrypt 해시이며 평문은 어디에도 저장되지 않는다

### Requirement: 로그인
The system SHALL authenticate email/password and return `200` with a 24시간 만료 JWT. 실패는 이메일 존재 여부를 노출하지 않고 단일 메시지로 통일한다.

#### Scenario: 정상 로그인
- **WHEN** 올바른 자격으로 `POST /auth/login` 요청
- **THEN** `200`과 JWT(exp 24h), `{ id, email, team_id }`를 반환한다

#### Scenario: 비밀번호 불일치
- **WHEN** 존재하는 이메일 + 틀린 비밀번호로 로그인
- **THEN** `401 INVALID_CREDENTIALS`를 반환한다

#### Scenario: 미존재 이메일 (열거 방지)
- **WHEN** 존재하지 않는 이메일로 로그인
- **THEN** 비밀번호 불일치와 **동일한** `401 INVALID_CREDENTIALS` 메시지를 반환한다

### Requirement: 로그아웃 (stateless)
The system SHALL treat logout as stateless and return `200` only, without maintaining a token blacklist.

#### Scenario: 로그아웃 호출
- **WHEN** `POST /auth/logout` 요청
- **THEN** `200`을 반환하고 서버는 토큰을 무효화하지 않는다(클라이언트가 폐기)

### Requirement: 현재 사용자 조회
The system SHALL return the current authenticated user from `GET /auth/me`.

#### Scenario: 유효 토큰
- **WHEN** 유효한 `Authorization: Bearer` 토큰으로 `GET /auth/me` 요청
- **THEN** `200`과 `{ id, email, team_id }`를 반환한다

#### Scenario: 토큰 만료/누락
- **WHEN** 만료되었거나 없는 토큰으로 `GET /auth/me` 요청
- **THEN** `401 TOKEN_EXPIRED`를 반환한다

### Requirement: JWT 만료 정책
The system SHALL issue JWTs that expire in 24 hours with no refresh mechanism.

#### Scenario: 만료 토큰으로 보호 API 호출
- **WHEN** 발급 후 24시간이 지난 토큰으로 보호된 API를 호출
- **THEN** `401 TOKEN_EXPIRED`를 반환하고 재로그인을 요구한다
