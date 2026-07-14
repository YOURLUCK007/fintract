"""FinTract FastAPI application entrypoint."""
import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .ml.categorizer import train_model
from .routers import (
    analytics,
    auth,
    budget,
    chat,
    expenses,
    forecast,
    goals,
    invest,
    networth,
    notifications,
    planner,
    reports,
    simulate,
    subscriptions,
    ws,
)
from .utils import rate_limiter

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-powered personal finance platform — expenses, forecasting, investments, and a grounded AI assistant.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip limiting for docs and health probes.
    if request.url.path.startswith(("/docs", "/openapi", "/redoc", "/health")):
        return await call_next(request)
    client = request.client.host if request.client else "anon"
    if not rate_limiter.allow(client):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please slow down."},
        )
    return await call_next(request)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    train_model(save=True)  # ensure categorizer artifact exists


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": app.version}


for r in (auth, expenses, analytics, forecast, invest, goals, notifications, chat,
          budget, subscriptions, networth, simulate, reports, planner, ws):
    app.include_router(r.router)

# Serve the front-end (single-origin deployment). Mounted last so /api and /ws win.
_FRONTEND_DIR = os.getenv(
    "FRONTEND_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static")),
)
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
