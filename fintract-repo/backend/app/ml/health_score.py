"""Financial-health scoring (0–100) across six weighted dimensions."""
from __future__ import annotations

from ..models import Expense, Goal
from .aggregate import rolling_windows

WEIGHTS = {
    "Savings ratio": 0.25,
    "Spending discipline": 0.18,
    "Investment habits": 0.17,
    "Emergency fund": 0.15,
    "Debt levels": 0.10,
    "Budget adherence": 0.15,
}


def _avg_monthly_spend(expenses: list[Expense]) -> float:
    values = [v for _label, v in rolling_windows(expenses, months=6) if v > 0]
    return sum(values) / max(len(values), 1) if values else 0.0


def compute_health(monthly_income: float, expenses: list[Expense], goals: list[Goal]) -> dict:
    avg_spend = _avg_monthly_spend(expenses)
    savings_rate = max((monthly_income - avg_spend) / monthly_income, 0.0) if monthly_income else 0.0

    invest_total = sum(e.amount for e in expenses if e.category == "Investments")
    total_spend = sum(e.amount for e in expenses) or 1.0
    invest_ratio = invest_total / total_spend

    emergency_goal = next((g for g in goals if "emergency" in g.name.lower()), None)
    emergency_pct = (emergency_goal.saved_amount / emergency_goal.target_amount) if emergency_goal and emergency_goal.target_amount else 0.0

    discretionary = sum(e.amount for e in expenses if e.category in {"Shopping", "Entertainment", "Food"})
    discipline = max(1 - (discretionary / total_spend) / 0.6, 0.0)

    breakdown = {
        "Savings ratio": min(savings_rate / 0.35, 1.0) * 100,
        "Spending discipline": min(discipline, 1.0) * 100,
        "Investment habits": min(invest_ratio / 0.15, 1.0) * 100,
        "Emergency fund": min(emergency_pct, 1.0) * 100,
        "Debt levels": 82.0,  # no debt module in demo; assume healthy baseline
        "Budget adherence": min(discipline * 0.9 + 0.2, 1.0) * 100,
    }
    score = sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS)

    tips = []
    worst = sorted(breakdown.items(), key=lambda kv: kv[1])[:2]
    for name, val in worst:
        tips.append(f"Improve <strong>{name}</strong> (currently {val:.0f}/100) to raise your score most.")

    return {
        "score": round(score),
        "breakdown": [{"label": k, "pct": round(v)} for k, v in breakdown.items()],
        "tips": tips,
        "savings_rate": round(savings_rate * 100, 1),
    }
