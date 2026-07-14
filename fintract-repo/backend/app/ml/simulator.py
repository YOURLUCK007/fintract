"""Savings simulator + what-if scenario engine.

Pure, deterministic financial math on top of the user's real spend so the UI can
show instant projections for hypothetical changes.
"""
from __future__ import annotations

from collections import defaultdict

from ..models import Expense


def _monthly_by_category(expenses: list[Expense]) -> tuple[dict[str, float], float]:
    totals: dict[str, float] = defaultdict(float)
    for e in expenses:
        totals[e.category] += e.amount
    months = max(len({f"{e.spent_on.year}-{e.spent_on.month:02d}" for e in expenses}), 1)
    monthly = {k: v / months for k, v in totals.items()}
    return monthly, sum(monthly.values())


def _project(monthly_savings: float, years: int = 5, annual_return: float = 0.08) -> list[dict]:
    """Compound monthly contributions at ``annual_return`` for ``years`` years."""
    r = annual_return / 12
    bal = 0.0
    out = []
    for m in range(1, years * 12 + 1):
        bal = bal * (1 + r) + max(monthly_savings, 0)
        if m % 12 == 0:
            out.append({"year": m // 12, "balance": round(bal)})
    return out


def simulate_savings(
    monthly_income: float,
    expenses: list[Expense],
    adjustments: dict[str, float],
    extra_investment: float = 0.0,
) -> dict:
    """``adjustments`` maps category -> percent reduction (0..100)."""
    monthly, spend_total = _monthly_by_category(expenses)
    base_savings = monthly_income - spend_total

    saved_from_cuts = 0.0
    lines = []
    for cat, pct in adjustments.items():
        pct = max(0.0, min(100.0, float(pct)))
        cur = monthly.get(cat, 0.0)
        cut = cur * pct / 100.0
        if cut > 0:
            saved_from_cuts += cut
            lines.append({"category": cat, "reduce_pct": round(pct), "saves": round(cut)})

    new_monthly_savings = base_savings + saved_from_cuts - extra_investment
    total_monthly_gain = saved_from_cuts  # extra_investment is redirected, not new savings

    return {
        "base_monthly_savings": round(base_savings),
        "new_monthly_savings": round(new_monthly_savings + extra_investment),
        "monthly_gain": round(total_monthly_gain + extra_investment),
        "weekly_gain": round((total_monthly_gain + extra_investment) / 4.33),
        "annual_gain": round((total_monthly_gain + extra_investment) * 12),
        "adjustments": lines,
        "projection_5yr": _project(new_monthly_savings + extra_investment),
    }


def what_if(monthly_income: float, expenses: list[Expense], scenario: str, params: dict) -> dict:
    """Handle discrete what-if scenarios. Returns headline + projection + summary."""
    monthly, spend_total = _monthly_by_category(expenses)
    base_savings = monthly_income - spend_total
    p = params or {}

    if scenario == "extra_savings":
        amt = float(p.get("amount", 5000))
        new_savings = base_savings + amt
        return {
            "headline": f"Saving ₹{amt:,.0f} more/month",
            "monthly_savings": round(new_savings),
            "annual_savings": round(new_savings * 12),
            "projection_5yr": _project(new_savings),
            "summary": f"You'd save ₹{new_savings*12:,.0f}/year and ~₹{_project(new_savings)[-1]['balance']:,.0f} in 5 years (at 8%).",
        }

    if scenario == "purchase":
        cost = float(p.get("amount", 50000))
        months_to_afford = round(cost / base_savings, 1) if base_savings > 0 else None
        affordable = base_savings > 0 and cost <= base_savings * 6
        msg = (
            f"At ₹{base_savings:,.0f}/mo savings, a ₹{cost:,.0f} purchase takes ~{months_to_afford} months to fund."
            if months_to_afford else
            "Your current savings rate is ≤0, so this purchase isn't fundable without cutting expenses."
        )
        return {
            "headline": f"Can I afford ₹{cost:,.0f}?",
            "affordable": affordable,
            "months_to_afford": months_to_afford,
            "monthly_savings": round(base_savings),
            "summary": msg,
        }

    if scenario == "salary_change":
        pct = float(p.get("percent", 20))
        new_income = monthly_income * (1 + pct / 100.0)
        new_savings = new_income - spend_total
        return {
            "headline": f"Salary {'+' if pct>=0 else ''}{pct:.0f}%",
            "new_income": round(new_income),
            "monthly_savings": round(new_savings),
            "annual_savings": round(new_savings * 12),
            "projection_5yr": _project(new_savings),
            "summary": f"New income ₹{new_income:,.0f}/mo lifts savings to ₹{new_savings:,.0f}/mo.",
        }

    if scenario == "loan_prepay":
        balance = float(p.get("balance", 300000))
        rate = float(p.get("rate", 10)) / 100.0
        emi = float(p.get("emi", 10000))
        # Months saved by prepaying now vs amortized payoff (rough).
        interest_saved = round(balance * rate * (balance / (emi * 12)) * 0.5)
        return {
            "headline": f"Prepay ₹{balance:,.0f} loan",
            "interest_saved": interest_saved,
            "summary": f"Prepaying could save roughly ₹{interest_saved:,.0f} in interest over the loan life.",
        }

    if scenario == "inflation":
        rate = float(p.get("rate", 6)) / 100.0
        future_spend = spend_total * (1 + rate) ** 5
        return {
            "headline": f"Inflation @ {rate*100:.0f}%/yr",
            "spend_today": round(spend_total),
            "spend_in_5yr": round(future_spend),
            "summary": f"Your ₹{spend_total:,.0f}/mo lifestyle would cost ₹{future_spend:,.0f}/mo in 5 years.",
        }

    return {"headline": "Unknown scenario", "summary": "No simulation available for this scenario."}
