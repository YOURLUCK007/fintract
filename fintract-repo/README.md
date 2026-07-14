# FinTract — AI-Powered Personal Finance Platform

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOURLUCK007/fintract)

FinTract is a full-stack, real-time personal finance platform. It automatically
categorizes expenses with machine learning, detects anomalies and duplicate
charges, forecasts savings, scores your financial health, recommends investment
allocations, and answers natural-language questions grounded in **your** data.

- **Backend:** FastAPI + SQLAlchemy, JWT auth, WebSocket real-time notifications
- **ML:** scikit-learn (TF-IDF + Naive Bayes categorizer, IsolationForest anomaly
  detection, linear-regression forecasting, health scoring, recommender, investment suitability)
- **Frontend:** zero-build HTML/CSS/JS SPA, Chart.js visualizations, dark/light themes
- **Data:** SQLite by default (zero setup) or PostgreSQL + Redis via Docker Compose

---

## Quick start (local, zero infrastructure)

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** — the backend serves the frontend on the same
origin. Click **Open Dashboard → Try the demo account** (or create your own).
A new account is automatically seeded with 6 months of demo transactions, goals
and notifications so every feature is populated immediately.

> On first run the app creates `fintract.db` (SQLite) and trains the ML model.

### Run with Docker (PostgreSQL + Redis)

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, and the backend (serving the frontend) at
**http://localhost:8000**.

### Deploy to a permanent free host (Render)

Click the **Deploy to Render** button above (or in Render: **New + → Blueprint →
connect this repo → Apply**). The included `render.yaml` provisions a free web
service + PostgreSQL database and serves the whole app at your Render URL.

---

## Features → where they live

| Feature | Implementation |
|---|---|
| Smart expense tracking + CSV import | `routers/expenses.py`, `ml/categorizer.py` |
| ML/NLP auto-categorization | `ml/categorizer.py` (TF-IDF + MultinomialNB, keyword fallback) |
| Anomaly & duplicate detection | `ml/anomaly.py` (IsolationForest + rules) |
| AI spending analysis & insights | `routers/analytics.py` |
| Saving recommendations | `ml/recommender.py` |
| Savings forecast (3 scenarios) | `ml/forecast.py` (LinearRegression trend) |
| Investment advisor + growth sim | `ml/invest.py` |
| Financial health score (0–100) | `ml/health_score.py` |
| AI chat assistant (grounded) | `routers/chat.py` |
| Goal planning + completion dates | `routers/goals.py` |
| Real-time notifications | `realtime.py`, `routers/ws.py` (WebSocket) |
| AI budget generator (50/30/20, adaptive) | `ml/budget.py`, `routers/budget.py` |
| Savings simulator + what-if scenarios | `ml/simulator.py`, `routers/simulate.py` |
| Net-worth tracker (assets/liabilities + 5-yr projection) | `routers/networth.py`, `models.py` |
| Subscription / recurring-payment detector | `ml/subscriptions.py`, `routers/subscriptions.py` |
| AI-generated reports (PDF + Excel export) | `routers/reports.py` (reportlab + openpyxl) |
| Security (JWT, bcrypt, rate limit, audit) | `auth.py`, `utils.py`, `models.py` |

---

## Architecture

```
fintract/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, rate-limit, static serving
│   │   ├── config.py          # env-driven settings
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # ORM models (DB schema)
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── auth.py            # JWT, bcrypt, current-user dependency
│   │   ├── utils.py           # audit log + rate limiter
│   │   ├── realtime.py        # WebSocket connection manager
│   │   ├── seed.py            # per-user demo-data seeding
│   │   ├── ml/                # categorizer, anomaly, forecast, health, recommender, invest
│   │   └── routers/           # auth, expenses, analytics, forecast, invest, goals, chat, notifications, ws
│   ├── tests/                 # pytest suite (auth, expenses, ML, endpoints)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # HTML/CSS/JS SPA (served by the backend)
│   ├── index.html
│   ├── css/styles.css
│   └── js/{api.js, app.js}
├── sample_data/               # sample CSV for the import feature
├── docker-compose.yml         # postgres + redis + backend
└── .env.example
```

### Request flow

```
Browser (frontend/js/app.js)
   │  fetch + JWT bearer token          WebSocket /ws?token=…
   ▼                                          ▼
FastAPI routers ──► SQLAlchemy (SQLite/Postgres)
   │                                          ▲
   └──► app/ml/* (scikit-learn models) ───────┘  (notifications pushed live)
```

---

## API overview

All `/api/*` routes except register/login require `Authorization: Bearer <token>`.
Interactive docs at **http://localhost:8000/docs**.

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account (auto-seeds demo data) |
| POST | `/api/auth/login` | OAuth2 password login → JWT |
| GET | `/api/analytics/overview` | KPIs, charts, health, insights, heatmap |
| GET | `/api/analytics/anomalies` | Anomaly & duplicate radar |
| GET/POST/DELETE | `/api/expenses` | List / add (ML-categorized) / delete |
| POST | `/api/expenses/import` | Import CSV / bank statement |
| POST | `/api/expenses/categorize` | Live ML category prediction |
| GET | `/api/forecast/savings?plan=` | Savings projection (conservative/balanced/aggressive) |
| GET | `/api/forecast/cashflow` | Cash-flow forecast |
| GET | `/api/forecast/recommendations` | Personalized saving tips |
| GET | `/api/invest/advice?risk=` | Allocation, suitability, growth sim |
| GET/POST/DELETE | `/api/goals` | Goal CRUD with completion dates |
| POST | `/api/chat` | Grounded AI assistant |
| GET | `/api/notifications` | Notification history |
| WS | `/ws?token=` | Real-time notification stream |

---

## Machine learning

- **Categorizer** — TF-IDF (1–2 grams) + Multinomial Naive Bayes trained on an
  in-repo labeled corpus (`ml/dataset.py`), with a deterministic keyword fallback
  for low-confidence predictions. Retrain: `python -m app.ml.train`.
- **Anomaly detection** — IsolationForest over log-scaled amounts flags outlier
  spends; a rule-based pass flags near-identical duplicate charges.
- **Forecasting** — LinearRegression fits the spend trend over rolling 30-day
  windows and projects 12 months with confidence bands and scenario factors.
- **Health score** — weighted 6-dimension score (savings ratio, discipline,
  investing, emergency fund, debt, budget adherence).
- **Investment suitability** — score from income, savings rate and risk alignment.

Run the ML/unit tests:

```bash
cd backend && source .venv/bin/activate && pytest
```

---

## Security

- Passwords hashed with **bcrypt** (`passlib`).
- **JWT** access tokens (`python-jose`), configurable expiry.
- **Rate limiting** middleware (sliding window per client IP).
- **Audit logs** for auth events (`audit_logs` table).
- Per-user data isolation on every query.

## Deployment notes

- Set a strong `SECRET_KEY` and a managed `DATABASE_URL` (PostgreSQL) in production.
- Put the app behind TLS (the WebSocket auto-upgrades to `wss://` on HTTPS).
- Scale horizontally by pointing `REDIS_URL` at a shared Redis for rate limiting.

## Disclaimer

Educational project. Investment allocations and simulations are illustrative and
**not** guaranteed financial advice.
