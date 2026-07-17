"""Email delivery via Brevo (formerly Sendinblue) HTTP API.

Free plan: 300 emails/day, no domain ownership required — just verify
your sender email address at app.brevo.com → Senders & IP → Senders.

Sign up free at https://brevo.com, then:
  1. Add & verify your sender email under Senders & IP → Senders
  2. Create an API key under profile menu → SMTP & API → API Keys
  3. Set BREVO_API_KEY and BREVO_FROM_EMAIL in your environment.
"""
import logging
import httpx

from .config import settings

logger = logging.getLogger(__name__)

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def _build_verification_html(verify_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <style>
    body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #0d0f1a; color: #e2e8f0; margin: 0; padding: 40px 20px; }}
    .card {{ max-width: 540px; margin: 0 auto; background: #161827; border-radius: 16px; padding: 40px; border: 1px solid #2d3154; }}
    .logo {{ font-size: 24px; font-weight: 800; color: #6c8cff; margin-bottom: 24px; }}
    h2 {{ font-size: 22px; margin: 0 0 12px; }}
    p  {{ color: #a0aec0; line-height: 1.6; margin: 0 0 24px; }}
    .btn {{ display: inline-block; background: linear-gradient(135deg, #6c8cff, #8a6bff);
            color: #fff; text-decoration: none; padding: 14px 32px; border-radius: 10px;
            font-weight: 700; font-size: 16px; }}
    .footer {{ margin-top: 32px; font-size: 12px; color: #4a5568; }}
    .url {{ word-break: break-all; color: #6c8cff; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">FinTract</div>
    <h2>Verify your email address</h2>
    <p>You're one step away from your AI-powered finance dashboard. Click the button below to verify your email and activate your account.</p>
    <a href="{verify_url}" class="btn">Verify my account →</a>
    <div class="footer">
      <p>If you didn't create a FinTract account, you can safely ignore this email.</p>
      <p>Link not working? Copy and paste this URL into your browser:<br/>
      <span class="url">{verify_url}</span></p>
    </div>
  </div>
</body>
</html>"""


def send_verification_email(to_email: str, token: str) -> bool:
    """Send a verification email via Brevo. Returns True on success, False otherwise."""
    if not settings.brevo_api_key:
        logger.warning(
            "BREVO_API_KEY not set — skipping email for %s. "
            "Sign up free at brevo.com and set BREVO_API_KEY to enable emails.",
            to_email,
        )
        return False

    verify_url = f"{settings.app_base_url}/api/auth/verify/{token}"

    payload = {
        "sender": {
            "name": "FinTract",
            "email": settings.brevo_from_email,
        },
        "to": [{"email": to_email}],
        "subject": "Verify your FinTract account",
        "htmlContent": _build_verification_html(verify_url),
    }

    try:
        response = httpx.post(
            BREVO_SEND_URL,
            headers={
                "accept": "application/json",
                "api-key": settings.brevo_api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        if response.status_code in (200, 201):
            logger.info("Verification email sent to %s (Brevo)", to_email)
            return True
        else:
            logger.error(
                "Brevo API error %s sending to %s: %s",
                response.status_code, to_email, response.text,
            )
            return False
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
        return False
