"""Unit tests for the ML layer: categorizer, anomaly detection, forecasting, invest."""
from datetime import date, timedelta

from app.ml.categorizer import categorize, train_model
from app.ml.anomaly import detect_anomalies, detect_duplicates
from app.ml.forecast import savings_forecast
from app.ml.invest import allocation, growth_simulation, suitability_score


class FakeExpense:
    def __init__(self, id, desc, amount, category, days_ago=0):
        self.id = id
        self.description = desc
        self.amount = amount
        self.category = category
        self.spent_on = date.today() - timedelta(days=days_ago)


def test_categorizer_known_inputs():
    train_model(save=False)
    assert categorize("swiggy dinner")[0] == "Food"
    assert categorize("uber to airport")[0] == "Travel"
    assert categorize("electricity bill")[0] == "Bills"


def test_anomaly_detects_outlier():
    exps = [FakeExpense(i, "coffee", 300, "Food", i) for i in range(12)]
    exps.append(FakeExpense(99, "tv", 50000, "Shopping", 1))
    flags = detect_anomalies(exps)
    assert flags[99] is True


def test_duplicate_detection():
    exps = [
        FakeExpense(1, "BookMyShow movie", 1200, "Entertainment", 1),
        FakeExpense(2, "BookMyShow movie", 1200, "Entertainment", 1),
        FakeExpense(3, "Rent", 20000, "Bills", 10),
    ]
    flags = detect_duplicates(exps)
    assert flags[1] and flags[2]
    assert flags[3] is False


def test_savings_forecast_shape():
    exps = [FakeExpense(i, "food", 2000, "Food", i * 5) for i in range(30)]
    fc = savings_forecast(95000, exps, "balanced")
    assert len(fc["projection"]) == 12
    assert fc["monthly"] > 0
    assert fc["yearly"] >= fc["monthly"]


def test_plan_ordering():
    exps = [FakeExpense(i, "food", 2000, "Food", i * 5) for i in range(30)]
    cons = savings_forecast(95000, exps, "conservative")["yearly"]
    aggr = savings_forecast(95000, exps, "aggressive")["yearly"]
    assert aggr >= cons


def test_invest_allocation_sums_to_100():
    alloc = allocation(3, 20000)
    assert sum(a["percent"] for a in alloc) == 100


def test_growth_and_suitability():
    g = growth_simulation(20000, 4, years=10)
    assert len(g["values"]) == 11
    assert g["values"][-1] > g["values"][0]
    assert 0 <= suitability_score(95000, 25, 3) <= 100
