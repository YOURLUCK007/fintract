"""Stripe payments — subscription checkout, webhooks, and status."""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/payments", tags=["payments"])
logger = logging.getLogger(__name__)


def _get_stripe():
    """Lazy-import stripe so the app starts without it being configured."""
    try:
        import stripe
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe SDK not installed. Run: pip install stripe")
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured on this server.")
    stripe.api_key = settings.stripe_secret_key
    return stripe


# ── Create checkout session ───────────────────────────────────────────────────

@router.post("/create-checkout")
def create_checkout(
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Create a Stripe Checkout session for FinTract Pro.

    Usage on the frontend:
        const { url } = await fetch('/api/payments/create-checkout', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token }
        }).then(r => r.json());
        window.location.href = url;
    """
    if not settings.stripe_pro_price_id:
        raise HTTPException(status_code=503, detail="No Stripe price configured.")

    stripe = _get_stripe()

    # Reuse or create the Stripe customer record
    customer_id = current.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(email=current.email, name=current.full_name)
        customer_id = customer["id"]
        current.stripe_customer_id = customer_id
        db.commit()

    origin = str(request.base_url).rstrip("/")
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{origin}/?payment=success",
        cancel_url=f"{origin}/?payment=cancel",
    )
    return {"url": session.url}


# ── Stripe webhook ────────────────────────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events.

    Register this endpoint in your Stripe dashboard:
        https://dashboard.stripe.com/webhooks
    Point it to: https://your-domain.com/api/payments/webhook
    Subscribe to: customer.subscription.created / updated / deleted
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured.")

    stripe = _get_stripe()
    body = await request.body()

    try:
        event = stripe.Webhook.construct_event(body, stripe_signature, settings.stripe_webhook_secret)
    except Exception as exc:
        logger.error("Stripe webhook signature invalid: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event["type"]
    data_obj = event["data"]["object"]

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        customer_id = data_obj.get("customer")
        is_active = data_obj.get("status") in ("active", "trialing")
        sub_id = data_obj.get("id")
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.stripe_subscription_id = sub_id
            user.is_premium = is_active
            db.commit()
            logger.info("User %s premium=%s via subscription %s", user.email, is_active, sub_id)

    elif event_type == "customer.subscription.deleted":
        customer_id = data_obj.get("customer")
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.is_premium = False
            user.stripe_subscription_id = None
            db.commit()
            logger.info("Subscription cancelled for user %s", user.email)

    return {"received": True}


# ── Subscription status ───────────────────────────────────────────────────────

@router.get("/status")
def subscription_status(current: User = Depends(get_current_user)):
    """Return the current user's subscription status."""
    return {
        "is_premium": current.is_premium,
        "stripe_customer_id": current.stripe_customer_id,
        "stripe_subscription_id": current.stripe_subscription_id,
        "publishable_key": settings.stripe_publishable_key or None,
    }
