"""Auth API (4) — signup / login / logout / me."""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import AppError
from app.models import User
from app.schemas import AuthOut, LoginIn, SignupIn, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == body.email))
    if exists:
        raise AppError(409, "EMAIL_TAKEN", "이미 가입된 이메일입니다")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthOut(token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    # 이메일 존재 여부를 노출하지 않도록 단일 메시지로 통일
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 일치하지 않습니다")
    return AuthOut(token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/logout")
def logout(_: User = Depends(get_current_user)):
    # stateless — 서버는 200만 반환, 블랙리스트 없음
    return {}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
