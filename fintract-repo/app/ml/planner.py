"""Planner analytics: round-up savings, emergency fund, diversification,
gamification, and sustainability (carbon) insights."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

from ..models import Asset, Expense, Goal, Liability

# Approx kg CO2e per rupee spent, by category (coarse spend-based factors).
CARBON_FACTORS = {
    "Travel": 0.020,
    "Food": 0.010,
    "Shopping": 0.008,
    "Bills": 0.015,
    "Entertainment": 0.004,
    "Healthcare": 0.004,
    "Education": 0.003,
    "Investments": 0.0,
    "Others": 0.005,
}

ECO_TIPS = {
    "Travel": "Try public transport, carpooling, or combining trips to cut travel emissions.",
    "Food": "Reducing food delivery and food waste lowers both cost and footprint.",
    "Bills": "LED bulbs, efficient appliances, and mindful AC use cut electricity emissions.",
    "Shopping": "Buying durable goods and repairing instead of replacing reduces impact.",
}


def _monthly_totals(expenses: list[Expense]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for e in expenses:
        totals[f"{e.spent_on.year}-{e.spent_on.month:02d}"] += e.amount
    return dict(totals)


def _avg_monthly_spend(expenses: list[Expense]) -> float:
    totals = _monthly_totals(expenses)
    return sum(totals.values()) / max(len(totals), 1) if totals else 0.0


# ---------- round-up savings ----------
def roundup_savings(expenses: list[Expense], round_to: int = 100) -> dict:
    items = []
    total = 0.0
    for e in expenses:
        saved = (round_to - e.amount % round_to) % round_to
        if saved > 0:
            total += saved
            items.append({"description": e.description, "amount": e.amount, "roundup": round(saved)})
    months = max(len(_monthly_totals(expenses)), 1)
    monthly = total / months
    return {
        "round_to": round_to,
        "total_roundups": round(total),
        "transactions": len(items),
        "monthly_average": round(monthly),
        "yearly_estimate": round(monthly * 12),
        "five_year_estimate": round(monthly * 12 * 5 * 1.2),  # with modest growth
        "recent": items[:10],
        "summary": (
            f"Rounding each purchase up to the nearest ₹{round_to} would have saved "
            f"₹{total:,.0f} so far (~₹{monthly * 12:,.0f}/yr)."
            if items else "Add some expenses to see your spare-change savings potential."
        ),
    }


# ---------- emergency fund planner ----------
def emergency_plan(
    monthly_income: float,
    expenses: list[Expense],
    goals: list[Goal],
    assets: list[Asset],
    months_cover: int = 6,
) -> dict:
    spend = _avg_monthly_spend(expenses)
    target = spend * months_cover
    emergency_goal = next((g for g in goals if "emergency" in g.name.lower()), None)
    saved = emergency_goal.saved_amount if emergency_goal else 0.0
    cash = sum(a.value for a in assets if a.kind == "cash")
    covered = max(saved, cash)
    pct = min(covered / target, 1.0) if target > 0 else 0.0
    monthly_room = max(monthly_income - spend, 0)
    contribution = round(monthly_room * 0.3) if monthly_room else 0
    months_to_target = (
        math.ceil((target - covered) / contribution) if target > covered and contribution > 0 else 0
    )
    return {
        "avg_monthly_spend": round(spend),
        "months_cover": months_cover,
        "target": round(target),
        "current": round(covered),
        "progress_pct": round(pct * 100, 1),
        "suggested_monthly_contribution": contribution,
        "months_to_target": months_to_target,
        "summary": (
            f"Target: ₹{target:,.0f} ({months_cover}× your ₹{spend:,.0f}/mo spend). "
            f"You have ₹{covered:,.0f} ({pct * 100:.0f}%)."
            + (f" At ₹{contribution:,.0f}/mo you'd finish in ~{months_to_target} months." if months_to_target else "")
            if target > 0 else
            "Add some expenses first — your emergency fund target is sized from real monthly spending."
        ),
    }


# ---------- diversification analyzer ----------
def diversification(assets: list[Asset]) -> dict:
    total = sum(a.value for a in assets)
    if total <= 0:
        return {
            "total": 0, "allocation": [], "warnings": [],
            "suggestions": ["Add your assets in Net Worth to analyze diversification."],
            "score": None,
        }
    by_kind: dict[str, float] = defaultdict(float)
    for a in assets:
        by_kind[a.kind] += a.value
    allocation = [
        {"kind": k, "value": round(v), "pct": round(v / total * 100, 1)}
        for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1])
    ]
    warnings = [
        f"{row['pct']:.0f}% of your wealth is in {row['kind']} — over 50% in one class is risky."
        for row in allocation if row["pct"] > 50
    ]
    suggestions = []
    if "investment" not in by_kind:
        suggestions.append("You hold no market investments — consider index funds/ETFs for growth.")
    if "gold" not in by_kind and "property" not in by_kind:
        suggestions.append("Adding gold or property exposure can hedge against inflation.")
    if by_kind.get("cash", 0) / total > 0.6:
        suggestions.append("A large cash pile loses value to inflation — deploy the excess.")
    # Herfindahl-based diversification score (100 = perfectly spread).
    hhi = sum((v / total) ** 2 for v in by_kind.values())
    n = len(by_kind)
    score = round((1 - hhi) / (1 - 1 / n) * 100) if n > 1 else 0
    return {
        "total": round(total),
        "allocation": allocation,
        "warnings": warnings,
        "suggestions": suggestions or ["Your portfolio spread looks reasonable."],
        "score": score,
    }


# ---------- gamification ----------
def gamification(
    monthly_income: float,
    expenses: list[Expense],
    goals: list[Goal],
    assets: list[Asset],
    liabilities: list[Liability],
) -> dict:
    monthly = _monthly_totals(expenses)
    # Saving streak: consecutive recent months (up to now) spending under income.
    streak = 0
    today = date.today()
    y, m = today.year, today.month
    while True:
        key = f"{y}-{m:02d}"
        if key in monthly and monthly[key] < monthly_income:
            streak += 1
        elif streak > 0 or key not in monthly:
            break
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        if streak > 36:
            break

    badges = []
    def badge(icon, name, desc, earned):
        badges.append({"icon": icon, "name": name, "desc": desc, "earned": bool(earned)})

    total_saved_goals = sum(g.saved_amount for g in goals)
    badge("🧾", "First Steps", "Record your first expense", len(expenses) >= 1)
    badge("📊", "Habit Builder", "Record 10+ expenses", len(expenses) >= 10)
    badge("🎯", "Goal Setter", "Create your first goal", len(goals) >= 1)
    badge("💰", "Saver", "Save ₹10,000 towards goals", total_saved_goals >= 10000)
    badge("🏦", "Wealth Tracker", "Add your first asset", len(assets) >= 1)
    badge("🛡️", "Safety Net", "Start an emergency fund goal",
          any("emergency" in g.name.lower() for g in goals))
    badge("🔥", "On a Streak", "3-month saving streak", streak >= 3)
    badge("💳", "Debt Aware", "Track a liability", len(liabilities) >= 1)
    badge("🏆", "Goal Crusher", "Fully fund a goal",
          any(g.target_amount and g.saved_amount >= g.target_amount for g in goals))

    earned = sum(1 for b in badges if b["earned"])
    points = earned * 100 + streak * 50 + min(len(expenses), 50) * 2
    level = min(points // 300 + 1, 10)

    # Weekly challenge: spend less this week than last week.
    iso = today.isocalendar()
    this_week = sum(e.amount for e in expenses if e.spent_on.isocalendar()[:2] == iso[:2])
    last_week_num = iso[1] - 1 or 52
    last_week = sum(e.amount for e in expenses if e.spent_on.isocalendar()[1] == last_week_num
                    and abs((today - e.spent_on).days) < 21)
    return {
        "saving_streak_months": streak,
        "points": points,
        "level": level,
        "level_name": ["Rookie", "Learner", "Budgeter", "Planner", "Saver",
                       "Strategist", "Investor", "Optimizer", "Expert", "Finance Master"][level - 1],
        "badges": badges,
        "badges_earned": earned,
        "weekly_challenge": {
            "name": "Spend less than last week",
            "this_week": round(this_week),
            "last_week": round(last_week),
            "on_track": this_week <= last_week if last_week > 0 else this_week == 0,
        },
    }


# ---------- sustainability ----------
def sustainability(expenses: list[Expense]) -> dict:
    months = max(len(_monthly_totals(expenses)), 1)
    by_cat: dict[str, float] = defaultdict(float)
    for e in expenses:
        by_cat[e.category] += e.amount
    rows = []
    total_kg = 0.0
    for cat, amt in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        kg = amt * CARBON_FACTORS.get(cat, 0.005) / months
        total_kg += kg
        rows.append({
            "category": cat,
            "monthly_spend": round(amt / months),
            "monthly_kg_co2": round(kg, 1),
            "tip": ECO_TIPS.get(cat),
        })
    trees = round(total_kg * 12 / 21)  # ~21 kg CO2 absorbed per tree per year
    return {
        "monthly_kg_co2": round(total_kg, 1),
        "yearly_kg_co2": round(total_kg * 12, 1),
        "trees_equivalent_per_year": trees,
        "by_category": rows,
        "summary": (
            f"Your spending drives ~{total_kg:,.0f} kg CO₂e/month "
            f"(≈{trees} trees/yr to offset)." if rows else
            "Add expenses to estimate the carbon footprint of your spending."
        ),
    }
