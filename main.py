import os
from dotenv import load_dotenv
from datetime import datetime

from app.ingest import ingest_articles
from app.reason import generate_podcast_script
from app.speak import text_to_speech
from app.delivery import send_email
import argparse

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Run the news-to-podcast pipeline")
    parser.add_argument("--user", type=str, default="default", help="User feed set (default, rohit, etc.)")
    return parser.parse_args()


def main(user="default"):
    print("DAILY PODCAST PIPELINE")
    print(f"Run started: {datetime.now()}\n")
    print(f"User: {user}")

    print("Step 1: Ingesting latest news...")
    article_count = ingest_articles(limit_per_feed=20, user=user)
    print(f"→ Ingested {article_count} articles.\n")

    if article_count == 0:
        print("No new articles — switching to recap mode.\n")
        recap = True
    else:
        recap = False


    print("Step 2: Generating podcast script...")
    script = generate_podcast_script(max_minutes=10, recap=recap)
    print("→ Script generated successfully.\n")

    print("Step 3: Generating audio file...")
    file_path = text_to_speech(script, user) # capture the returned path

    print("Step 4: Sending email...")
    send_email(file_path, subject=f"{user.title()}'s Daily News Podcast")

    print("\nAll steps complete. Podcast saved in ./output/")

if __name__ == "__main__":
    args = parse_args()
    main(user=args.user)
