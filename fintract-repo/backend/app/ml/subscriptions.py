"""Subscription / recurring-payment detector.

Groups transactions by a normalized merchant name and flags groups that recur
with a roughly stable amount across multiple charges. Estimates monthly and
annual cost and infers the billing cadence from the average gap between charges.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from statistics import mean

# Hints that a merchant is subscription-like (used to relax the recurrence rule).
_SUBSCRIPTION_HINTS = re.compile(
    r"netflix|spotify|prime|hotstar|youtube|subscription|gym|membership|"
    r"jio|airtel|vi |broadband|wifi|insurance|emi|rent|icloud|google one|"
    r"disney|sony|zee|sonyliv|apple",
    re.IGNORECASE,
)


def _normalize(desc: str) -> str:
    d = desc.lower().strip()
    d = re.sub(r"[-#0-9]+", " ", d)          # drop order numbers/ids
    d = re.sub(r"\b(order|payment|recharge|monthly|subscription|bill)\b", " ", d)
    d = re.sub(r"\s+", " ", d).strip()
    return d


def _cadence(avg_gap: float) -> str:
    if avg_gap <= 10:
        return "weekly"
    if avg_gap <= 45:
        return "monthly"
    if avg_gap <= 100:
        return "quarterly"
    return "yearly"


def _monthly_factor(cadence: str) -> float:
    return {"weekly": 4.33, "monthly": 1.0, "quarterly": 1 / 3, "yearly": 1 / 12}[cadence]


def detect_subscriptions(expenses: list[dict] | list) -> list[dict]:
    """Return detected subscriptions sorted by estimated monthly cost (desc).

    Accepts Expense ORM objects (uses .description/.amount/.spent_on).
    """
    groups: dict[str, list] = defaultdict(list)
    for e in expenses:
        groups[_normalize(e.description)].append(e)

    subs: list[dict] = []
    for key, items in groups.items():
        if not key:
            continue
        items = sorted(items, key=lambda x: x.spent_on)
        amounts = [x.amount for x in items]
        avg_amt = mean(amounts)
        hinted = bool(_SUBSCRIPTION_HINTS.search(items[0].description))

        # Need >=2 charges to call it recurring (or 1 charge from a known service).
        if len(items) < 2 and not hinted:
            continue

        # Amounts must be roughly stable (within ~20% of the mean).
        if len(items) >= 2:
            spread = (max(amounts) - min(amounts)) / avg_amt if avg_amt else 1
            if spread > 0.35 and not hinted:
                continue
            gaps = [(items[i].spent_on - items[i - 1].spent_on).days for i in range(1, len(items))]
            avg_gap = mean(gaps) if gaps else 30
        else:
            avg_gap = 30  # assume monthly for a single hinted charge

        cadence = _cadence(avg_gap)
        monthly = avg_amt * _monthly_factor(cadence)
        subs.append({
            "name": items[-1].description[:60],
            "category": items[-1].category,
            "amount": round(avg_amt),
            "cadence": cadence,
            "charges": len(items),
            "monthly_cost": round(monthly),
            "annual_cost": round(monthly * 12),
            "last_charged": items[-1].spent_on.isoformat(),
        })

    subs.sort(key=lambda s: s["monthly_cost"], reverse=True)
    return subs


def summarize(expenses) -> dict:
    subs = detect_subscriptions(expenses)
    return {
        "subscriptions": subs,
        "count": len(subs),
        "total_monthly": round(sum(s["monthly_cost"] for s in subs)),
        "total_annual": round(sum(s["annual_cost"] for s in subs)),
    }
