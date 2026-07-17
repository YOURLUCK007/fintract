"""SQLAlchemy engine, session factory and declarative base."""
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

import logging
logger = logging.getLogger(__name__)


def _normalize_db_url(url: str) -> str:
    """Normalize managed-host URLs (Render/Railway/Heroku) to a psycopg2 driver."""
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalize_db_url(settings.database_url)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_NEW_USER_COLUMNS = [
    # Use FALSE/TRUE (not 0/1) — works in both SQLite ≥3.23 and PostgreSQL.
    ("is_verified",            "BOOLEAN DEFAULT FALSE"),
    ("verification_token",     "VARCHAR(64)"),
    ("stripe_customer_id",     "VARCHAR(64)"),
    ("stripe_subscription_id", "VARCHAR(64)"),
    ("is_premium",             "BOOLEAN DEFAULT FALSE"),
]


def _migrate_users_table() -> None:
    """Add any missing columns to the users table (safe to run on every startup)."""
    with engine.connect() as conn:
        for col_name, col_def in _NEW_USER_COLUMNS:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                conn.commit()
                logger.info("Migration: added column users.%s", col_name)
            except Exception as exc:
                # Column already exists (or another benign duplicate error) — ignore.
                logger.debug("Migration skip users.%s: %s", col_name, exc)
                conn.rollback()


def _trust_preexisting_users() -> None:
    """Auto-verify accounts that existed before the verification system was added.

    Pre-existing rows have verification_token = NULL (no default was set) AND
    is_verified = FALSE (set by the DEFAULT FALSE migration).  New unverified
    accounts always have a non-NULL token, so this UPDATE only touches the old rows.
    Safe to run on every startup — once a row is set to TRUE it stays TRUE.
    """
    with engine.connect() as conn:
        try:
            result = conn.execute(
                text("UPDATE users SET is_verified = TRUE WHERE verification_token IS NULL AND is_verified = FALSE")
            )
            conn.commit()
            if result.rowcount:
                logger.info("Migration: auto-verified %d pre-existing user(s)", result.rowcount)
        except Exception as exc:
            logger.warning("Migration: could not auto-verify pre-existing users: %s", exc)
            conn.rollback()


def init_db() -> None:
    """Create all tables and apply lightweight column migrations."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_users_table()
    _trust_preexisting_users()
