"""인증·인가 의존성."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.models import User
from app.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if cred is None or not cred.credentials:
        raise AppError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")
    payload = decode_token(cred.credentials)
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None:
        raise AppError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")
    return user


def require_membership(team_id: int, user: User) -> None:
    """모든 /teams/{id}/* 라우트의 멤버십 검증. 비멤버 403."""
    if user.team_id != team_id:
        raise AppError(403, "FORBIDDEN", "이 팀의 멤버가 아닙니다")
