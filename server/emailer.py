import os
import smtplib
from email.message import EmailMessage

def send_email_smtp(recipient: str, subject: str, body: str) -> dict:
    # Works with any SMTP (e.g., Gmail App Passwords, Mailgun SMTP)
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "{gmail-username}")
    password = os.getenv("SMTP_PASSWORD", "{gmail-app-password}")
    sender = os.getenv("SMTP_FROM", username)

    if not all([host, port, username, password, sender]):
        return {"ok": False, "error": "SMTP not configured in environment"}

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(username, password)
        s.send_message(msg)

    return {"ok": True}
