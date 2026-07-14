"""Planner endpoints: round-up, emergency fund, diversification, Monte Carlo,
financial twin, gamification, sustainability, and the risk-profile quiz."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.montecarlo import run_monte_carlo
from ..ml.planner import (
    diversification,
    emergency_plan,
    gamification,
    roundup_savings,
    sustainability,
)
from ..ml.twin import simulate_twin
from ..models import Asset, Expense, Goal, Liability, User
from ..schemas import MonteCarloRequest, RiskQuizRequest, TwinRequest

router = APIRouter(prefix="/api/plan", tags=["planner"])


def _expenses(db: Session, user: User) -> list[Expense]:
    return db.query(Expense).filter(Expense.user_id == user.id).all()


@router.get("/roundup")
def roundup(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return roundup_savings(_expenses(db, current))


@router.get("/emergency")
def emergency(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    goals = db.query(Goal).filter(Goal.user_id == current.id).all()
    assets = db.query(Asset).filter(Asset.user_id == current.id).all()
    return emergency_plan(current.monthly_income, _expenses(db, current), goals, assets)


@router.get("/diversification")
def diversify(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    assets = db.query(Asset).filter(Asset.user_id == current.id).all()
    return diversification(assets)


@router.post("/montecarlo")
def montecarlo(
    payload: MonteCarloRequest,
    current: User = Depends(get_current_user),
):
    return run_monte_carlo(
        monthly_investment=payload.monthly_investment,
        years=payload.years,
        risk=payload.risk or current.risk_tolerance,
        initial=payload.initial,
    )


@router.post("/twin")
def twin(
    payload: TwinRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    assets = db.query(Asset).filter(Asset.user_id == current.id).all()
    liabilities = db.query(Liability).filter(Liability.user_id == current.id).all()
    return simulate_twin(
        current.monthly_income, _expenses(db, current), assets, liabilities,
        payload.scenario, payload.params,
    )


@router.get("/gamification")
def game(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    goals = db.query(Goal).filter(Goal.user_id == current.id).all()
    assets = db.query(Asset).filter(Asset.user_id == current.id).all()
    liabilities = db.query(Liability).filter(Liability.user_id == current.id).all()
    return gamification(current.monthly_income, _expenses(db, current), goals, assets, liabilities)


@router.get("/sustainability")
def carbon(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return sustainability(_expenses(db, current))


@router.post("/risk-quiz")
def risk_quiz(
    payload: RiskQuizRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    answers = [max(1, min(5, int(a))) for a in payload.answers] or [3]
    risk = round(sum(answers) / len(answers))
    risk = max(1, min(5, risk))
    current.risk_tolerance = risk
    db.commit()
    labels = {1: "Very Conservative", 2: "Conservative", 3: "Moderate", 4: "Aggressive", 5: "Very Aggressive"}
    return {
        "risk_tolerance": risk,
        "profile": labels[risk],
        "summary": f"Based on your answers, your profile is {labels[risk]} (risk {risk}/5). "
                   "Your investment advice and simulations now use this profile.",
    }
