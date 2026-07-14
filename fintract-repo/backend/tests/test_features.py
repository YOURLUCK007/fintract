"""Tests for the high-impact feature set: budget, subscriptions, net worth,
simulator, what-if, and report export."""


def test_new_user_starts_empty(empty_client):
    """A brand-new account has no seeded data — everything starts at zero."""
    ov = empty_client.get("/api/analytics/overview").json()
    assert ov["categories"] == []
    assert all(v == 0 for v in ov["spending"])

    assert empty_client.get("/api/goals").json() == []
    assert empty_client.get("/api/subscriptions").json()["count"] == 0
    nw = empty_client.get("/api/networth").json()
    assert nw["total_assets"] == 0 and nw["total_liabilities"] == 0 and nw["net_worth"] == 0
    assert empty_client.get("/api/budget").json()["current_spend"] == 0


def test_added_values_persist(empty_client):
    """Values a user adds are stored and returned on subsequent requests."""
    empty_client.post("/api/expenses", json={"description": "Coffee", "amount": 200, "category": "Food"})
    empty_client.post("/api/networth/assets", json={"name": "Wallet", "kind": "cash", "value": 5000})

    ov = empty_client.get("/api/analytics/overview").json()
    assert any(c["name"] == "Food" and c["value"] == 200 for c in ov["categories"])
    nw = empty_client.get("/api/networth").json()
    assert nw["total_assets"] == 5000


def test_budget_generator(auth_client):
    r = auth_client.get("/api/budget")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["monthly_income"] > 0
    assert "split" in data and {"needs", "wants", "savings"} <= set(data["split"])
    assert isinstance(data["categories"], list) and data["categories"]
    # recommended never exceeds current for wants over target
    for c in data["categories"]:
        assert set(c) >= {"category", "current", "recommended", "delta", "bucket"}


def test_subscription_detector(auth_client):
    r = auth_client.get("/api/subscriptions")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] >= 1
    assert data["total_monthly"] > 0
    names = " ".join(s["name"].lower() for s in data["subscriptions"])
    # seeded Netflix/Spotify are recurring and should surface
    assert "netflix" in names or "spotify" in names


def test_networth_crud_and_summary(auth_client):
    r = auth_client.get("/api/networth")
    assert r.status_code == 200, r.text
    base = r.json()
    assert base["total_assets"] > 0
    assert len(base["projection"]) == 5

    a = auth_client.post("/api/networth/assets", json={"name": "Crypto", "kind": "investment", "value": 50000})
    assert a.status_code == 201
    aid = a.json()["id"]
    after = auth_client.get("/api/networth").json()
    assert after["total_assets"] == base["total_assets"] + 50000

    d = auth_client.delete(f"/api/networth/assets/{aid}")
    assert d.status_code == 204

    l = auth_client.post("/api/networth/liabilities", json={"name": "Personal loan", "balance": 20000, "monthly_payment": 2000})
    assert l.status_code == 201


def test_savings_simulator(auth_client):
    r = auth_client.post("/api/simulate/savings", json={"adjustments": {"Food": 20, "Shopping": 15}, "extra_investment": 1000})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["monthly_gain"] > 0
    assert len(data["projection_5yr"]) == 5
    assert data["projection_5yr"][-1]["balance"] > data["projection_5yr"][0]["balance"]


def test_whatif_scenarios(auth_client):
    purchase = auth_client.post("/api/simulate/whatif", json={"scenario": "purchase", "params": {"amount": 50000}})
    assert purchase.status_code == 200
    assert "affordable" in purchase.json()

    salary = auth_client.post("/api/simulate/whatif", json={"scenario": "salary_change", "params": {"percent": 20}})
    assert salary.json()["new_income"] > 95000

    infl = auth_client.post("/api/simulate/whatif", json={"scenario": "inflation", "params": {"rate": 6}})
    assert infl.json()["spend_in_5yr"] >= infl.json()["spend_today"]


def test_reports_export(auth_client):
    summary = auth_client.get("/api/reports/summary")
    assert summary.status_code == 200
    assert summary.json()["health_score"] >= 0

    pdf = auth_client.get("/api/reports/export?format=pdf")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"

    xlsx = auth_client.get("/api/reports/export?format=excel")
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"


# ---------- planner features ----------
def test_roundup_and_emergency(auth_client):
    r = auth_client.get("/api/plan/roundup").json()
    assert r["yearly_estimate"] >= 0 and "summary" in r

    e = auth_client.get("/api/plan/emergency").json()
    assert e["target"] > 0 and 0 <= e["progress_pct"] <= 100


def test_diversification(auth_client):
    d = auth_client.get("/api/plan/diversification").json()
    assert d["total"] > 0
    assert abs(sum(row["pct"] for row in d["allocation"]) - 100) < 2


def test_montecarlo(auth_client):
    r = auth_client.post("/api/plan/montecarlo", json={"monthly_investment": 5000, "years": 10, "risk": 3})
    assert r.status_code == 200
    data = r.json()
    assert len(data["yearly"]) == 10
    last = data["yearly"][-1]
    assert last["pessimistic"] <= last["median"] <= last["optimistic"]
    assert last["median_inflation_adjusted"] < last["median"]


def test_financial_twin(auth_client):
    car = auth_client.post("/api/plan/twin", json={"scenario": "buy_car", "params": {"price": 800000}}).json()
    assert car["emi"] > 0

    home = auth_client.post("/api/plan/twin", json={"scenario": "home_loan", "params": {"price": 5000000}}).json()
    assert home["total_interest"] > 0

    loss = auth_client.post("/api/plan/twin", json={"scenario": "job_loss", "params": {}}).json()
    assert "months_runway" in loss

    rvb = auth_client.post("/api/plan/twin", json={"scenario": "rent_vs_buy", "params": {"rent": 20000}}).json()
    assert "verdict" in rvb


def test_gamification_and_sustainability(auth_client):
    g = auth_client.get("/api/plan/gamification").json()
    assert g["level"] >= 1 and any(b["earned"] for b in g["badges"])

    s = auth_client.get("/api/plan/sustainability").json()
    assert s["monthly_kg_co2"] > 0 and s["by_category"]


def test_risk_quiz_updates_profile(auth_client):
    r = auth_client.post("/api/plan/risk-quiz", json={"answers": [5, 5, 4, 5, 5]})
    assert r.status_code == 200
    assert r.json()["risk_tolerance"] == 5
    assert auth_client.get("/api/auth/me").json()["risk_tolerance"] == 5


def test_planner_empty_account_safe(empty_client):
    for path in ("/api/plan/roundup", "/api/plan/emergency", "/api/plan/diversification",
                 "/api/plan/gamification", "/api/plan/sustainability"):
        r = empty_client.get(path)
        assert r.status_code == 200, path
    twin = empty_client.post("/api/plan/twin", json={"scenario": "job_loss", "params": {}})
    assert twin.status_code == 200


def test_excel_import(empty_client):
    import io as _io
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["date", "description", "amount", "category"])
    ws.append(["2026-06-01", "Swiggy dinner", 450, ""])
    ws.append(["2026-06-02", "Uber ride", 220, "Travel"])
    buf = _io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    r = empty_client.post("/api/expenses/import", files={"file": ("import.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    rows = r.json()
    assert len(rows) == 2
    assert any(x["category"] == "Travel" for x in rows)
