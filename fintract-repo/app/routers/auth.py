"""Authentication endpoints: register, login, profile, email verification."""
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..email_service import send_verification_email
from ..models import User
from ..schemas import Token, UserCreate, UserOut, UserUpdate
from ..utils import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DEMO_EMAIL = "demo@fintract.app"
_DEMO_PASSWORD = "demo1234"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    is_demo = payload.email.lower() == _DEMO_EMAIL
    token_value = None if is_demo else secrets.token_urlsafe(32)

    user = User(
        email=payload.email,
        full_name=payload.full_name or payload.email.split("@")[0].title(),
        hashed_password=hash_password(payload.password),
        monthly_income=payload.monthly_income,
        risk_tolerance=payload.risk_tolerance,
        # Demo account is pre-verified; everyone else must click the email link
        is_verified=is_demo,
        verification_token=token_value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if is_demo:
        from ..seed import seed_user_demo_data
        seed_user_demo_data(db, user)
        write_audit(db, "user.register.demo", user_id=user.id, ip=_client_ip(request))
        token = create_access_token(str(user.id))
        return Token(access_token=token, user=UserOut.model_validate(user))

    # Send the verification email
    sent = send_verification_email(user.email, token_value)
    write_audit(db, "user.register", user_id=user.id, ip=_client_ip(request))

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "verification_sent",
            "email": user.email,
            "email_sent": sent,
            # If SMTP is not configured (dev mode), expose the link so developers
            # can click it directly from the API response.
            "dev_verify_url": (
                f"{request.base_url}api/auth/verify/{token_value}"
                if not sent
                else None
            ),
        },
    )


# ─── Verify email ────────────────────────────────────────────────────────────

@router.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired verification link.")

    user.is_verified = True
    user.verification_token = None
    db.commit()
    write_audit(db, "user.verified", user_id=user.id)

    # Redirect to the landing page with a flag so the JS can show a success banner
    return RedirectResponse(url="/?verified=1", status_code=302)


# ─── Resend verification ─────────────────────────────────────────────────────

@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or user.is_verified:
        # Don't leak whether the email exists
        return {"message": "If that account exists and is unverified, a new link has been sent."}

    token_value = secrets.token_urlsafe(32)
    user.verification_token = token_value
    db.commit()
    send_verification_email(user.email, token_value)
    return {"message": "If that account exists and is unverified, a new link has been sent."}


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()

    if not user or not verify_password(form.password, user.hashed_password):
        write_audit(db, "user.login_failed", ip=_client_ip(request), detail=form.username)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in. Check your inbox for the verification link.",
        )

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
