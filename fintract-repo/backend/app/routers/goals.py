"""Goal endpoints with computed completion date & monthly contribution."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Goal, User
from ..schemas import GoalCreate, GoalOut

router = APIRouter(prefix="/api/goals", tags=["goals"])


def _to_out(g: Goal) -> GoalOut:
    percent = min(100.0, round(g.saved_amount / g.target_amount * 100, 1)) if g.target_amount else 0.0
    remaining = max(g.target_amount - g.saved_amount, 0.0)
    months_left = 0
    eta = "Completed"
    if remaining > 0 and g.monthly_contribution > 0:
        import math
        months_left = math.ceil(remaining / g.monthly_contribution)
        m = date.today().month - 1 + months_left
        yy = date.today().year + m // 12
        mm = m % 12 + 1
        eta = date(yy, mm, 1).strftime("%b %Y")
    elif remaining > 0:
        eta = "Set a monthly amount"
    return GoalOut(
        id=g.id, name=g.name, emoji=g.emoji, target_amount=g.target_amount,
        saved_amount=g.saved_amount, monthly_contribution=g.monthly_contribution,
        percent=percent, months_left=months_left, eta=eta,
    )


@router.get("", response_model=list[GoalOut])
def list_goals(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    goals = db.query(Goal).filter(Goal.user_id == current.id).order_by(Goal.id).all()
    return [_to_out(g) for g in goals]


@router.post("", response_model=GoalOut, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    g = Goal(user_id=current.id, **payload.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return _to_out(g)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    g = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current.id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(g)
    db.commit()
