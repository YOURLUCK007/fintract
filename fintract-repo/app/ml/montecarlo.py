"""Monte Carlo portfolio simulator with inflation-adjusted outcomes."""
from __future__ import annotations

import numpy as np

# risk 1..5 -> (expected annual return, annual volatility)
RISK_PROFILES = {
    1: (0.06, 0.04),
    2: (0.08, 0.08),
    3: (0.10, 0.12),
    4: (0.12, 0.17),
    5: (0.14, 0.24),
}

INFLATION = 0.06


def run_monte_carlo(
    monthly_investment: float,
    years: int = 10,
    risk: int = 3,
    initial: float = 0.0,
    simulations: int = 500,
) -> dict:
    years = max(1, min(int(years), 40))
    risk = max(1, min(int(risk), 5))
    mu, sigma = RISK_PROFILES[risk]
    months = years * 12
    rng = np.random.default_rng(42)

    monthly_mu = mu / 12
    monthly_sigma = sigma / np.sqrt(12)
    returns = rng.normal(monthly_mu, monthly_sigma, size=(simulations, months))

    balances = np.empty((simulations, months))
    bal = np.full(simulations, float(initial))
    for m in range(months):
        bal = bal * (1 + returns[:, m]) + monthly_investment
        balances[:, m] = bal

    year_idx = np.arange(1, years + 1) * 12 - 1
    yearly = balances[:, year_idx]
    p10 = np.percentile(yearly, 10, axis=0)
    p50 = np.percentile(yearly, 50, axis=0)
    p90 = np.percentile(yearly, 90, axis=0)

    invested = initial + monthly_investment * months
    infl = (1 + INFLATION) ** np.arange(1, years + 1)
    return {
        "risk": risk,
        "expected_annual_return_pct": round(mu * 100, 1),
        "volatility_pct": round(sigma * 100, 1),
        "years": years,
        "total_invested": round(invested),
        "simulations": simulations,
        "yearly": [
            {
                "year": int(y),
                "pessimistic": round(float(p10[i])),
                "median": round(float(p50[i])),
                "optimistic": round(float(p90[i])),
                "median_inflation_adjusted": round(float(p50[i] / infl[i])),
            }
            for i, y in enumerate(range(1, years + 1))
        ],
        "final_median": round(float(p50[-1])),
        "final_median_real": round(float(p50[-1] / infl[-1])),
        "prob_beating_inflation": round(
            float((yearly[:, -1] > invested * infl[-1]).mean() * 100), 1
        ),
        "summary": (
            f"Investing ₹{monthly_investment:,.0f}/mo for {years} yrs at risk {risk}: "
            f"median outcome ₹{p50[-1]:,.0f} "
            f"(₹{p50[-1] / infl[-1]:,.0f} in today's money)."
        ),
    }
