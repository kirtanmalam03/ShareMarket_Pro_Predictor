import os
import smtplib
from email.message import EmailMessage


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def send_contact_email(*, name: str, email: str, message: str) -> None:
    """
    Sends a contact email using SMTP config from environment variables.

    Free option: Gmail SMTP with an App Password.
    Env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS
      CONTACT_TO_EMAIL (default: nityagohel0109@gmail.com)
      CONTACT_FROM_EMAIL (default: SMTP_USERNAME)
    """
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_use_tls = _bool_env("SMTP_USE_TLS", True)

    to_email = os.getenv("CONTACT_TO_EMAIL", "nityagohel0109@gmail.com").strip()
    from_email = os.getenv("CONTACT_FROM_EMAIL", smtp_username).strip()

    if not smtp_host or not smtp_username or not smtp_password or not from_email:
        raise RuntimeError("Email service is not configured. Please set SMTP_* env vars.")

    msg = EmailMessage()
    msg["Subject"] = f"[Stock Predictor Pro] Contact message from {name}"
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Reply-To"] = email
    msg.set_content(
        "New contact form submission\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n\n"
        "Message:\n"
        f"{message}\n"
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        if smtp_use_tls:
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
