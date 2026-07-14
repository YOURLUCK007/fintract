"""Expense API tests: seeded data, auto-categorization, CSV import, delete."""
import io


def test_seed_data_present(auth_client):
    r = auth_client.get("/api/expenses?limit=500")
    assert r.status_code == 200
    assert len(r.json()) > 50  # 6 months of demo data seeded on register


def test_add_expense_auto_categorizes(auth_client):
    r = auth_client.post("/api/expenses", json={"description": "swiggy dinner order", "amount": 480})
    assert r.status_code == 201
    assert r.json()["category"] == "Food"


def test_add_expense_explicit_category(auth_client):
    r = auth_client.post("/api/expenses", json={"description": "misc", "amount": 100, "category": "Bills"})
    assert r.json()["category"] == "Bills"


def test_categorize_endpoint(auth_client):
    r = auth_client.post("/api/expenses/categorize", json={"description": "netflix subscription"})
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "Entertainment"
    assert 0 <= body["confidence"] <= 1


def test_csv_import(auth_client):
    csv_data = "date,description,amount\n2026-01-05,Uber ride,300\n2026-01-06,Amazon order,1500\n"
    files = {"file": ("expenses.csv", io.BytesIO(csv_data.encode()), "text/csv")}
    r = auth_client.post("/api/expenses/import", files=files)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_delete_expense(auth_client):
    created = auth_client.post("/api/expenses", json={"description": "temp", "amount": 50, "category": "Others"}).json()
    r = auth_client.delete(f"/api/expenses/{created['id']}")
    assert r.status_code == 204
