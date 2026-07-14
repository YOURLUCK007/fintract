# FinTract — AI-Powered Personal Finance Platform (Front-End Demo)

> Intelligent finance, beautifully simple. Track expenses, forecast savings, score your
> financial health, and get personalized investment recommendations — all in one premium dashboard.

This repository contains a **fully working, zero-build front-end demo** of FinTract, built with
plain **HTML, CSS, and vanilla JavaScript** (charts via Chart.js CDN). It runs instantly in any
browser — no install, no backend required — and showcases the product's UI/UX and feature set
described in the FinTract product brief.

> ⚠️ This is an educational demo. Numbers are representative sample data and all
> recommendations are illustrative, **not guaranteed financial advice**.

---

## ✨ What's included

| Area | Demo capability |
| --- | --- |
| **Landing page** | Hero, animated floating cards, feature grid (12 features), how-it-works, security band |
| **Overview dashboard** | KPIs, income-vs-spend chart, category doughnut, monthly trend, spending heatmap, AI insights, financial health ring (0–100) |
| **Expenses** | Add expense with **NLP auto-categorization**, category filters, transaction table, anomaly & duplicate radar |
| **Savings forecast** | Conservative / Balanced / Aggressive scenarios, 12-month projection with confidence range, cash-flow forecast, ranked recommendations with est. savings |
| **Investments** | Risk-tolerance slider → live re-balanced allocation (polar chart), 10-year growth simulation, allocation detail cards |
| **Goals** | Create goals, auto-computed completion dates & required monthly contributions, progress bars |
| **AI assistant** | Conversational UI with grounded, numeric canned answers to finance questions |
| **Theming** | Dark/light mode (persisted), fully responsive, smooth animations, toast notifications |

---

## 🚀 Run it

No build step. Pick any option:

```bash
# Option 1 — just open the file
open index.html            # macOS
xdg-open index.html        # Linux

# Option 2 — serve locally (recommended; avoids any file:// quirks)
python3 -m http.server 8080
# then visit http://localhost:8080
```

---

## 🗂️ Project structure

```
fintract/
├── index.html            # Landing page + single-page app shell
├── css/
│   └── styles.css        # Design system, theming, layout, animations
├── js/
│   └── app.js            # Routing, charts, NLP categorizer, forecast/invest/goals/chat logic
├── data/
│   └── demo-data.js      # Representative sample dataset (INR)
├── assets/
│   └── sample-expenses.csv  # Example import file
└── README.md
```

---

## 🧠 How the "AI" works in this demo

The demo simulates the ML/AI layer on the client so it runs with no backend:

- **Auto-categorization** — a keyword/regex NLP model (`nlpCategorize`) maps descriptions to
  one of 9 categories (Food, Travel, Shopping, Bills, Healthcare, Entertainment, Education,
  Investments, Others).
- **Anomaly & duplicate detection** — pre-computed examples illustrating spikes, duplicates,
  and price increases.
- **Forecasting** — three scenario models with confidence bands derived from the savings base curve.
- **Investment advisor** — allocation tables keyed by a 1–5 risk score, plus a compounding growth simulation.
- **Chat assistant** — an intent matcher that grounds answers in the demo dataset.

In a production build these would be replaced by real services (see below).

---

## 🏛️ Intended production architecture

This demo represents the front-end of the larger FinTract vision. The full system is designed as:

- **Frontend:** React + Next.js + TypeScript + Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL · **Cache:** Redis
- **ML:** scikit-learn / XGBoost / LightGBM (+ TensorFlow/PyTorch where appropriate) for
  expense prediction, savings prediction, budget forecasting, anomaly detection, cash-flow
  forecasting, and investment suitability scoring
- **Security:** JWT + OAuth, password hashing, encryption at rest, rate limiting, audit logs
- **Ops:** Docker + CI/CD

The folder layout here is intentionally modular so it can grow into that architecture
(e.g. swapping `data/demo-data.js` for live REST API calls).

---

## 📄 License / disclaimer

Educational demonstration project. Not financial advice.
