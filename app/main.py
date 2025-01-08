from fastapi import FastAPI

app = FastAPI(
    title="AI Text Summarizer",
    description="Summarize text with a local LLM running on Ollama.",
    version="0.1.0",
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
