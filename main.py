import os
from dotenv import load_dotenv
from datetime import datetime

from app.ingest import ingest_articles
from app.reason import generate_podcast_script
from app.speak import text_to_speech, send_email

load_dotenv()

def main():
    print("DAILY PODCAST PIPELINE")
    print(f"Run started: {datetime.now()}\n")

    print("Step 1: Ingesting latest news...")
    article_count = ingest_articles(limit_per_feed=20)
    print(f"→ Ingested {article_count} articles.\n")

    if article_count == 0:
        print("No articles found. Aborting.")
        return

    print("Step 2: Generating podcast script...")
    script = generate_podcast_script(max_minutes=5)
    print("→ Script generated successfully.\n")

    print("Step 3: Generating audio file...")
    file_path = text_to_speech(script)  # capture the returned path

    print("Step 4: Sending email...")
    send_email(file_path)

    print("\nAll steps complete. Podcast saved in ./output/")

if __name__ == "__main__":
    main()
