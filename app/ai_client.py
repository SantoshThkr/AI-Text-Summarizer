import httpx

from app import config


async def generate(messages: list[dict[str, str]]) -> str:
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        # Ollama's default context window is only a few thousand tokens and it
        # silently cuts off longer prompts. 20k characters is about 5k tokens.
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }

    async with httpx.AsyncClient(
        base_url=config.OLLAMA_BASE_URL, timeout=config.OLLAMA_TIMEOUT_SECONDS
    ) as client:
        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()

    return response.json()["message"]["content"]
