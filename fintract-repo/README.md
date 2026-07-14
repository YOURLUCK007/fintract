# FinTract — AI-Powered Personal Finance Platform

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOURLUCK007/fintract)

FinTract is a full-stack AI personal finance platform with **18 features** built in.  
One Python server handles everything — API + frontend — zero extra tools needed.

---

## Features

| # | Feature |
|---|---------|
| 1 | 🧾 Smart expense tracking with NLP auto-categorization |
| 2 | 🤖 AI anomaly & duplicate transaction radar |
| 3 | 📈 Savings forecast — conservative / balanced / aggressive |
| 4 | 💼 AI investment advisor with risk-adjusted allocation |
| 5 | 💰 AI budget generator (50/30/20 rule, per-category) |
| 6 | 🧮 Savings & what-if simulator |
| 7 | 📊 Net worth tracker (assets + liabilities) |
| 8 | 🔁 Subscription & recurring payment detector |
| 9 | 🎯 Goal planning with ETA & progress tracking |
| 10 | 🚨 Emergency fund planner (6× monthly spend target) |
| 11 | 🪙 Round-up savings (spare change calculator) |
| 12 | 🧩 Diversification analyzer (Herfindahl score) |
| 13 | 🌱 Carbon footprint of spending |
| 14 | 🎲 Monte Carlo portfolio simulator (500 scenarios) |
| 15 | 🧭 Risk profile questionnaire |
| 16 | 👤 Financial Twin — simulate big life decisions |
| 17 | 🏆 Gamification — badges, points, weekly challenge |
| 18 | 📄 PDF & Excel report export |

---

## Tech stack

- **Backend:** FastAPI + SQLAlchemy + JWT auth + WebSocket notifications
- **ML:** scikit-learn (NLP categorizer, IsolationForest anomaly detection, Monte Carlo, Financial Twin)
- **Frontend:** Zero-build HTML/CSS/JS SPA with Chart.js — dark/light theme
- **Database:** SQLite by default (zero setup) · PostgreSQL via `DATABASE_URL` env var

---

## Quick start

```bash
# Clone and run — that's it
git clone https://github.com/YOURLUCK007/fintract.git
cd fintract
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://localhost:8000** — sign up and explore all 18 features.

## Project structure

```
fintract/
├── app/                  # FastAPI backend
│   ├── routers/          # 15 API routers (expenses, goals, planner, lab, …)
│   ├── ml/               # ML models (categorizer, anomaly, montecarlo, twin, …)
│   ├── main.py           # App entry point — mounts API + serves static/
│   ├── models.py         # SQLAlchemy ORM
│   └── schemas.py        # Pydantic request/response schemas
├── static/               # Frontend SPA (HTML + CSS + JS, no build step)
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── api.js        # All API calls
│       └── app.js        # Full 946-line SPA logic
├── requirements.txt
├── Procfile              # For Render / Railway / Heroku
└── start.sh              # One-command local start
```

## Deploy to Render (free)

Click the **Deploy to Render** button above, or:

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect this repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Done ✅

> **Note:** Uses SQLite by default. Set `DATABASE_URL` to a PostgreSQL URL for production persistence.
