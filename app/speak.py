import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from app.reason import generate_podcast_script
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_speech(text: str):
    """Convert text to speech and save as an MP3."""
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("output", exist_ok=True)
    out_path = f"output/podcast_{today}.mp3"

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text,
    ) as response:
        response.stream_to_file(out_path)

    print(f"Podcast saved to {out_path}")
    return out_path

def send_email(file_path: str):
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

    print(f"Attempting to send email from {EMAIL_USER} to {RECIPIENT_EMAIL}")

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = "Your Daily News Podcast"

    body = "Here's your automatically generated news podcast for today."
    msg.attach(MIMEText(body, "plain"))

    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
        msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

    print("Email sent successfully!")
    
if __name__ == "__main__":
    print("Step 1: Loading collection...")
    script = generate_podcast_script(max_minutes=5)
    print("Step 2: Generating audio...")
    text_to_speech(script)
    print("Done.")
