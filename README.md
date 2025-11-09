# News-to-Podcast Agent

## Overview
Back in middle school, our teachers made us watch CNN 10 every morning because it was short, simple, and enough to stay informed. Years later, I just stumbled upon it again and realized I’m so behind on current events. I didn’t want to scroll through endless articles or newsletters. I just wanted something short I could listen to on my morning commute/walk news that actually matters to me.

So I built this: an automated pipeline that collects daily U.S. and tech/AI news, summarizes it into a short script, converts it into a podcast, and emails me the MP3 every morning.

---

## Project Plan

### 1. Problem
I wanted a single, low-effort way to stay updated — like a personal version of CNN 10, but powered by AI.

### 2. Pipeline
```
Ingest → Reason → Speak → Deliver → Repeat
```

### 3. Ingest
- Used **RSS feeds** (via `feedparser`) to pull articles from verified U.S. and tech sources.
- This avoids scraping and keeps the data structured.

### 4. Store & Query
- Stored articles in a **Chroma** vector database.
- Used **OpenAI embeddings** for semantic search and retrieval.

### 5. Reason
- Queried the DB for relevant stories (U.S., local, and AI/tech).
- Generated a coherent, conversational script using **GPT-4o-mini**.

### 6. Speak
- Converted the script into natural speech using **OpenAI TTS**.
- Output: a clean, listenable MP3.

### 7. Deliver
- Sent the MP3 automatically through **Gmail SMTP**.

### 8. Automate
- Set up **GitHub Actions** to run the full pipeline daily.

---

## Stack
| Purpose | Tool |
|----------|------|
| Language | Python |
| Data | RSS + Feedparser |
| Database | ChromaDB |
| LLM | GPT-4o-mini |
| TTS | OpenAI TTS |
| API | FastAPI |
| Scheduling | GitHub Actions |
| Delivery | Gmail SMTP |

---

## Setup

```bash
git clone https://github.com/rohitgogi/news-to-podcast-agent.git
cd news-to-podcast-agent
pip install -r requirements.txt
```

Create a `.env` file:
```
OPENAI_API_KEY=your_key
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
RECIPIENT_EMAIL=your_email@gmail.com
```

Run locally:
```bash
python main.py
```

Or start the API:
```bash
uvicorn api:app --reload
```

---

## Future Ideas
- Add voice and tone options for TTS.
- Build a dashboard to replay and manage episodes.
- Personalize based on user preferences or reading history.

---

## Reflection
This started as a personal solution — I wanted to stay informed without wasting time. It turned into a full pipeline that combines ingestion, vector databases, LLM summarization, and automation. It’s a small project, but it forced me to build something end-to-end that actually solves a real problem for myself.
