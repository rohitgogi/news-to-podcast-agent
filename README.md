# News-to-Podcast Agent

## Overview
Back in middle school, our teachers made us watch CNN 10 every morning because it was short, simple, and enough to stay informed. Years later, I just stumbled upon it again and realized I’m so behind on current events. I didn’t want to scroll through endless articles or newsletters. I just wanted something short I could listen to on my morning commute/walk news that actually matters to me.

So I built this: an automated pipeline that collects daily U.S. and tech/AI news, summarizes it into a short script, converts it into a podcast, and emails me the MP3 every morning.

## Features & Challenges

### What It Does
This project automatically builds and delivers a daily AI-generated podcast based on the latest U.S. and tech/AI news.  
Every morning it:
1. Pulls live news from trusted RSS feeds (CNN, NPR, Wired, The Verge, BBC, etc.)
2. Embeds and stores them in a vector database for semantic search
3. Generates a summarized, conversational script using GPT-4o-mini
4. Converts that script to natural speech using OpenAI TTS
5. Emails me the MP3 directly through Gmail
6. Repeats the whole process automatically every day through GitHub Actions

It’s basically an AI pipeline that takes the internet’s chaos and turns it into a 5-minute personal audio briefing.

---

### Personalization & Intelligence
I later extended the base project to make it smarter:
- **User Personalization:**  
  Added simple topic-filtering through the FastAPI layer (e.g. `?topic=technology` or `?topic=business`), so i can generate focused episodes.
- **Story Clustering:**  
  Used sentence embeddings + cosine similarity (via scikit-learn) to group related articles into unified topics. This prevents the model from summarizing the same story twice under different headlines.
- **Semantic Retrieval:**  
  Each day’s articles are semantically indexed, not just stored by keyword, allowing the LLM to reason over contextually similar stories.
- **Embedding Caching:**  
  Built an MD5-based cache using `hashlib` so repeated embeddings aren’t recomputed, cutting API calls and latency.
- **API Access:**  
  Built a FastAPI wrapper (`/generate`) so I can trigger the pipeline from a browser or mobile shortcut.
- **Automation:**  
  GitHub Actions runs the full pipeline every morning, including ingestion, reasoning, speech, and email, with no manual steps.
- **Persistent Deduplication:**  
  Integrated `seen_articles.json` to track and skip duplicate stories between runs. Each article is hashed by content, meaning repeated top stories from RSS feeds are automatically filtered out.
- **Recap Mode:**  
  Added fallback behavior for days with no new articles. If nothing fresh appears, the pipeline now auto-generates a recap episode with a spoken intro like “There are no major updates today, here’s a recap of ongoing stories...”.
- **Multi-User Support:**  
  Each user can have their own feeds and topics through `feeds/user_feeds.json`. Running `python main.py --user rohit` or `--user default` builds personalized podcasts and separate MP3 files.
- **Delivery Refactor:**  
  Moved all email delivery logic into a standalone `delivery.py` module to separate responsibilities from `speak.py`, making the codebase cleaner and more modular.
- **Persistent Vector Store:**  
  ChromaDB now remains stable between runs. Ingestion no longer wipes daily collections; new content is appended while old content persists.
- **Automated GitHub Action:**  
  The project now includes a fully working `.github/workflows/daily-podcast.yml` that installs dependencies, runs the pipeline, and uploads the generated MP3 as an artifact every morning at 7 AM ET.

---

### Stack
| Layer | Tool / Library | Why |
|-------|----------------|-----|
| Ingestion | `feedparser`, RSS | Reliable, structured, no scraping |
| Storage | `ChromaDB` | Lightweight, local vector DB |
| Embeddings | `text-embedding-3-small` (OpenAI) | Fast + inexpensive |
| Summarization | `gpt-4o-mini` | Coherent short-form writing |
| Speech | `OpenAI TTS` | High-quality voices with one API client |
| Personalization | `FastAPI` | Simple REST control layer |
| Clustering | `scikit-learn`, `cosine_similarity` | Topic grouping |
| Caching | `hashlib`, JSON | Reduces API costs |
| Delivery | `smtplib` + Gmail App Password | Direct MP3 email |
| Automation | `GitHub Actions` | Fully hands-off daily scheduling |

---

### Key Challenges
**1. Embedding Mismatch**  
Originally, ingestion used OpenAI embeddings and reasoning used SentenceTransformer (`384-dim`).  
This caused a dimensionality error (`got 384 expected 1536`).  
Solved by aligning both to OpenAI embeddings for consistency.

