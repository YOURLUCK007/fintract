"""AI budget generator.

Builds an adaptive monthly budget from the user's income and historical spend.
Blends a 50/30/20 needs/wants/savings framework with the user's real category
averages so the plan is realistic yet nudges toward healthy targets.
"""
from __future__ import annotations

from collections import defaultdict

from ..models import Expense

# Which categories count as "needs" vs "wants" for the 50/30/20 split.
NEEDS = {"Bills", "Healthcare", "Education", "Others"}
WANTS = {"Food", "Travel", "Shopping", "Entertainment"}


def _monthly_by_category(expenses: list[Expense]) -> tuple[dict[str, float], int]:
    totals: dict[str, float] = defaultdict(float)
    for e in expenses:
        totals[e.category] += e.amount
    months = max(len({f"{e.spent_on.year}-{e.spent_on.month:02d}" for e in expenses}), 1)
    return {k: v / months for k, v in totals.items()}, months


def generate_budget(monthly_income: float, expenses: list[Expense]) -> dict:
    """Return a recommended budget: per-category caps + needs/wants/savings split."""
    monthly, months = _monthly_by_category(expenses)
    spend_total = sum(monthly.values())

    # Target envelopes (50/30/20). Savings target is whatever is left after caps.
    needs_target = monthly_income * 0.50
    wants_target = monthly_income * 0.30
    savings_target = monthly_income * 0.20

    needs_now = sum(v for k, v in monthly.items() if k in NEEDS)
    wants_now = sum(v for k, v in monthly.items() if k in WANTS)

    def _cap(cat: str, current: float) -> float:
        """Recommend a cap: keep needs near actual, trim wants toward target."""
        if cat in WANTS and wants_now > wants_target and wants_now > 0:
            return round(current * (wants_target / wants_now))
        if cat in NEEDS and needs_now > needs_target and needs_now > 0:
            return round(current * (needs_target / needs_now))
        return round(current)

    categories = []
    for cat in sorted(monthly, key=lambda c: monthly[c], reverse=True):
        current = monthly[cat]
        if current <= 0:
            continue
        rec = _cap(cat, current)
        categories.append({
            "category": cat,
            "current": round(current),
            "recommended": rec,
            "delta": round(rec - current),  # negative = suggested cut
            "bucket": "needs" if cat in NEEDS else ("wants" if cat in WANTS else "savings"),
        })

    recommended_spend = sum(c["recommended"] for c in categories)
    projected_savings = round(monthly_income - recommended_spend)

    return {
        "months_analyzed": months,
        "monthly_income": round(monthly_income),
        "current_spend": round(spend_total),
        "recommended_spend": recommended_spend,
        "current_savings": round(monthly_income - spend_total),
        "projected_savings": projected_savings,
        "split": {
            "needs": {"target": round(needs_target), "current": round(needs_now)},
            "wants": {"target": round(wants_target), "current": round(wants_now)},
            "savings": {"target": round(savings_target), "projected": projected_savings},
        },
        "categories": categories,
    }
