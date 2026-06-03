"""Chat API (3) — poll list / create / delete."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_membership
from app.errors import AppError
from app.models import Message, User
from app.schemas import MessageCreateIn, MessageOut

router = APIRouter(tags=["Chat"])

RECENT_LIMIT = 50


def _to_out(m: Message, email: str) -> MessageOut:
    return MessageOut(
        id=m.id,
        team_id=m.team_id,
        user_id=m.user_id,
        user_email=email,
        content=m.content,
        created_at=m.created_at,
    )


@router.get("/teams/{team_id}/messages", response_model=list[MessageOut])
def list_messages(
    team_id: int,
    since: int | None = Query(default=None, description="마지막 수신 message.id (증분 폴링)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_membership(team_id, user)
    stmt = select(Message, User.email).join(User, User.id == Message.user_id).where(
        Message.team_id == team_id
    )
    if since is not None:
        # id 커서 — 같은 초 충돌·중복·누락 없이 증분
        rows = db.execute(stmt.where(Message.id > since).order_by(Message.id.asc())).all()
    else:
        # 최초 진입 — 최근 50개를 시간순으로
        rows = db.execute(stmt.order_by(Message.id.desc()).limit(RECENT_LIMIT)).all()
        rows = list(reversed(rows))
    return [_to_out(m, email) for m, email in rows]


@router.post("/teams/{team_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(
    team_id: int,
    body: MessageCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_membership(team_id, user)
    msg = Message(team_id=team_id, user_id=user.id, content=body.content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return _to_out(msg, user.email)


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    msg = db.get(Message, message_id)
    if msg is None:
        raise AppError(404, "NOT_FOUND", "메시지를 찾을 수 없습니다")
    require_membership(msg.team_id, user)
    # 본인만 삭제 — owner여도 타인 메시지 불가
    if msg.user_id != user.id:
        raise AppError(403, "NOT_OWNER", "본인의 메시지만 삭제할 수 있습니다")
    db.delete(msg)
    db.commit()
