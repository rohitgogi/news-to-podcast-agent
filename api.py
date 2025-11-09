from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from app.ingest import ingest_articles
from app.reason import generate_podcast_script
from app.speak import text_to_speech
from fastapi.responses import FileResponse

app = FastAPI(
    title="News-to-Podcast API",
    description="Generate an AI-powered daily news podcast.",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Welcome to the News-to-Podcast API"}

@app.get("/generate")
def generate_podcast(
    minutes: int = Query(5, ge=1, le=15),
    topic: str = Query("general", description="Focus area, e.g. technology or politics")
):
    """Run full pipeline: ingest → summarize → synthesize."""
    try:
        article_count = ingest_articles(limit_per_feed=10)
        if article_count == 0:
            return JSONResponse(
                {"error": "No articles found"}, status_code=404
            )

        script = generate_podcast_script(max_minutes=minutes, topic=topic)
        file_path = text_to_speech(script)

        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=file_path.split("/")[-1]
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
