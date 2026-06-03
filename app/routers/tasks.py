"""Task API (6) — list / create / get / update / status / delete."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_membership
from app.errors import AppError
from app.models import Task, Team, User
from app.schemas import TaskCreateIn, TaskOut, TaskStatusIn, TaskUpdateIn

router = APIRouter(tags=["Task"])


def _validate_assignee(db: Session, team_id: int, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    assignee = db.get(User, assignee_id)
    if assignee is None or assignee.team_id != team_id:
        raise AppError(400, "VALIDATION_ERROR", "담당자는 같은 팀의 멤버여야 합니다")


def _load_task_for_member(db: Session, task_id: int, user: User) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise AppError(404, "NOT_FOUND", "태스크를 찾을 수 없습니다")
    require_membership(task.team_id, user)
    return task


@router.get("/teams/{team_id}/tasks", response_model=list[TaskOut])
def list_tasks(
    team_id: int,
    filter: str | None = Query(default=None, description="me | unassigned"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_membership(team_id, user)
    stmt = select(Task).where(Task.team_id == team_id)
    if filter == "me":
        stmt = stmt.where(Task.assignee_id == user.id)
    elif filter == "unassigned":
        stmt = stmt.where(Task.assignee_id.is_(None))
    stmt = stmt.order_by(Task.created_at.desc(), Task.id.desc())
    return [TaskOut.model_validate(t) for t in db.scalars(stmt).all()]


@router.post("/teams/{team_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    team_id: int,
    body: TaskCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_membership(team_id, user)
    _validate_assignee(db, team_id, body.assignee_id)
    task = Task(
        team_id=team_id,
        title=body.title,
        status="TODO",
        creator_id=user.id,
        assignee_id=body.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return TaskOut.model_validate(_load_task_for_member(db, task_id, user))


@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    body: TaskUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _load_task_for_member(db, task_id, user)
    if body.title is not None:
        task.title = body.title
    if "assignee_id" in body.model_fields_set:
        _validate_assignee(db, task.team_id, body.assignee_id)
        task.assignee_id = body.assignee_id
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.patch("/tasks/{task_id}/status", response_model=TaskOut)
def change_status(
    task_id: int,
    body: TaskStatusIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _load_task_for_member(db, task_id, user)
    task.status = body.status.value
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = _load_task_for_member(db, task_id, user)
    team = db.get(Team, task.team_id)
    is_owner = bool(team and team.owner_id == user.id)
    if task.creator_id != user.id and not is_owner:
        raise AppError(403, "FORBIDDEN", "카드를 삭제할 권한이 없습니다")
    db.delete(task)
    db.commit()
