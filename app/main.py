from fastapi import FastAPI

from app.schemas import SummarizeRequest, SummarizeResponse
from app.summarizer import summarize_text

app = FastAPI(
    title="AI Text Summarizer",
    description="Summarize text with a local LLM running on Ollama.",
    version="0.1.0",
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/summarize")
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    summary = await summarize_text(request.text, request.length)
    return SummarizeResponse(summary=summary, length=request.length)
