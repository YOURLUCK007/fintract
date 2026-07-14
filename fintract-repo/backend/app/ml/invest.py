"""Investment advisor: risk-based allocation, suitability score, growth simulation."""
from __future__ import annotations

# Allocation tables keyed by risk tolerance (1 = very safe .. 5 = aggressive).
ALLOCATIONS: dict[int, list[tuple[str, int]]] = {
    1: [("Emergency fund", 30), ("Fixed deposits", 28), ("Govt bonds", 20), ("Gold", 12), ("Index funds", 10)],
    2: [("Emergency fund", 25), ("Fixed deposits", 22), ("Govt bonds", 16), ("Index funds", 18), ("Gold", 10), ("Mutual funds", 9)],
    3: [("Emergency fund", 20), ("Index funds", 24), ("Mutual funds", 18), ("Fixed deposits", 14), ("ETFs", 12), ("Gold", 8), ("Govt bonds", 4)],
    4: [("Index funds", 30), ("ETFs", 22), ("Mutual funds", 20), ("Emergency fund", 12), ("Gold", 8), ("Retirement", 8)],
    5: [("Index funds", 34), ("ETFs", 26), ("Mutual funds", 22), ("Retirement", 10), ("Emergency fund", 8)],
}


def suitability_score(monthly_income: float, savings_rate: float, risk: int) -> int:
    """A 0–100 score for how ready the user is to invest at the chosen risk level."""
    income_factor = min(monthly_income / 100000, 1.0)
    savings_factor = min(savings_rate / 30.0, 1.0)  # savings_rate in %
    risk_alignment = 1 - abs(risk - 3) / 4  # centered profiles score highest on readiness
    score = (0.4 * savings_factor + 0.35 * income_factor + 0.25 * risk_alignment) * 100
    return round(score)


def allocation(risk: int, investable_monthly: float) -> list[dict]:
    risk = max(1, min(5, int(risk)))
    return [
        {"name": name, "percent": pct, "monthly": round(investable_monthly * pct / 100)}
        for name, pct in ALLOCATIONS[risk]
    ]


def growth_simulation(investable_monthly: float, risk: int, years: int = 10) -> dict:
    """Compound an annual contribution at a risk-adjusted rate (illustrative)."""
    rate = 0.05 + max(1, min(5, int(risk))) * 0.015
    annual = investable_monthly * 12
    values, acc = [], 0.0
    for i in range(years + 1):
        if i > 0:
            acc = (acc + annual) * (1 + rate)
        values.append(round(acc))
    return {
        "labels": [f"Y{i}" for i in range(years + 1)],
        "values": values,
        "rate": round(rate * 100, 1),
    }
