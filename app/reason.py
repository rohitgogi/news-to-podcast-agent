import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from app.utils import load_cache, save_cache
import hashlib

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# connect to existing daily collection
chroma_client = chromadb.PersistentClient(path="chroma_db")
print("Step 1: Loading collection...")

# necessary because we need to make sure ingestion and reasoning both use 384 dimention embeddings
embed_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small",
)
collection = chroma_client.get_collection(
    name="news_articles",
    embedding_function=embed_fn,
)

def summarize_article(title, content):
    """Summarize a single article into 2-3 key sentences."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a concise news summarizer."},
            {"role": "user", "content": f"Summarize this article in 2-3 sentences:\n\nTitle: {title}\n\n{content}"}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def generate_podcast_script(max_minutes: int = 5) -> str:
    """Query the vector DB for today's articles and create a spoken script."""

    # chroma searches using semantic phrases so we can just speak to it what we want basically
    query = "Top local Atlanta, Georgia news from the last day, plus major national AND AI tech stories if relevant."

    print("Step 2: Querying Chroma...")
    result = collection.query(query_texts=[query], n_results=15)
    print("Step 2 complete.")

    docs = result["documents"][0]
    metas = result["metadatas"][0]

    print("Step 2b: Ranking articles by semantic relevance...")

    # create an embedding for query
    query_embedding = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    ).data[0].embedding

    # for each doc, compute cosine similarity to query embedding
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # fetch embeddings from chroma or re-embed titles
    ranked = []
    for doc, meta in zip(docs, metas):
        
        # if title already exists in the cache reuse the vector else embed and store
        cache = load_cache()
        cache_key = hashlib.sha256(meta["title"].encode()).hexdigest()
        print(f"Loaded {len(cache)} cached embeddings.")

        if cache_key in cache:
            emb = cache[cache_key]
        else:
            emb = client.embeddings.create(
                input=meta["title"],
                model="text-embedding-3-small"
            ).data[0].embedding
            cache[cache_key] = emb
            save_cache(cache)
            print(f"Cached new embedding for: {meta['title']}")
                
        score = cosine_similarity(query_embedding, emb)
        ranked.append((score, doc, meta))

    # Sort by score and get top 7
    ranked.sort(key=lambda x: x[0], reverse=True)
    ranked = ranked[:7]

    # rebuild docs/metas for summarization
    docs = [r[1] for r in ranked]
    metas = [r[2] for r in ranked]
    
    # build the context for retrieval
    context_blocks = []
    for doc, meta in zip(docs, metas):
        context_blocks.append(
            f"Title: {meta['title']}\nSource: {meta['source']}\n\n{doc}"
        )

    print("Step 3: Summarizing individual articles...")

    # compressed stories
    summaries = []
    for doc, meta in zip(docs, metas):
        summary = summarize_article(meta['title'], doc)
        summaries.append(f"{meta['title']}: {summary}")

    context_text = "\n\n".join(summaries)

    
    context_text = "\n\n---\n\n".join(context_blocks)
    target_words = max_minutes * 130  # we want it to speak slow enough (around 130 words per minute) that we can understand but also we can 2x speed it

    prompt = f"""
You are writing a spoken news script for a short AI-generated podcast. 

Guidelines:
- Focus only on major United States news and technology stories.
- Be factual, clear, and conversational — as if a calm professional narrator is speaking.
- Do NOT include sound cues, stage directions, or brackets like [music] or [transition].
- Use smooth verbal transitions instead of sound effects (e.g., “Moving on to our next story…”).
- Keep sentences short and natural for speech.
- Avoid filler words, opinions, or speculation.
- End with a brief summary or sign-off, no outro music.
- Aim for about {target_words} words (~{max_minutes} minutes of speech).

Context (real articles to summarize):
{context_text}
{context_text}
"""
    # call the LLM with our prompt, low temperature because we want more accurate info and dont care as much about diversity 
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """You are a professional podcast scriptwriter and expert news anchor
            who summarizes important events in a short spoken podcast."""},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    script = completion.choices[0].message.content.strip()
    return script

if __name__ == "__main__":
    script = generate_podcast_script(max_minutes=5)
    print(script)
