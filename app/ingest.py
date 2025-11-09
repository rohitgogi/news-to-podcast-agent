import os
import feedparser
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import json
from datetime import datetime, timezone

load_dotenv()

# load in env variables
NEWS_FEEDS = os.getenv("NEWS_FEEDS", "").split(",")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

def ingest_articles(limit_per_feed: int = 10) -> int:
    """Fetch articles from RSS feeds and store them in the vector DB. Returns count stored."""
    
    
    articles = []
    for url in NEWS_FEEDS:
        url = url.strip()
        if not url:
            continue
        # if url exists, and has no whitespaces get the RSS XML data into a python object
        print(f"Fetching from: {url}")
        feed = feedparser.parse(url)
        print(f"Found {len(feed.entries[:limit_per_feed])} articles")
        
        # only get top (limit_per_feed) artocles
        for entry in feed.entries[:limit_per_feed]:
            articles.append(
                {
                    "title": entry.title,
                    "summary": getattr(entry, "summary", ""),
                    "link": entry.link,
                    "source": url,
                }
            )

    if not articles:
        return 0

    ids = [a["link"] for a in articles]
    docs = [f"{a['title']}\n\n{a['summary']}" for a in articles]
    metas = [{"title": a["title"], "link": a["link"], "source": a["source"]} for a in articles]

    # insert if not existing or replace if it does
    os.makedirs("logs", exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(f"logs/ingest_{today}.json", "w") as f:
        json.dump(articles, f, indent=2)
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    
    print(f"Total stored: {len(articles)} articles across {len(NEWS_FEEDS)} feeds.")
    print("Sample headlines:")
    for a in articles[:5]:
        print(f"  - {a['title']} ({a['source']})")
    return len(articles)

if __name__ == "__main__":
    count = ingest_articles(limit_per_feed=10)
    print(f"Ingested {count} articles.")
