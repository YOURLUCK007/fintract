"""Analytics/overview endpoints: KPIs, category & trend charts, insights, heatmap, anomalies."""
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..ml.aggregate import last_30_days, rolling_windows
from ..ml.anomaly import anomaly_summary
from ..ml.health_score import compute_health
from ..models import Expense, Goal, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

CATEGORY_COLORS = {
    "Food": "#6c8cff", "Travel": "#8a6bff", "Shopping": "#18d4a0", "Bills": "#ffb23e",
    "Healthcare": "#ff6b81", "Entertainment": "#46c2ff", "Education": "#c98bff",
    "Investments": "#88e0c0", "Others": "#9aa6bd",
}


@router.get("/overview")
def overview(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    goals = db.query(Goal).filter(Goal.user_id == current.id).all()

    # Rolling 30-day windows (stable regardless of the current calendar day).
    windows = rolling_windows(expenses, months=6)
    month_labels = [label for label, _ in windows]
    spending = [total for _, total in windows]
    income = [round(current.monthly_income, 2)] * len(windows)

    this_month_spend = spending[-1] if spending else 0.0
    non_zero = [v for v in spending if v > 0]
    avg_spend = (sum(non_zero) / len(non_zero)) if non_zero else 0.0
    ref_spend = this_month_spend or avg_spend
    monthly_savings = max(current.monthly_income - ref_spend, 0.0)
    savings_rate = (monthly_savings / current.monthly_income * 100) if current.monthly_income else 0.0

    # Category breakdown over the last 30 days (fallback to all-time if empty).
    recent = last_30_days(expenses) or expenses
    cat_totals: dict[str, float] = defaultdict(float)
    for e in recent:
        cat_totals[e.category] += e.amount

    categories = [
        {"name": k, "value": round(v, 2), "color": CATEGORY_COLORS.get(k, "#9aa6bd")}
        for k, v in sorted(cat_totals.items(), key=lambda kv: kv[1], reverse=True)
    ]

    health = compute_health(current.monthly_income, expenses, goals)
    insights = _build_insights(current, expenses, spending, cat_totals, savings_rate)
    heatmap = _build_heatmap(expenses)

    def money(v: float) -> str:
        return f"₹{v:,.0f}"

    kpis = [
        {"label": "Monthly income", "value": money(current.monthly_income), "delta": "profile", "dir": "up"},
        {"label": "This month spend", "value": money(this_month_spend or avg_spend),
         "delta": f"{'-' if (this_month_spend or avg_spend) <= avg_spend else '+'}vs avg", "dir": "up"},
        {"label": "Monthly savings", "value": money(monthly_savings), "delta": f"{savings_rate:.0f}% rate", "dir": "up"},
        {"label": "Savings rate", "value": f"{savings_rate:.0f}%", "delta": "of income", "dir": "up"},
    ]

    return {
        "kpis": kpis,
        "months": month_labels,
        "income": income,
        "spending": spending,
        "trend": spending,
        "categories": categories,
        "health": health,
        "insights": insights,
        "heatmap": heatmap,
    }


def _build_insights(user: User, expenses, spending: list[float], cat_totals, savings_rate) -> list[dict]:
    insights: list[dict] = []
    if cat_totals:
        top_cat = max(cat_totals.items(), key=lambda kv: kv[1])
        insights.append({"em": "📊", "text": f"Your biggest category is <strong>{top_cat[0]}</strong> at ₹{top_cat[1]:,.0f}."})

    if len(spending) >= 2 and spending[-2] > 0:
        prev, cur = spending[-2], spending[-1]
        change = (cur - prev) / prev * 100
        arrow = "dropped" if change < 0 else "rose"
        insights.append({"em": "📈", "text": f"Total spend <strong>{arrow} {abs(change):.0f}%</strong> vs the prior 30 days."})

    insights.append({"em": "💰", "text": f"Your savings rate is <strong>{savings_rate:.0f}%</strong> "
                                          f"({'above' if savings_rate >= 20 else 'below'} the 20% benchmark)."})

    recurring = [e for e in expenses if e.category == "Entertainment"]
    if recurring:
        insights.append({"em": "🔁", "text": f"{len(recurring)} entertainment/subscription charges detected — review for savings."})
    return insights[:4]


def _build_heatmap(expenses) -> list[float]:
    """Daily spend intensity for the last ~130 days, normalized 0..1."""
    today = date.today()
    daily: dict[date, float] = defaultdict(float)
    for e in expenses:
        daily[e.spent_on] += e.amount
    days = 130
    vals = [daily.get(today - timedelta(days=days - 1 - i), 0.0) for i in range(days)]
    mx = max(vals) or 1.0
    return [round(v / mx, 3) for v in vals]


@router.get("/anomalies")
def anomalies(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    return {"anomalies": anomaly_summary(expenses)}
