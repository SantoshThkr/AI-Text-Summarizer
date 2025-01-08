# AI Text Summarizer

A small FastAPI service that summarizes text with a local LLM running on Ollama.

## Run locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
uvicorn app.main:app --reload
```
