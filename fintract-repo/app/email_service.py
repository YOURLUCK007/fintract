"""Email delivery — sends transactional emails via SMTP or skips if unconfigured."""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import settings

logger = logging.getLogger(__name__)


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
    """Send a verification email.  Returns True if sent, False if SMTP is not configured."""
    if not settings.smtp_host or not settings.smtp_user:
        logger.warning(
            "SMTP not configured — skipping verification email for %s. "
            "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env",
            to_email,
        )
        return False

    verify_url = f"{settings.app_base_url}/api/auth/verify/{token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your FinTract account"
    msg["From"] = settings.smtp_from_address
    msg["To"] = to_email
    msg.attach(MIMEText(_build_verification_html(verify_url), "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as srv:
            srv.ehlo()
            if settings.smtp_port != 465:
                srv.starttls()
            srv.login(settings.smtp_user, settings.smtp_password)
            srv.sendmail(settings.smtp_from_address, [to_email], msg.as_string())
        logger.info("Verification email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
        return False
