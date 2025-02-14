from app.ai_client import generate
from app.prompts import build_messages


async def summarize_text(text: str, length: str) -> str:
    messages = build_messages(text, length)
    summary = await generate(messages)
    return summary.strip()
