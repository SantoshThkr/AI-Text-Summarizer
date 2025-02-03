from app.ai_client import generate


async def summarize_text(text: str, length: str) -> str:
    messages = [
        {"role": "system", "content": "You are a text summarization assistant."},
        {"role": "user", "content": f"Summarize this text ({length}):\n\n{text}"},
    ]
    summary = await generate(messages)
    return summary.strip()
