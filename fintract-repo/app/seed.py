"""Demo-data seeding: generates a realistic 6-month transaction history per user."""
from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .models import Asset, Expense, Goal, Liability, Notification, User

# (description, category, typical_amount, monthly_frequency)
_TEMPLATES = [
    ("Swiggy dinner order", "Food", 520, 8),
    ("Zomato lunch", "Food", 340, 6),
    ("BigBasket groceries", "Food", 2600, 3),
    ("Uber ride", "Travel", 380, 6),
    ("Petrol - HP", "Travel", 1500, 2),
    ("Amazon order", "Shopping", 1800, 2),
    ("Myntra apparel", "Shopping", 2600, 1),
    ("Electricity bill", "Bills", 2100, 1),
    ("Mobile recharge", "Bills", 399, 1),
    ("Broadband bill", "Bills", 799, 1),
    ("Netflix subscription", "Entertainment", 649, 1),
    ("Spotify Premium", "Entertainment", 119, 1),
    ("BookMyShow movie", "Entertainment", 500, 1),
    ("Apollo Pharmacy", "Healthcare", 700, 1),
    ("Coursera course", "Education", 1499, 1),
    ("SIP - Nifty index fund", "Investments", 10000, 1),
]

_GOALS = [
    ("Emergency fund", "🛟", 300000, 220000, 15000),
    ("New laptop", "💻", 120000, 48000, 12000),
    ("Goa vacation", "🏖️", 80000, 26000, 8000),
    ("Home down payment", "🏠", 2000000, 540000, 40000),
]

# (name, kind, value)
_ASSETS = [
    ("Savings account", "cash", 185000),
    ("Mutual funds & SIP", "investment", 420000),
    ("Fixed deposit", "cash", 200000),
    ("Gold (SGB)", "gold", 90000),
    ("EPF / retirement", "investment", 310000),
]

# (name, kind, balance, monthly_payment)
_LIABILITIES = [
    ("Home loan", "mortgage", 1800000, 22000),
    ("Car loan", "loan", 260000, 9000),
    ("Credit card outstanding", "credit_card", 34000, 6000),
]


def seed_user_demo_data(db: Session, user: User, months: int = 6) -> None:
    """Populate a new user's account with demo expenses, goals and a notification."""
    if db.query(Expense).filter(Expense.user_id == user.id).first():
        return  # already seeded

    rng = random.Random(user.id)  # deterministic per user
    today = date.today()
    expenses: list[Expense] = []
    for m in range(months):
        month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1) if False else today
        for desc, cat, amt, freq in _TEMPLATES:
            for _ in range(freq):
                day_offset = rng.randint(0, 27) + m * 30
                spent = today - timedelta(days=day_offset)
                jitter = rng.uniform(0.8, 1.25)
                expenses.append(Expense(
                    user_id=user.id,
                    description=desc,
                    amount=round(amt * jitter, 2),
                    category=cat,
                    spent_on=spent,
                    is_recurring=freq == 1 and cat in {"Bills", "Entertainment", "Investments"},
                ))
    # Deliberate anomaly (big outlier) + an exact duplicate pair for the radar.
    expenses.append(Expense(user_id=user.id, description="Myntra apparel", category="Shopping",
                            amount=18999, spent_on=today - timedelta(days=4)))
    expenses.append(Expense(user_id=user.id, description="BookMyShow movie", category="Entertainment",
                            amount=1200, spent_on=today - timedelta(days=2)))
    expenses.append(Expense(user_id=user.id, description="BookMyShow movie", category="Entertainment",
                            amount=1200, spent_on=today - timedelta(days=1)))

    db.add_all(expenses)

    for name, emoji, target, saved, monthly in _GOALS:
        db.add(Goal(user_id=user.id, name=name, emoji=emoji,
                    target_amount=target, saved_amount=saved, monthly_contribution=monthly))

    for name, kind, value in _ASSETS:
        db.add(Asset(user_id=user.id, name=name, kind=kind, value=value))
    for name, kind, balance, monthly_payment in _LIABILITIES:
        db.add(Liability(user_id=user.id, name=name, kind=kind,
                         balance=balance, monthly_payment=monthly_payment))

    db.add(Notification(user_id=user.id, kind="milestone",
                        title="Welcome to FinTract 🎉",
                        body="We seeded 6 months of demo data so you can explore every feature."))
    db.commit()

    # Compute anomaly/duplicate flags on the seeded set.
    from .ml.anomaly import detect_anomalies, detect_duplicates
    all_exp = db.query(Expense).filter(Expense.user_id == user.id).all()
    an = detect_anomalies(all_exp)
    du = detect_duplicates(all_exp)
    for e in all_exp:
        e.is_anomaly = an.get(e.id, False)
        e.is_duplicate = du.get(e.id, False)
    db.commit()
