"""Forecast endpoints: savings projection, cash flow, recommendations."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.forecast import cashflow_forecast, savings_forecast
from ..ml.recommender import recommendations
from ..models import Expense, User

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("/savings")
def savings(
    plan: str = Query("balanced", pattern="^(conservative|balanced|aggressive)$"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return savings_forecast(current.monthly_income, expenses, plan)


@router.get("/cashflow")
def cashflow(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return cashflow_forecast(current.monthly_income, expenses)


@router.get("/recommendations")
def recs(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return {"recommendations": recommendations(expenses)}
