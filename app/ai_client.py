import httpx

from app import config


class AIClientError(Exception):
    pass


class AIUnavailableError(AIClientError):
    pass


class AITimeoutError(AIClientError):
    pass


class AIResponseError(AIClientError):
    pass


async def generate(messages: list[dict[str, str]]) -> str:
    if not config.OLLAMA_MODEL:
        raise AIUnavailableError("OLLAMA_MODEL is not set")

    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        # Ollama's default context window is only a few thousand tokens and it
        # silently cuts off longer prompts. 20k characters is about 5k tokens.
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    # Ollama sends nothing until generation is finished, so the read timeout
    # effectively limits the whole request. Connecting should be quick.
    timeout = httpx.Timeout(config.OLLAMA_TIMEOUT_SECONDS, connect=5.0)

    try:
        async with httpx.AsyncClient(
            base_url=config.OLLAMA_BASE_URL, timeout=timeout
        ) as client:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise AITimeoutError("Ollama request timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise AIUnavailableError(
            f"Ollama returned {exc.response.status_code}: {exc.response.text[:200]}"
        ) from exc
    except httpx.HTTPError as exc:
        raise AIUnavailableError(f"Could not reach Ollama: {exc!r}") from exc

    try:
        content = response.json()["message"]["content"]
    except (ValueError, KeyError, TypeError) as exc:
        raise AIResponseError("Unexpected response format from Ollama") from exc

    if not isinstance(content, str):
        raise AIResponseError("Ollama response content is not text")
    return content
