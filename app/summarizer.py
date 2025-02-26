from app.ai_client import AIResponseError, generate
from app.prompts import build_messages


async def summarize_text(text: str, length: str) -> str:
    messages = build_messages(text, length)
    summary = (await generate(messages)).strip()
    if not summary:
        raise AIResponseError("Ollama returned an empty summary")
    return summary
