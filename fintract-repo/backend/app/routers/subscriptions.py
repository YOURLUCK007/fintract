"""Subscription detector endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.subscriptions import summarize
from ..models import Expense, User

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("")
def list_subscriptions(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return summarize(expenses)
