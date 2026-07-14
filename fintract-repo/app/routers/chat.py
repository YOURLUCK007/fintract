"""AI chat assistant — intent matching grounded in the user's real financial data."""
import re
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.forecast import savings_forecast
from ..ml.health_score import compute_health
from ..ml.invest import allocation
from ..ml.recommender import recommendations
from ..models import Expense, Goal, User
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _category_totals(expenses: list[Expense]) -> dict[str, float]:
    agg: dict[str, float] = defaultdict(float)
    for e in expenses:
        agg[e.category] += e.amount
    return agg


def _answer(user: User, expenses: list[Expense], goals: list[Goal], q: str) -> str:
    s = q.lower()
    totals = _category_totals(expenses)
    total = sum(totals.values()) or 1.0
    top = max(totals.items(), key=lambda kv: kv[1]) if totals else ("Others", 0)

    # affordability: "can i afford a ₹50,000 purchase"
    amt_match = re.search(r"(\d[\d,]{2,})", s.replace("₹", ""))

    if re.search(r"most|highest|where.*spend|top categ|biggest", s):
        pct = top[1] / total * 100
        return (f"Your biggest category is <strong>{top[0]}</strong> at ₹{top[1]:,.0f} "
                f"(~{pct:.0f}% of tracked spend).")

    if re.search(r"save.*\d|how.*save|reduce", s):
        recs = recommendations(expenses)
        total_save = sum(r["save"] for r in recs[:3])
        lines = "; ".join(f"{r['title']} (₹{r['save']:,.0f})" for r in recs[:3])
        return f"Top ways to save: {lines}. That's about <strong>₹{total_save:,.0f}/mo</strong> combined."

    if re.search(r"afford|can i.*buy", s) and amt_match:
        target = float(amt_match.group(1).replace(",", ""))
        fc = savings_forecast(user.monthly_income, expenses, "balanced")
        monthly = fc["monthly"] or 1
        months = target / monthly
        verdict = "✅ Affordable" if months <= 3 else "⚠️ Stretch — plan ahead"
        return (f"A ₹{target:,.0f} purchase ≈ {months:.1f} months of your current savings "
                f"(₹{monthly:,.0f}/mo). {verdict}.")

    if re.search(r"invest|portfolio|allocat|plan based", s):
        alloc = allocation(user.risk_tolerance, user.monthly_income * 0.25)
        parts = ", ".join(f"{a['percent']}% {a['name']}" for a in alloc[:5])
        return (f"For your risk level {user.risk_tolerance}, a suggested split: {parts}. "
                f"<em>Educational only, not guaranteed advice.</em>")

    if re.search(r"year|forecast|how much.*save", s):
        fc = savings_forecast(user.monthly_income, expenses, "balanced")
        agg = savings_forecast(user.monthly_income, expenses, "aggressive")
        return (f"Balanced plan → about <strong>₹{fc['yearly']:,.0f}</strong> in 12 months. "
                f"Aggressive plan → <strong>₹{agg['yearly']:,.0f}</strong>.")

    if re.search(r"health|score", s):
        h = compute_health(user.monthly_income, expenses, goals)
        return f"Your financial health score is <strong>{h['score']}/100</strong>. {h['tips'][0] if h['tips'] else ''}"

    if re.search(r"goal", s):
        if not goals:
            return "You have no goals yet — add one and I'll compute its completion date."
        g = goals[0]
        pct = g.saved_amount / g.target_amount * 100 if g.target_amount else 0
        return f"Your goal '<strong>{g.name}</strong>' is {pct:.0f}% funded (₹{g.saved_amount:,.0f}/₹{g.target_amount:,.0f})."

    fc = savings_forecast(user.monthly_income, expenses, "balanced")
    return (f"Here's a snapshot: monthly savings ≈ <strong>₹{fc['monthly']:,.0f}</strong>, "
            f"top category <strong>{top[0]}</strong>. Ask me about saving, affording a purchase, "
            f"or an investment plan.")


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    goals = db.query(Goal).filter(Goal.user_id == current.id).all()
    return ChatResponse(reply=_answer(current, expenses, goals, payload.message))
