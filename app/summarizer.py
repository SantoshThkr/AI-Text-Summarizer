import httpx

from app import config


async def summarize_text(text: str, length: str) -> str:
    prompt = f"Summarize the following text. Summary length: {length}.\n\n{text}"
    async with httpx.AsyncClient(
        base_url=config.OLLAMA_BASE_URL, timeout=config.OLLAMA_TIMEOUT_SECONDS
    ) as client:
        response = await client.post(
            "/api/generate",
            json={"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
    return response.json()["response"].strip()
