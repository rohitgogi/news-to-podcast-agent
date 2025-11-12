import os
import feedparser
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import json
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from datetime import timedelta


load_dotenv()

# load in env variables
NEWS_FEEDS = os.getenv("NEWS_FEEDS", "").split(",")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEEN_PATH = Path("data/seen_articles.json")

# persistent client keeps vectors across runs and not reset after the script is done
chroma_client = chromadb.PersistentClient(path="chroma_db")
embed_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small",
)

# we remove yesterday's news articles
if "news_articles" in [c.name for c in chroma_client.list_collections()]:
    chroma_client.delete_collection("news_articles")

# then create a new one for today
collection = chroma_client.create_collection(
    name="news_articles",
    embedding_function=embed_fn,
)
def load_seen_articles() -> dict:
    """Load the JSON file tracking previously seen articles."""
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SEEN_PATH.exists():
        SEEN_PATH.write_text("{}", encoding="utf-8")
    with SEEN_PATH.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_seen_articles(seen: dict) -> None:
    """Persist the seen-articles map to disk."""
    with SEEN_PATH.open("w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)

def article_hash(title: str, summary: str) -> str:
    """Stable hash for article content (title + summary)."""
    base = (title + summary).encode("utf-8", errors="ignore")
    return hashlib.md5(base).hexdigest()



def load_feeds(user: str = "default"):
    """Load feed URLs from config."""
    with open("feeds/default_feeds.json", "r") as f:
        default_feeds = json.load(f)
    user_feeds_path = "feeds/user_feeds.json"
    if os.path.exists(user_feeds_path):
        with open(user_feeds_path, "r") as f:
            user_feeds = json.load(f)
    else:
        user_feeds = {"default": ["general"]}

    selected_groups = user_feeds.get(user, ["general"])
    urls = []
    for group in selected_groups:
        urls.extend(default_feeds.get(group, []))
    return list(set(urls))


def ingest_articles(limit_per_feed = 20, user="default") -> int:
    """Fetch articles from RSS feeds and store them in the vector DB. Returns count stored."""
    
    seen = load_seen_articles()
    new_articles = []
    now = datetime.utcnow()
    feeds = load_feeds(user)
    articles = []
    for url in feeds:
        url = url.strip()
        if not url:
            continue
        # if url exists, and has no whitespaces get the RSS XML data into a python object
        print(f"Fetching from: {url}")
        feed = feedparser.parse(url)
        print(f"Found {len(feed.entries[:limit_per_feed])} articles")
        
        # only get top (limit_per_feed) artocles
        for entry in feed.entries[:limit_per_feed]:
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            link = getattr(entry, "link", "") or ""
            if not link:
                continue

            content_hash = article_hash(title, summary)

            # 1) Skip if already seen with same content
            if link in seen and seen[link].get("hash") == content_hash:
                continue

            # 2) Optional: skip old articles (older than 36h)
            published_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_dt = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_dt = datetime(*entry.updated_parsed[:6])

            if published_dt and now - published_dt > timedelta(hours=36):
                continue

            # 3) This is a "new enough" or updated article → keep it
            new_articles.append(
                {
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "source": url,
                }
            )

            # 4) Update seen map
            record = seen.get(link, {})
            if "first_seen" not in record:
                record["first_seen"] = now.isoformat()
            record["last_seen"] = now.isoformat()
            record["hash"] = content_hash
            record["source"] = url
            seen[link] = record


    if not articles:
        print("No new articles after dedup/filtering.")
        save_seen_articles(seen)
        return 0

    # Persist updated seen map
    save_seen_articles(seen)

    if not new_articles:
        print("No new articles after dedup/filtering.")
        return 0

    ids = [a["link"] for a in new_articles]
    docs = [f"{a['title']}\n\n{a['summary']}" for a in new_articles]
    metas = [{"title": a["title"], "link": a["link"], "source": a["source"]} for a in new_articles]


    # insert if not existing or replace if it does
    os.makedirs("logs", exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(f"logs/ingest_{today}.json", "w") as f:
        json.dump(new_articles, f, indent=2)
    
    KEYWORDS = ["AI", "artificial intelligence", "machine learning", "technology", "innovation", "US", "America"]

    # keyword filter logic to clear articles irrelevant to our prompt
    filtered_articles = []
    for a in articles:
        text = f"{a['title']} {a['summary']}".lower()
        if any(k.lower() in text for k in KEYWORDS):
            filtered_articles.append(a)

    if not filtered_articles:
        print("No articles matched filter — storing all instead.")
        filtered_articles = articles

    articles = filtered_articles
        
    
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    print(f"Ingested {len(new_articles)} new articles.")
    print(f"Total stored: {len(articles)} articles across {len(NEWS_FEEDS)} feeds.")
    print("Sample headlines:")
    for a in articles[:5]:
        print(f"  - {a['title']} ({a['source']})")
    return len(articles)

if __name__ == "__main__":
    count = ingest_articles(limit_per_feed=10)
    print(f"Ingested {count} articles.")