**2. RSS Feed Reliability**  
Some feeds returned zero items or invalid XML.  
Added per-feed logging and fallback sources to keep ingestion consistent.

**3. Rate Limits & Cost Control**  
Hit OpenAI quota limits during early testing.  
Introduced caching and `limit_per_feed` caps to balance cost vs coverage.

**4. Deployment on GitHub Actions**  
Secrets (.env) aren’t automatically passed to Actions.  
Fixed by configuring repository secrets and loading them explicitly via workflow `env:` mapping.

**5. Gmail Rejections from Cloud IPs**  
Gmail flagged some Actions as suspicious.  
Handled by switching to App Passwords and reducing attachment frequency.

**6. Deduplication & Recap System**  
Before, duplicate stories reappeared daily. Integrated persistent deduplication, then added recap fallback logic to handle “no new news” gracefully.

**7. Multi-User Feeds**  
Implemented per-user configuration using `feeds/user_feeds.json`. This allows isolated pipelines (e.g. `default` vs `rohit`) that store and email their own podcasts.

---

### Current Capabilities
- End-to-end automation: from ingestion to delivery  
- Clean FastAPI interface (`/generate?minutes=5&topic=tech`)  
- Automatic clustering and topic summarization  
- Personalized daily podcast emailed as MP3  
- Persistent deduplication and recap mode  
- Multi-user personalization support  
- Fully reproducible, one-click GitHub Action  
- Extensible architecture for dashboards, multi-voice TTS, and custom feeds

---

### Next Steps
- Integrate a lightweight front-end dashboard for playback and history  
- Add voice selection and tone controls for TTS  
- Expand to global news with language-specific models  
- Store listener preferences in SQLite or Supabase for long-term personalization  
- Add failure notifications and runtime analytics to GitHub Actions  

---

## Original Project Plan

### 1. The Goal
I wanted to be able to stay updated on daily news without having to scroll through hundreds of articles or subscribe to ten different newsletters.  
Something short, relevant, and digestible like *CNN 10* for adults.  
So the goal was simple: take the chaos of online news, clean it up, and turn it into something I could just listen to every morning.

### 2. The Concept
The full system runs in five stages:
```
Ingest → Reason → Speak → Deliver → Repeat
```

Each stage handles one part of the process, from collecting raw data to producing a finished podcast episode.

### 3. Ingest
First, I had to figure out how to pull fresh news automatically.  
I found **RSS (Really Simple Syndication)** feeds, structured web data that updates as news outlets post new stories.  
With Python’s `feedparser`, I can easily collect articles from major U.S. and tech/AI sources without scraping HTML or dealing with paywalls.

### 4. Store
Next, I needed a way to store and query that data efficiently.  
I used **Chroma**, a lightweight vector database, because it’s simple and fast enough for this scope.  
Articles are embedded using **OpenAI’s text-embedding-3-small** model so I can later retrieve them semantically rather than by keywords.

### 5. Reason
Once the data is in, the project uses **GPT-4o-mini** to summarize the latest and most relevant stories into a short, coherent script, something you’d actually want to listen to.  
I kept the temperature low to prioritize accuracy and factual tone.

### 6. Speak
Then comes text-to-speech.  
Using **OpenAI TTS**, the script is turned into a clear, human-sounding MP3, kind of like a radio segment.

### 7. Deliver
After the audio is generated, it’s automatically emailed to me through **Gmail SMTP**.  
It’s just a short daily podcast sitting in my inbox, ready to play on my commute.

### 8. Repeat
Finally, the whole pipeline runs every morning using **GitHub Actions**, so it’s fully automated, no manual work needed.

### 9. Why This Tech Stack
I went with OpenAI for everything (embeddings, LLM, TTS) to keep the architecture clean, one API client, consistent models, and fewer points of failure.  
And GitHub Actions made sense for scheduling since I was hosting the repo there anyway.

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

To automate through GitHub Actions:
- Add your secrets under **Settings → Secrets → Actions**
- Push `.github/workflows/daily-podcast.yml`
- Workflow runs daily at **7 AM ET**

---

## Future Ideas
- Add voice and tone options for TTS.
- Build a dashboard to replay and manage episodes.
- Personalize based on user preferences or reading history.
- Multi-voice, emotion-aware podcast generation.
- Optional weekend summary edition.

---

## Reflection
This started as a personal solution, I wanted to stay informed without wasting time. It turned into a full pipeline that combines ingestion, vector databases, LLM summarization, and automation. It’s a small project, but it forced me to build something end-to-end that actually solves a real problem for myself.

Now, it’s stable, autonomous, and extensible, it literally talks to me every morning.
