import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

def send_email(file_path: str, subject: str = "Your Daily News Podcast") -> None:
    """Send the generated MP3 file as an email attachment."""
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

    if not all([EMAIL_USER, EMAIL_PASS, RECIPIENT_EMAIL]):
        print("[DELIVERY] Missing email credentials in .env — aborting.")
        return

    print(f"[DELIVERY] Sending from {EMAIL_USER} → {RECIPIENT_EMAIL}")

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject

    body = "Here's your automatically generated news podcast for today."
    msg.attach(MIMEText(body, "plain"))

    # Attach the file
    try:
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(file_path)}"
            )
            msg.attach(part)
    except FileNotFoundError:
        print(f"[DELIVERY] Attachment not found: {file_path}")
        return

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("[DELIVERY] Email sent successfully!")
    except Exception as e:
        print(f"[DELIVERY] Failed to send email: {e}")
