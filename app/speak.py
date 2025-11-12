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

if __name__ == "__main__":
    print("[RUN] Generating script...")
    script = generate_podcast_script(max_minutes=5)
    print("[RUN] Converting to audio...")
    mp3_path = text_to_speech(script)
    print(f"[RUN] Saved to {mp3_path}")
