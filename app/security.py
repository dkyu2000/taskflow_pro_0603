"""비밀번호 해시(bcrypt) + JWT(HS256, 24h)."""
from datetime import timedelta

import bcrypt
import jwt

from app.config import JWT_ALG, JWT_EXPIRE_HOURS, JWT_SECRET
from app.errors import AppError
from app.utils import now_kst


def hash_password(plain: str) -> str:
    # bcrypt 72바이트 제한 → 안전하게 절단
    pw = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    now = now_kst()
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise AppError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")
    except jwt.PyJWTError:
        raise AppError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")
