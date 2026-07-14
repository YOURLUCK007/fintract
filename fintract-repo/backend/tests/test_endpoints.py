"""Smoke tests for the analytics/forecast/invest/goals/chat endpoints."""


def test_overview(auth_client):
    r = auth_client.get("/api/analytics/overview")
    assert r.status_code == 200
    d = r.json()
    assert len(d["kpis"]) == 4
    assert 0 <= d["health"]["score"] <= 100
    assert len(d["heatmap"]) == 130
    assert d["categories"]


def test_forecast_plans(auth_client):
    for plan in ("conservative", "balanced", "aggressive"):
        r = auth_client.get(f"/api/forecast/savings?plan={plan}")
        assert r.status_code == 200
        assert r.json()["plan"] == plan
    assert auth_client.get("/api/forecast/cashflow").status_code == 200
    assert auth_client.get("/api/forecast/recommendations").json()["recommendations"]


def test_invest(auth_client):
    r = auth_client.get("/api/invest/advice?risk=4")
    d = r.json()
    assert d["risk"] == 4
    assert sum(a["percent"] for a in d["allocation"]) == 100
    assert d["growth"]["values"]


def test_goals_crud(auth_client):
    created = auth_client.post("/api/goals", json={
        "name": "New bike", "target_amount": 120000, "saved_amount": 30000, "monthly_contribution": 10000,
    }).json()
    assert created["percent"] == 25.0
    assert created["eta"]  # computed completion date
    got = auth_client.get("/api/goals").json()
    assert any(g["name"] == "New bike" for g in got)
    assert auth_client.delete(f"/api/goals/{created['id']}").status_code == 204


def test_chat_grounded(auth_client):
    r = auth_client.post("/api/chat", json={"message": "where did I spend the most?"})
    assert r.status_code == 200
    assert "biggest category" in r.json()["reply"].lower()


def test_health_probe(auth_client):
    assert auth_client.get("/health").json()["status"] == "ok"
