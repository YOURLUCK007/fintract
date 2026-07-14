"""Shared time-bucketing helpers.

Uses rolling 30-day windows ending today rather than calendar months, so the
"current month" is never a partial/sparse bucket regardless of today's date.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from ..models import Expense

WINDOW_DAYS = 30


def rolling_windows(expenses: list[Expense], months: int = 6) -> list[tuple[str, float]]:
    """Return [(label, total)] for ``months`` consecutive 30-day windows, oldest first."""
    today = date.today()
    buckets: list[float] = [0.0] * months
    for e in expenses:
        days_ago = (today - e.spent_on).days
        if days_ago < 0:
            days_ago = 0
        idx = days_ago // WINDOW_DAYS
        if 0 <= idx < months:
            buckets[months - 1 - idx] += e.amount
    labels = []
    for i in range(months):
        end = today - timedelta(days=WINDOW_DAYS * (months - 1 - i))
        labels.append(end.strftime("%b"))
    return list(zip(labels, [round(b, 2) for b in buckets]))


def last_30_days(expenses: list[Expense]) -> list[Expense]:
    cutoff = date.today() - timedelta(days=WINDOW_DAYS)
    return [e for e in expenses if e.spent_on >= cutoff]


def category_totals(expenses: list[Expense]) -> dict[str, float]:
    agg: dict[str, float] = defaultdict(float)
    for e in expenses:
        agg[e.category] += e.amount
    return agg
