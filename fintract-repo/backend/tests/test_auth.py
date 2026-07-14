"""Auth flow tests: register, duplicate email, login, protected route."""


def test_register_and_me(client):
    r = client.post("/api/auth/register", json={"email": "a@b.com", "password": "pw123456"})
    assert r.status_code == 201
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@b.com"


def test_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"email": "dup@b.com", "password": "pw123456"})
    r = client.post("/api/auth/register", json={"email": "dup@b.com", "password": "pw123456"})
    assert r.status_code == 400


def test_login_success_and_failure(client):
    client.post("/api/auth/register", json={"email": "l@b.com", "password": "pw123456"})
    ok = client.post("/api/auth/login", data={"username": "l@b.com", "password": "pw123456"})
    assert ok.status_code == 200
    assert "access_token" in ok.json()
    bad = client.post("/api/auth/login", data={"username": "l@b.com", "password": "wrong"})
    assert bad.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/analytics/overview").status_code == 401
