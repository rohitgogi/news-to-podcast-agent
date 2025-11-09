import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from app.reason import generate_podcast_script

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

if __name__ == "__main__":
    print("Step 1: Loading collection...")
    script = generate_podcast_script(max_minutes=5)
    print("Step 2: Generating audio...")
    text_to_speech(script)
    print("Done.")
