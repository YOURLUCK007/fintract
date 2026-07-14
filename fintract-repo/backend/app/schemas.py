"""Pydantic request/response schemas."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str = ""
    monthly_income: float = 95000.0
    risk_tolerance: int = Field(default=3, ge=1, le=5)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    monthly_income: float
    risk_tolerance: int
    currency: str
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = None
    monthly_income: float | None = None
    risk_tolerance: int | None = Field(default=None, ge=1, le=5)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- expenses ----------
class ExpenseCreate(BaseModel):
    description: str
    amount: float = Field(gt=0)
    category: str | None = None  # None/"auto" -> ML categorizes
    spent_on: date | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    description: str
    amount: float
    category: str
    spent_on: date
    is_recurring: bool
    is_anomaly: bool
    is_duplicate: bool


class CategorizeRequest(BaseModel):
    description: str


class CategorizeResponse(BaseModel):
    description: str
    category: str
    confidence: float


# ---------- goals ----------
class GoalCreate(BaseModel):
    name: str
    emoji: str = "🎯"
    target_amount: float = Field(gt=0)
    saved_amount: float = 0.0
    monthly_contribution: float = Field(default=0.0, ge=0)


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    emoji: str
    target_amount: float
    saved_amount: float
    monthly_contribution: float
    percent: float = 0.0
    months_left: int = 0
    eta: str = ""


# ---------- net worth ----------
class AssetCreate(BaseModel):
    name: str
    kind: str = "cash"
    value: float = Field(ge=0)


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    kind: str
    value: float


class LiabilityCreate(BaseModel):
    name: str
    kind: str = "loan"
    balance: float = Field(ge=0)
    monthly_payment: float = Field(default=0.0, ge=0)


class LiabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    kind: str
    balance: float
    monthly_payment: float


# ---------- simulator ----------
class SavingsSimRequest(BaseModel):
    adjustments: dict[str, float] = {}  # category -> percent reduction
    extra_investment: float = Field(default=0.0, ge=0)


class WhatIfRequest(BaseModel):
    scenario: str  # extra_savings|purchase|salary_change|loan_prepay|inflation
    params: dict = {}


# ---------- chat ----------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ---------- planner ----------
class MonteCarloRequest(BaseModel):
    monthly_investment: float = Field(default=5000, ge=0)
    years: int = Field(default=10, ge=1, le=40)
    risk: int | None = Field(default=None, ge=1, le=5)
    initial: float = Field(default=0.0, ge=0)


class TwinRequest(BaseModel):
    scenario: str  # buy_car|home_loan|rent_vs_buy|job_loss|salary_change|marriage|start_business
    params: dict = {}


class RiskQuizRequest(BaseModel):
    answers: list[int] = []


# ---------- notifications ----------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    title: str
    body: str
    is_read: bool
    created_at: datetime
