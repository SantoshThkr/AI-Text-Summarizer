import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.ai_client import AIResponseError, AITimeoutError, AIUnavailableError
from app.schemas import SummarizeRequest, SummarizeResponse
from app.summarizer import summarize_text

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Text Summarizer",
    description="Summarize text with a local LLM running on Ollama.",
    version="0.1.0",
)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/summarize",
    responses={
        502: {"description": "The model returned an empty or invalid response."},
        503: {"description": "Ollama is not reachable or not configured."},
        504: {"description": "Ollama did not respond in time."},
    },
)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    try:
        summary = await summarize_text(request.text, request.length)
    except AITimeoutError as exc:
        logger.warning("Summarization timed out: %s", exc)
        raise HTTPException(
            status_code=504,
            detail="Summarization took too long. Please try again with shorter text.",
        ) from None
    except AIUnavailableError as exc:
        logger.warning("Summarization service unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Summarization service is currently unavailable.",
        ) from None
    except AIResponseError as exc:
        logger.warning("Invalid response from model: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Summarization service returned an invalid response.",
        ) from None

    return SummarizeResponse(summary=summary, length=request.length)
