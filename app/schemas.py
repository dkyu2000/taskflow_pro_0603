"""pydantic 요청/응답 스키마 — Swagger 모델 + 서버 검증."""
import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.utils import KST

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
INVITE_RE = re.compile(r"^[A-Z]{4}-[0-9]{4}$")


class TaskStatus(str, Enum):
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"


class _KSTModel(BaseModel):
    """created_at을 항상 KST(+09:00) 오프셋으로 직렬화."""

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", when_used="json", check_fields=False)
    def _ser_created_at(self, v: datetime):
        if isinstance(v, datetime) and v.tzinfo is None:
            v = v.replace(tzinfo=KST)
        return v.isoformat()


# ---------- Auth ----------
class SignupIn(BaseModel):
    email: str = Field(examples=["user@example.com"])
    password: str = Field(min_length=8, examples=["password123"])

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        if not EMAIL_RE.match(v):
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v


class LoginIn(BaseModel):
    email: str = Field(examples=["user@example.com"])
    password: str = Field(examples=["password123"])


class UserOut(_KSTModel):
    id: int
    email: str
    team_id: int | None = None


class AuthOut(BaseModel):
    token: str = Field(examples=["eyJhbGciOiJIUzI1NiIs..."])
    user: UserOut


# ---------- Team ----------
class TeamCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=30, examples=["Frontiers"])


class TeamJoinIn(BaseModel):
    invite_code: str = Field(examples=["FRNT-2026"])

    @field_validator("invite_code")
    @classmethod
    def _code(cls, v: str) -> str:
        if not INVITE_RE.match(v):
            raise ValueError("초대코드 형식이 올바르지 않습니다")
        return v


class TeamOut(_KSTModel):
    id: int
    name: str
    invite_code: str
    owner_id: int
    created_at: datetime


class TeamBrief(BaseModel):
    id: int
    name: str
    member_count: int


class TeamJoinOut(BaseModel):
    team: TeamBrief
    redirect: str = Field(examples=["/teams/7"])


class MemberOut(_KSTModel):
    id: int
    email: str
    role: str = Field(examples=["owner", "member"])
    created_at: datetime


# ---------- Task ----------
class TaskCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=100, examples=["DB 마이그레이션 작성"])
    assignee_id: int | None = Field(default=None, examples=[42])


class TaskUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    assignee_id: int | None = None


class TaskStatusIn(BaseModel):
    status: TaskStatus = Field(examples=["DOING"])


class TaskOut(_KSTModel):
    id: int
    team_id: int
    title: str
    status: str
    creator_id: int
    assignee_id: int | None = None
    created_at: datetime


# ---------- Chat ----------
class MessageCreateIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000, examples=["JWT 미들웨어 끝내고 옮길게요"])


class MessageOut(_KSTModel):
    id: int
    team_id: int
    user_id: int
    user_email: str
    content: str
    created_at: datetime


# ---------- 공통 ----------
class ErrorOut(BaseModel):
    error: dict = Field(
        examples=[{"code": "FORBIDDEN", "message": "이 팀의 멤버가 아닙니다"}]
    )
