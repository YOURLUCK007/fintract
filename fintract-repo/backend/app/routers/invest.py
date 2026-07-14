"""Investment advisor endpoints: allocation, growth simulation, suitability."""
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.invest import allocation, growth_simulation, suitability_score
from ..models import Expense, User

router = APIRouter(prefix="/api/invest", tags=["investments"])


def _investable_monthly(user: User, expenses: list[Expense]) -> float:
    by_month: dict[str, float] = defaultdict(float)
    for e in expenses:
        by_month[f"{e.spent_on.year}-{e.spent_on.month:02d}"] += e.amount
    avg_spend = (sum(by_month.values()) / len(by_month)) if by_month else user.monthly_income * 0.65
    return max(user.monthly_income - avg_spend, user.monthly_income * 0.1)


@router.get("/advice")
def advice(
    risk: int | None = Query(None, ge=1, le=5),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    r = risk or current.risk_tolerance
    investable = _investable_monthly(current, expenses)
    savings_rate = (investable / current.monthly_income * 100) if current.monthly_income else 0.0
    return {
        "risk": r,
        "investable_monthly": round(investable),
        "suitability": suitability_score(current.monthly_income, savings_rate, r),
        "allocation": allocation(r, investable),
        "growth": growth_simulation(investable, r),
        "disclaimer": "Educational simulation only — not guaranteed financial advice.",
    }
