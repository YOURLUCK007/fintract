"""Savings & cash-flow forecasting using linear regression over monthly aggregates."""
from __future__ import annotations

from datetime import date

import numpy as np
from sklearn.linear_model import LinearRegression

from ..models import Expense
from .aggregate import rolling_windows

PLAN_FACTORS = {
    "conservative": 0.75,
    "balanced": 1.0,
    "aggressive": 1.30,
}
PLAN_GROWTH = {"conservative": 0.04, "balanced": 0.07, "aggressive": 0.10}


def monthly_spend_values(expenses: list[Expense], months: int = 6) -> list[float]:
    """Spend per rolling 30-day window (stable regardless of today's calendar day)."""
    return [total for _label, total in rolling_windows(expenses, months=months)]


def _trend_forecast(values: list[float], periods: int) -> list[float]:
    """Fit a linear trend and project ``periods`` steps forward (clamped >= 0)."""
    if len(values) < 2:
        base = values[0] if values else 0.0
        return [max(base, 0.0)] * periods
    X = np.arange(len(values)).reshape(-1, 1)
    y = np.array(values)
    model = LinearRegression().fit(X, y)
    future_X = np.arange(len(values), len(values) + periods).reshape(-1, 1)
    preds = model.predict(future_X)
    return [max(float(p), 0.0) for p in preds]


def savings_forecast(monthly_income: float, expenses: list[Expense], plan: str = "balanced") -> dict:
    """Project weekly/monthly/yearly savings and a 12-month cumulative curve."""
    # No fabricated spend for brand-new users: an empty history means zero outflow.
    spend_values = [v for v in monthly_spend_values(expenses) if v > 0] or [0.0]

    predicted_spend = _trend_forecast(spend_values, 12)
    factor = PLAN_FACTORS.get(plan, 1.0)

    monthly_savings = []
    for ps in predicted_spend:
        base_saving = max(monthly_income - ps, 0.0)
        # Plan factor models how aggressively the user trims discretionary spend.
        adjusted = base_saving + (ps * 0.12 * (factor - 0.75))
        monthly_savings.append(max(adjusted, 0.0))

    avg_monthly = float(np.mean(monthly_savings))
    cumulative, running = [], 0.0
    for m in monthly_savings:
        running += m
        cumulative.append(round(running, 2))

    return {
        "plan": plan,
        "weekly": round(avg_monthly / 4.33, 2),
        "monthly": round(avg_monthly, 2),
        "yearly": round(cumulative[-1], 2),
        "projection": cumulative,
        "upper": [round(c * 1.12, 2) for c in cumulative],
        "lower": [round(c * 0.9, 2) for c in cumulative],
        "growth": PLAN_GROWTH.get(plan, 0.07),
        "labels": [f"M{i+1}" for i in range(12)],
    }


def cashflow_forecast(monthly_income: float, expenses: list[Expense], periods: int = 6) -> dict:
    spend_values = [v for v in monthly_spend_values(expenses) if v > 0] or [0.0]
    outflow = _trend_forecast(spend_values, periods)
    inflow = [round(monthly_income, 2)] * periods
    today = date.today()
    labels = []
    m = today.month
    for _ in range(periods):
        m += 1
        yy = today.year + (m - 1) // 12
        mm = (m - 1) % 12 + 1
        labels.append(date(yy, mm, 1).strftime("%b"))
    return {
        "labels": labels,
        "inflow": inflow,
        "outflow": [round(o, 2) for o in outflow],
    }
