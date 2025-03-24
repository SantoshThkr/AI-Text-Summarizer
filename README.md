# AI Text Summarizer

A small FastAPI service that summarizes text with a local LLM running on [Ollama](https://ollama.com).
You send text and a target length (`short`, `medium` or `long`) and get back a summary.

## Why this project exists

I wanted one AI feature built properly rather than a large app built loosely: validated input,
a clear prompt, predictable responses, clean errors when the model is down or slow, and tests
that don't need a model running. Using Ollama keeps it free to run and keeps the text on your machine.

## Features

- `POST /api/summarize` with three summary lengths
- `GET /api/health` for liveness checks (does not call the model)
- Input validation with Pydantic (empty, whitespace-only, too long, invalid length)
- Prompt that treats the input as data, not instructions
- Configurable Ollama URL, model and timeout
- Clean JSON errors for timeouts, unavailable model and bad model output
- Interactive API docs at `/docs` and `/redoc`
- Tests with the AI client mocked, so CI doesn't need Ollama

## Tech stack

- Python 3.12, FastAPI, Uvicorn, Pydantic v2
- httpx for async calls to the Ollama HTTP API
- python-dotenv for configuration
- pytest, pytest-asyncio
- Ruff, Black
- Docker, GitHub Actions

## Architecture

```text
Client
   ↓
FastAPI            app/main.py        routes, error mapping
   ↓
Summarizer         app/summarizer.py  builds prompt, calls model, checks result
   ↓
Prompt Builder     app/prompts.py     system prompt + length instructions
   ↓
Ollama             app/ai_client.py   HTTP call to /api/chat, timeouts, parsing
   ↓
Summary
```

Request and response models live in `app/schemas.py` and settings in `app/config.py`.

## Requirements

- Python 3.12
- Ollama running locally or somewhere reachable over HTTP
- An instruct model pulled in Ollama (for example `llama3.2`)
- Docker (optional)

## Ollama setup

Install Ollama from [ollama.com/download](https://ollama.com/download), then pull a model:

```bash
ollama pull llama3.2
```

Ollama listens on `http://localhost:11434` by default. Check that it's running:

```bash
curl http://localhost:11434/api/tags
```

Any instruct/chat model works. Smaller models like `llama3.2:1b` are faster but follow the
length instructions less reliably. `llama3.2` (3B), `qwen2.5` or `mistral` give better summaries
if you have the memory for them.

You can also run Ollama itself in Docker:

```bash
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
docker exec ollama ollama pull llama3.2
```

## Environment variables

Copy `.env.example` to `.env` and set the model:

```bash
cp .env.example .env
```

| Variable | Default | Description |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is running |
| `OLLAMA_MODEL` | *(empty)* | Model name, e.g. `llama3.2`. Required for `/api/summarize` |
| `MAX_INPUT_LENGTH` | `20000` | Maximum input text length in characters |
| `OLLAMA_TIMEOUT_SECONDS` | `60` | How long to wait for the model before returning 504 |

If `OLLAMA_MODEL` is empty, the API still starts, but `/api/summarize` returns 503.

## Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env   # then set OLLAMA_MODEL
uvicorn app.main:app --reload
```

The API runs on `http://localhost:8000`. Swagger UI is at `http://localhost:8000/docs`.

## Docker setup

Build the image:

```bash
docker build -t ai-text-summarizer .
```

The container runs only the API. Ollama stays on the host (or in its own container), so point
the app at it with `host.docker.internal`:

```bash
docker run --rm -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama3.2 \
  ai-text-summarizer
```

On Linux, add `--add-host=host.docker.internal:host-gateway` to the `docker run` command.

## API usage

### `GET /api/health`

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok"
}
```

### `POST /api/summarize`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `text` | string | yes | 1 to `MAX_INPUT_LENGTH` characters, whitespace-only is rejected |
| `length` | string | no | `short` (1-2 sentences), `medium` (3-5, default), `long` (5-8) |

The sentence counts are instructions to the model, not hard limits.

### Example request

```bash
curl -X POST "http://localhost:8000/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "On Tuesday, the city council of Riverton voted 7 to 2 to approve a $45 million plan to rebuild the Main Street bridge, which was closed in 2023 after inspectors found serious corrosion in its steel supports. Mayor Linda Park said construction will begin in April and is expected to take about 18 months. During that time, a free shuttle bus will connect the east and west sides of the city every 15 minutes.",
    "length": "short"
  }'
```

### Example response

```json
{
  "summary": "The city council of Riverton approved a $45 million plan to rebuild the Main Street bridge, which will begin construction in April and take about 18 months to complete. A free shuttle bus will run every 15 minutes during construction.",
  "length": "short"
}
```

### Errors

| Status | When | Body |
| --- | --- | --- |
| 422 | Invalid request (missing/empty text, too long, bad length) | FastAPI validation details |
| 502 | Model returned an empty or malformed response | `{"detail": "Summarization service returned an invalid response."}` |
| 503 | Ollama is unreachable, the model is missing, or `OLLAMA_MODEL` is not set | `{"detail": "Summarization service is currently unavailable."}` |
| 504 | Ollama didn't answer within `OLLAMA_TIMEOUT_SECONDS` | `{"detail": "Summarization took too long. Please try again with shorter text."}` |

Error responses never include stack traces or internal details. The real cause is written to the server log.

## Testing

```bash
pytest
ruff check .
black --check .
```

The tests don't call a real model. API tests replace the AI client function, and the AI client
tests use `httpx.MockTransport` to simulate Ollama responses, connection errors and timeouts.

GitHub Actions runs Ruff, Black and pytest on every push to `master` and on pull requests.

## Limitations

- Summary quality depends on the model. Small models sometimes ignore the length instruction or add details that aren't in the source text.
- The prompt tells the model to treat input as data, but prompt injection can't be fully prevented. Don't pass the output to anything that trusts it blindly.
- Input is limited by characters, not tokens. The client asks Ollama for an 8192-token context, which fits the default 20,000 characters. If you raise `MAX_INPUT_LENGTH` a lot, Ollama will quietly truncate the input.
- One request is one model call with no streaming, so long texts on slow hardware can hit the timeout.
- No authentication or rate limiting. It's meant to run locally or behind something that handles that.

## Future improvements

Each of these would be a small, separate version:

- V2: bullet-point summaries
- V3: different tones (neutral, casual, formal)
- V4: output language selection
- V5: streaming responses
- V6: TXT/Markdown file input
- V7: summarize a URL
- V8: batch summarization
