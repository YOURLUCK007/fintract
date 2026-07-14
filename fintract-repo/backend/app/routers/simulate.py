"""Savings simulator + what-if scenario endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.simulator import simulate_savings, what_if
from ..models import Expense, User
from ..schemas import SavingsSimRequest, WhatIfRequest

router = APIRouter(prefix="/api/simulate", tags=["simulate"])


@router.post("/savings")
def savings_sim(
    payload: SavingsSimRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return simulate_savings(
        current.monthly_income, expenses, payload.adjustments, payload.extra_investment
    )


@router.post("/whatif")
def whatif_sim(
    payload: WhatIfRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return what_if(current.monthly_income, expenses, payload.scenario, payload.params)
