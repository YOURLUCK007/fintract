"""Financial Twin — simulate big life decisions against the user's real finances."""
from __future__ import annotations

from collections import defaultdict

from ..models import Asset, Expense, Liability


def _monthly_spend(expenses: list[Expense]) -> float:
    if not expenses:
        return 0.0
    totals: dict[str, float] = defaultdict(float)
    for e in expenses:
        totals[f"{e.spent_on.year}-{e.spent_on.month:02d}"] += e.amount
    return sum(totals.values()) / max(len(totals), 1)


def _emi(principal: float, annual_rate: float, years: float) -> float:
    n = max(int(years * 12), 1)
    r = annual_rate / 12
    if r <= 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def simulate_twin(
    monthly_income: float,
    expenses: list[Expense],
    assets: list[Asset],
    liabilities: list[Liability],
    scenario: str,
    params: dict,
) -> dict:
    p = params or {}
    spend = _monthly_spend(expenses)
    savings = monthly_income - spend
    liquid = sum(a.value for a in assets if a.kind in ("cash", "investment"))

    if scenario == "buy_car":
        price = float(p.get("price", 800000))
        down = float(p.get("down_payment", price * 0.2))
        rate = float(p.get("rate", 9.5)) / 100
        years = float(p.get("years", 5))
        emi = _emi(max(price - down, 0), rate, years)
        running = float(p.get("running_cost", 6000))
        new_savings = savings - emi - running
        return {
            "headline": f"Buying a ₹{price:,.0f} car",
            "emi": round(emi),
            "monthly_running_cost": round(running),
            "new_monthly_savings": round(new_savings),
            "down_payment_covered": down <= liquid,
            "verdict": "affordable" if new_savings > 0 else "strains your budget",
            "summary": (
                f"EMI ₹{emi:,.0f}/mo + running ₹{running:,.0f}/mo leaves you "
                f"₹{new_savings:,.0f}/mo in savings ({'OK' if new_savings > 0 else 'negative — risky'})."
            ),
        }

    if scenario == "home_loan":
        price = float(p.get("price", 5000000))
        down = float(p.get("down_payment", price * 0.2))
        rate = float(p.get("rate", 8.5)) / 100
        years = float(p.get("years", 20))
        emi = _emi(max(price - down, 0), rate, years)
        total_paid = emi * years * 12 + down
        new_savings = savings - emi
        return {
            "headline": f"₹{price:,.0f} home on a {years:.0f}-yr loan",
            "emi": round(emi),
            "total_paid": round(total_paid),
            "total_interest": round(total_paid - price),
            "new_monthly_savings": round(new_savings),
            "emi_to_income_pct": round(emi / monthly_income * 100, 1) if monthly_income else None,
            "verdict": "healthy" if monthly_income and emi <= monthly_income * 0.4 else "EMI exceeds the safe 40% of income",
            "summary": (
                f"EMI ₹{emi:,.0f}/mo ({emi / monthly_income * 100:.0f}% of income). "
                f"Total interest over the loan: ₹{total_paid - price:,.0f}."
            ) if monthly_income else f"EMI would be ₹{emi:,.0f}/mo.",
        }

    if scenario == "rent_vs_buy":
        price = float(p.get("price", 5000000))
        rent = float(p.get("rent", 20000))
        rate = float(p.get("rate", 8.5)) / 100
        years = float(p.get("years", 20))
        appreciation = float(p.get("appreciation", 5)) / 100
        emi = _emi(price * 0.8, rate, years)
        maintenance = price * 0.01 / 12
        buy_monthly = emi + maintenance
        home_value = price * (1 + appreciation) ** years
        rent_total = rent * 12 * years * 1.05 ** (years / 2)  # rough rent escalation
        buy_net_cost = buy_monthly * 12 * years + price * 0.2 - (home_value - price)
        cheaper = "buying" if buy_net_cost < rent_total else "renting"
        return {
            "headline": "Rent vs Buy",
            "buy_monthly_cost": round(buy_monthly),
            "rent_monthly_cost": round(rent),
            "home_value_after": round(home_value),
            "net_cost_buying": round(buy_net_cost),
            "net_cost_renting": round(rent_total),
            "verdict": f"{cheaper} looks cheaper over {years:.0f} years",
            "summary": (
                f"Over {years:.0f} yrs: buying nets ~₹{buy_net_cost:,.0f} "
                f"(after ₹{home_value - price:,.0f} appreciation) vs renting ~₹{rent_total:,.0f} — {cheaper} wins."
            ),
        }

    if scenario == "job_loss":
        months_runway = round(liquid / spend, 1) if spend > 0 else None
        return {
            "headline": "If I lose my job",
            "liquid_assets": round(liquid),
            "monthly_burn": round(spend),
            "months_runway": months_runway,
            "verdict": (
                "comfortable" if months_runway and months_runway >= 6
                else "build a bigger emergency fund" if months_runway is not None
                else "add expenses & assets to estimate your runway"
            ),
            "summary": (
                f"₹{liquid:,.0f} liquid savings covers ~{months_runway} months of your "
                f"₹{spend:,.0f}/mo spending." if months_runway is not None
                else "No spending history yet — add expenses and assets first."
            ),
        }

    if scenario == "salary_change":
        pct = float(p.get("percent", 20))
        new_income = monthly_income * (1 + pct / 100)
        new_savings = new_income - spend
        return {
            "headline": f"Salary {'+' if pct >= 0 else ''}{pct:.0f}%",
            "new_income": round(new_income),
            "new_monthly_savings": round(new_savings),
            "annual_savings": round(new_savings * 12),
            "summary": f"Income becomes ₹{new_income:,.0f}/mo; savings ₹{new_savings:,.0f}/mo (₹{new_savings * 12:,.0f}/yr).",
        }

    if scenario == "marriage":
        increase = float(p.get("spend_increase_pct", 40))
        partner_income = float(p.get("partner_income", 0))
        new_spend = spend * (1 + increase / 100) + 10000  # base joint-household bump
        new_income = monthly_income + partner_income
        new_savings = new_income - new_spend
        return {
            "headline": "Getting married",
            "new_household_income": round(new_income),
            "new_household_spend": round(new_spend),
            "new_monthly_savings": round(new_savings),
            "summary": (
                f"Joint income ₹{new_income:,.0f}/mo vs spend ₹{new_spend:,.0f}/mo "
                f"→ household savings ₹{new_savings:,.0f}/mo."
            ),
        }

    if scenario == "start_business":
        capital = float(p.get("capital", 500000))
        months_no_income = float(p.get("months_no_income", 12))
        needed = capital + spend * months_no_income
        gap = needed - liquid
        return {
            "headline": "Starting a business",
            "capital_needed": round(capital),
            "runway_needed": round(spend * months_no_income),
            "total_needed": round(needed),
            "liquid_assets": round(liquid),
            "shortfall": round(max(gap, 0)),
            "verdict": "funded" if gap <= 0 else f"save ₹{gap:,.0f} more first",
            "summary": (
                f"You need ₹{needed:,.0f} (capital + {months_no_income:.0f} mo living costs); "
                f"you have ₹{liquid:,.0f} liquid — "
                + ("you're covered." if gap <= 0 else f"₹{gap:,.0f} short.")
            ),
        }

    return {"headline": "Unknown scenario", "summary": "No simulation available for this scenario."}
