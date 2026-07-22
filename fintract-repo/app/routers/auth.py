"""Authentication endpoints: register, login, Google OAuth, profile."""
import secrets

import google.auth.exceptions
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import Token, UserCreate, UserOut, UserUpdate
from ..utils import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DEMO_EMAIL = "demo@fintract.app"
_DEMO_PASSWORD = "demo1234"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token using Google's public keys. No service account needed."""
    try:
        request = google_requests.Request()
        claims = google_id_token.verify_firebase_token(
            id_token, request, audience=settings.firebase_project_id
        )
        return claims
    except (google.auth.exceptions.TransportError, ValueError) as exc:
        raise ValueError(f"Invalid Firebase token: {exc}")


# ─── Firebase web config (served to frontend so API key stays server-side) ────

@router.get("/firebase-config")
def firebase_config():
    return {
        "apiKey": settings.google_api_key,
        "authDomain": settings.firebase_auth_domain,
        "projectId": settings.firebase_project_id,
        "storageBucket": settings.firebase_storage_bucket,
        "messagingSenderId": settings.firebase_messaging_sender_id,
        "appId": settings.firebase_app_id,
    }


# ─── Google sign-in ──────────────────────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    id_token: str


@router.post("/google", response_model=Token)
def google_auth(payload: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    try:
        claims = _verify_firebase_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    email = claims.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="No email returned from Google.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        name = claims.get("name", "") or email.split("@")[0].title()
        user = User(
            email=email,
            full_name=name,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        write_audit(db, "user.register.google", user_id=user.id, ip=_client_ip(request))
    else:
        write_audit(db, "user.login.google", user_id=user.id, ip=_client_ip(request))

    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserOut.model_validate(user))


# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    is_demo = payload.email.lower() == _DEMO_EMAIL

    user = User(
        email=payload.email,
        full_name=payload.full_name or payload.email.split("@")[0].title(),
        hashed_password=hash_password(payload.password),
        monthly_income=payload.monthly_income,
        risk_tolerance=payload.risk_tolerance,
        is_verified=True,
        verification_token=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if is_demo:
        from ..seed import seed_user_demo_data
        seed_user_demo_data(db, user)
        write_audit(db, "user.register.demo", user_id=user.id, ip=_client_ip(request))
    else:
        write_audit(db, "user.register", user_id=user.id, ip=_client_ip(request))

    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserOut.model_validate(user))


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()

    if not user or not verify_password(form.password, user.hashed_password):
        write_audit(db, "user.login_failed", ip=_client_ip(request), detail=form.username)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    write_audit(db, "user.login", user_id=user.id, ip=_client_ip(request))
    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserOut.model_validate(user))


# ─── Profile ─────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current, field, value)
    db.commit()
    db.refresh(current)
    return current
