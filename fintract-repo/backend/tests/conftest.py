"""Pytest fixtures: isolated in-memory DB + authenticated test client."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(monkeypatch):
    # Fresh in-memory SQLite shared across the connection pool.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Point the app's SessionLocal at the test engine (used by seed helpers).
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _register(client, email="t@example.com"):
    r = client.post("/api/auth/register", json={
        "email": email, "password": "secret123",
        "full_name": "Tester", "monthly_income": 95000, "risk_tolerance": 3,
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture()
def auth_client(client):
    """Authenticated client seeded with demo data (most feature tests need data)."""
    _register(client)
    from app import database
    from app.models import User
    from app.seed import seed_user_demo_data
    db = database.SessionLocal()
    try:
        user = db.query(User).filter(User.email == "t@example.com").first()
        seed_user_demo_data(db, user)
    finally:
        db.close()
    return client


@pytest.fixture()
def empty_client(client):
    """Authenticated client with a brand-new, unseeded account (all zeros)."""
    return _register(client, email="empty@example.com")
