import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
from app.config import settings


def _send_email_sync(msg):
    if not settings.SMTP_HOST:
        return
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def send_email(to_email: str, subject: str, body: str, attachment_path: str = None, attachment_name: str = None):
    msg = MIMEMultipart()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = attachment_name or os.path.basename(attachment_path)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    if not settings.SMTP_HOST:
        print(f"[MOCK] Email to {to_email}: {subject} - attachment: {attachment_path}")
        return

    await asyncio.to_thread(_send_email_sync, msg)


async def send_attestation_email(to_email: str, stagiaire_nom_complet: str, attestation_path: str, attestation_numero: str):
    subject = f"Votre attestation de stage Hutchinson"
    body = f"Bonjour {stagiaire_nom_complet},\n\n"
    body += "Veuillez trouver ci-joint votre attestation de stage.\n\n"
    body += "Cordialement,\n"
    body += "Service des stages - Hutchinson Tunisie"
    filename = f"Attestation_stage_{stagiaire_nom_complet}.pdf"
    await send_email(to_email, subject, body, attestation_path, filename)
