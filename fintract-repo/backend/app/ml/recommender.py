"""Personalized saving recommendations derived from the user's category spend."""
from __future__ import annotations

from collections import defaultdict

from ..models import Expense


def _category_totals(expenses: list[Expense]) -> dict[str, float]:
    agg: dict[str, float] = defaultdict(float)
    for e in expenses:
        agg[e.category] += e.amount
    return agg


def recommendations(expenses: list[Expense]) -> list[dict]:
    """Return ranked recommendations with estimated monthly savings and reasoning."""
    totals = _category_totals(expenses)
    months = max(len({f"{e.spent_on.year}-{e.spent_on.month:02d}" for e in expenses}), 1)
    monthly = {k: v / months for k, v in totals.items()}
    recs: list[dict] = []

    food = monthly.get("Food", 0)
    if food > 3000:
        recs.append({
            "title": "Reduce food delivery by 20%",
            "why": f"You spend ~₹{food:,.0f}/mo on food; cooking a few more meals weekly trims this.",
            "save": round(food * 0.20),
        })

    ent = monthly.get("Entertainment", 0)
    if ent > 500:
        recs.append({
            "title": "Cancel unused subscriptions",
            "why": "Recurring entertainment charges detected — review and drop the unused ones.",
            "save": round(min(ent * 0.5, 1200)),
        })

    travel = monthly.get("Travel", 0)
    if travel > 2000:
        recs.append({
            "title": "Shift to public transport 2×/week",
            "why": f"Fuel & ride-hailing is ~₹{travel:,.0f}/mo; public transport cuts it meaningfully.",
            "save": round(travel * 0.18),
        })

    shop = monthly.get("Shopping", 0)
    if shop > 4000:
        recs.append({
            "title": "Set a monthly shopping cap",
            "why": "Shopping is trending above budget — a hard cap keeps it in check.",
            "save": round(shop * 0.25),
        })

    recs.append({
        "title": "Auto-sweep idle balance to a liquid fund",
        "why": "Earn ~6% on cash that would otherwise sit idle in savings.",
        "save": 900,
    })

    recs.sort(key=lambda r: r["save"], reverse=True)
    return recs[:6]
