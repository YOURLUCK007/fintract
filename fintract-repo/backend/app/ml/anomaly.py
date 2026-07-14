"""Anomaly & duplicate detection for transactions.

Uses scikit-learn IsolationForest on per-category amount features, plus a simple
rule for duplicate detection (same category, near-identical amount within a short
time window).
"""
from __future__ import annotations

from datetime import timedelta

import numpy as np
from sklearn.ensemble import IsolationForest

from ..models import Expense


def detect_anomalies(expenses: list[Expense]) -> dict[int, bool]:
    """Return {expense_id: is_anomaly}. Trains a small IsolationForest per run.

    An expense is flagged when its amount is an outlier relative to the user's
    overall spending distribution (log-scaled to reduce skew).
    """
    flags: dict[int, bool] = {e.id: False for e in expenses}
    amounts = [e.amount for e in expenses if e.category != "Investments"]
    if len(amounts) < 8:
        return flags

    X = np.log1p(np.array([e.amount for e in expenses]).reshape(-1, 1))
    contamination = min(0.15, max(0.03, 3 / len(expenses)))
    model = IsolationForest(n_estimators=120, contamination=contamination, random_state=42)
    preds = model.fit_predict(X)  # -1 = outlier
    for exp, pred in zip(expenses, preds):
        # Only surface high-value outliers (ignore unusually *small* spends).
        if pred == -1 and exp.amount > float(np.median(amounts)) and exp.category != "Investments":
            flags[exp.id] = True
    return flags


def detect_duplicates(expenses: list[Expense], window_days: int = 1, tol: float = 0.01) -> dict[int, bool]:
    """Flag likely duplicate charges: same description, near-identical amount, close in time.

    Matching on description (not just category) keeps this precise — recurring but
    distinct transactions in the same category are not treated as duplicates.
    """
    flags: dict[int, bool] = {e.id: False for e in expenses}
    ordered = sorted(expenses, key=lambda e: (e.description.lower(), e.spent_on))
    for i, a in enumerate(ordered):
        if a.amount < 200:  # ignore trivial repeated small charges
            continue
        for b in ordered[i + 1:]:
            if b.description.lower() != a.description.lower():
                break
            if abs((b.spent_on - a.spent_on).days) > window_days:
                continue
            hi = max(a.amount, b.amount)
            if hi > 0 and abs(a.amount - b.amount) / hi <= tol:
                flags[a.id] = True
                flags[b.id] = True
    return flags


def anomaly_summary(expenses: list[Expense]) -> list[dict]:
    """Human-readable anomaly/duplicate messages for the UI."""
    anomalies = detect_anomalies(expenses)
    dups = detect_duplicates(expenses)
    out: list[dict] = []

    # Surface high-value anomalies first (most actionable), largest first.
    spikes = sorted((e for e in expenses if anomalies.get(e.id)), key=lambda e: e.amount, reverse=True)
    for e in spikes:
        out.append({
            "type": "spike",
            "text": f"Unusual: <strong>{e.description} ₹{e.amount:,.0f}</strong> "
                    f"is well above your typical {e.category.lower()} spend.",
        })

    seen_dup_pairs = set()
    for e in sorted((e for e in expenses if dups.get(e.id)), key=lambda e: e.amount, reverse=True):
        key = (e.description.lower(), round(e.amount / 50))
        if key in seen_dup_pairs:
            continue
        seen_dup_pairs.add(key)
        out.append({
            "type": "dup",
            "text": f"Possible duplicate: <strong>{e.description} ₹{e.amount:,.0f}</strong> "
                    f"charged twice within a day.",
        })
    return out[:6]
