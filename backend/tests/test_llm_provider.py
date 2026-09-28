import pytest

from app.config import settings
from app.services.llm_provider import (
    get_llm_provider,
    DummyProvider,
    OpenAICompatibleProvider,
    LLMProviderError,
)


def test_dummy_provider_when_no_api_key_and_no_local_llm(monkeypatch):
    """Sans clé API ET sans LLM local (Ollama) configuré, le fournisseur ne
    fait aucun appel réseau (repli sur DummyProvider)."""
    monkeypatch.setattr(settings, "LLM_API_KEY", "")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
    provider = get_llm_provider()
    assert isinstance(provider, DummyProvider)


def test_ollama_provider_when_no_api_key(monkeypatch):
    """Avec un LLM local Ollama configuré (127.0.0.1:11434), aucune clé API
    n'est nécessaire : le fournisseur OpenAI-compatible est utilisé directement,
    pas le DummyProvider (support Ollama sans clé API)."""
    monkeypatch.setattr(settings, "LLM_API_KEY", "")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setattr(settings, "LLM_MODEL", "qwen3:8b")
    provider = get_llm_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.api_key == ""
    assert provider.model == "qwen3:8b"


@pytest.mark.asyncio
async def test_dummy_provider_returns_empty():
    provider = DummyProvider()
    result = await provider.complete([{"role": "user", "content": "hi"}])
    assert result == ""


@pytest.mark.asyncio
async def test_provider_network_error_raises():
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="http://127.0.0.1:1",
        model="test-model",
        timeout=2,
        temperature=0.0,
    )
    with pytest.raises(LLMProviderError):
        await provider.complete([{"role": "user", "content": "bonjour"}])


@pytest.mark.asyncio
async def test_provider_http_error_raises():
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://httpbin.org/status/500",
        model="test-model",
        timeout=10,
        temperature=0.0,
    )
    with pytest.raises(LLMProviderError):
        await provider.complete([{"role": "user", "content": "bonjour"}])