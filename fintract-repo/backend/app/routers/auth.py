"""Authentication endpoints: register, login, profile."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import Token, UserCreate, UserOut, UserUpdate
from ..utils import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name or payload.email.split("@")[0].title(),
        hashed_password=hash_password(payload.password),
        monthly_income=payload.monthly_income,
        risk_tolerance=payload.risk_tolerance,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # New accounts start completely empty (all zeros). Only the shared demo
    # account is pre-filled so the "Try the demo" button shows a populated example.
    if user.email.lower() == "demo@fintract.app":
        from ..seed import seed_user_demo_data
        seed_user_demo_data(db, user)

    write_audit(db, "user.register", user_id=user.id, ip=_client_ip(request))
    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        write_audit(db, "user.login_failed", ip=_client_ip(request), detail=form.username)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    write_audit(db, "user.login", user_id=user.id, ip=_client_ip(request))
    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserOut.model_validate(user))


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
