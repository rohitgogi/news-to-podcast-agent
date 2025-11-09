import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

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

def generate_podcast_script(max_minutes: int = 5) -> str:
    """Query the vector DB for today's articles and create a spoken script."""

    # chroma searches using semantic phrases so we can just speak to it what we want basically
    query = "Top local Atlanta, Georgia news from the last day, plus major national AND AI tech stories if relevant."

    print("Step 2: Querying Chroma...")
    result = collection.query(query_texts=[query], n_results=15)
    print("Step 2 complete.")

    docs = result["documents"][0]
    metas = result["metadatas"][0]

    # build the context for retrieval
    context_blocks = []
    for doc, meta in zip(docs, metas):
        context_blocks.append(
            f"Title: {meta['title']}\nSource: {meta['source']}\n\n{doc}"
        )

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
