import json

import httpx
import pytest

from app import ai_client, config
from app.ai_client import AIResponseError, AITimeoutError, AIUnavailableError, generate

MESSAGES = [{"role": "user", "content": "Summarize this."}]


@pytest.fixture(autouse=True)
def ollama_settings(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setattr(config, "OLLAMA_MODEL", "test-model")
    monkeypatch.setattr(config, "OLLAMA_TIMEOUT_SECONDS", 30.0)


@pytest.fixture
def fake_ollama(monkeypatch):
    def use(handler):
        real_client = httpx.AsyncClient
        transport = httpx.MockTransport(handler)
        monkeypatch.setattr(
            ai_client.httpx,
            "AsyncClient",
            lambda **kwargs: real_client(transport=transport, **kwargs),
        )

    return use


def chat_response(content):
    return httpx.Response(
        200, json={"message": {"role": "assistant", "content": content}, "done": True}
    )


async def test_generate_sends_chat_request(fake_ollama):
    requests = []

    def handler(request):
        requests.append(request)
        return chat_response("A summary.")

    fake_ollama(handler)

    assert await generate(MESSAGES) == "A summary."

    request = requests[0]
    body = json.loads(request.content)
    assert request.url == "http://ollama.test/api/chat"
    assert body["model"] == "test-model"
    assert body["messages"] == MESSAGES
    assert body["stream"] is False
    assert request.extensions["timeout"]["read"] == 30.0


async def test_connection_error_raises_unavailable(fake_ollama):
    def handler(request):
        raise httpx.ConnectError("Connection refused", request=request)

    fake_ollama(handler)

    with pytest.raises(AIUnavailableError):
        await generate(MESSAGES)


async def test_timeout_raises_timeout_error(fake_ollama):
    def handler(request):
        raise httpx.ReadTimeout("Read timed out", request=request)

    fake_ollama(handler)

    with pytest.raises(AITimeoutError):
        await generate(MESSAGES)


async def test_error_status_raises_unavailable(fake_ollama):
    fake_ollama(lambda request: httpx.Response(404, json={"error": "model not found"}))

    with pytest.raises(AIUnavailableError):
        await generate(MESSAGES)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"unexpected": "shape"}),
        httpx.Response(200, json={"message": {"content": None}}),
    ],
    ids=["not-json", "missing-message", "non-text-content"],
)
async def test_malformed_response_raises_response_error(fake_ollama, response):
    fake_ollama(lambda request: response)

    with pytest.raises(AIResponseError):
        await generate(MESSAGES)


async def test_missing_model_raises_unavailable(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_MODEL", "")

    with pytest.raises(AIUnavailableError, match="OLLAMA_MODEL"):
        await generate(MESSAGES)
