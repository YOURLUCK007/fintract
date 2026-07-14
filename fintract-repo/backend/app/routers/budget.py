"""AI budget generator endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.budget import generate_budget
from ..models import Expense, User

router = APIRouter(prefix="/api/budget", tags=["budget"])


@router.get("")
def get_budget(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return generate_budget(current.monthly_income, expenses)
