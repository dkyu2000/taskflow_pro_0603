"""Team API (5) — create / join / get / members / leave."""
import random
import string

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_membership
from app.errors import AppError
from app.models import Task, Team, User
from app.schemas import (
    MemberOut,
    TeamBrief,
    TeamCreateIn,
    TeamJoinIn,
    TeamJoinOut,
    TeamOut,
)

router = APIRouter(tags=["Team"])


def _gen_invite_code(db: Session) -> str:
    for _ in range(20):
        code = (
            "".join(random.choices(string.ascii_uppercase, k=4))
            + "-"
            + "".join(random.choices(string.digits, k=4))
        )
        if not db.scalar(select(Team).where(Team.invite_code == code)):
            return code
    raise AppError(500, "INTERNAL", "초대코드 생성에 실패했습니다")


@router.post("/teams", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(body: TeamCreateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.team_id is not None:
        raise AppError(409, "ALREADY_IN_TEAM", "이미 팀에 소속되어 있습니다")
    team = Team(name=body.name, invite_code=_gen_invite_code(db), owner_id=user.id)
    db.add(team)
    db.flush()  # team.id 확보
    user.team_id = team.id
    db.commit()
    db.refresh(team)
    return TeamOut.model_validate(team)


@router.post("/teams/join", response_model=TeamJoinOut)
def join_team(body: TeamJoinIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.team_id is not None:
        raise AppError(409, "ALREADY_IN_TEAM", "이미 다른 팀에 소속되어 있습니다")
    team = db.scalar(select(Team).where(Team.invite_code == body.invite_code))
    if team is None:
        raise AppError(404, "NOT_FOUND", "해당 초대코드를 찾을 수 없습니다")
    user.team_id = team.id
    db.commit()
    count = db.scalar(select(func.count()).select_from(User).where(User.team_id == team.id))
    return TeamJoinOut(
        team=TeamBrief(id=team.id, name=team.name, member_count=count or 0),
        redirect=f"/teams/{team.id}",
    )


@router.get("/teams/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_membership(team_id, user)
    team = db.get(Team, team_id)
    if team is None:
        raise AppError(404, "NOT_FOUND", "팀을 찾을 수 없습니다")
    return TeamOut.model_validate(team)


@router.get("/teams/{team_id}/members", response_model=list[MemberOut])
def list_members(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_membership(team_id, user)
    team = db.get(Team, team_id)
    members = db.scalars(select(User).where(User.team_id == team_id).order_by(User.created_at)).all()
    return [
        MemberOut(
            id=m.id,
            email=m.email,
            role="owner" if (team and m.id == team.owner_id) else "member",
            created_at=m.created_at,
        )
        for m in members
    ]


@router.delete("/teams/{team_id}/leave")
def leave_team(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_membership(team_id, user)
    team = db.get(Team, team_id)
    if team and team.owner_id == user.id:
        # 소유권 이전은 범위 외 → owner는 떠날 수 없음
        raise AppError(409, "OWNER_CANNOT_LEAVE", "팀 소유자는 팀을 떠날 수 없습니다")
    # 본인이 assignee인 카드는 미할당으로, 작성한 task/message는 보존
    for t in db.scalars(select(Task).where(Task.team_id == team_id, Task.assignee_id == user.id)).all():
        t.assignee_id = None
    user.team_id = None
    db.commit()
    return {}
