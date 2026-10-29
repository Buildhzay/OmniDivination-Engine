import pytest

from app.ai.client import LLMNotConfigured, generate_text
from app.config import get_settings


def test_missing_key_gives_none(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert get_settings().gemini_api_key is None


def test_empty_key_treated_as_missing(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert get_settings().gemini_api_key is None


def test_model_can_be_overridden(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "model-test")
    assert get_settings().llm_model == "model-test"


def test_generate_text_without_key_fails_clearly(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(LLMNotConfigured):
        generate_text("xin chào")


def test_api_key_never_appears_in_repr(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-123")
    settings = get_settings()
    assert settings.gemini_api_key == "SECRET-123"
    assert "SECRET-123" not in repr(settings)
    assert "SECRET-123" not in str(settings)


def test_generate_text_returns_text_from_api(monkeypatch):
    from types import SimpleNamespace

    from google import genai

    import app.ai.client as client

    client_options = {}

    class FakeInteractions:
        def create(self, **kwargs):
            client_options["request"] = kwargs
            return SimpleNamespace(output_text="xin chào bạn")

    class FakeClient:
        def __init__(self, *, api_key, http_options):
            client_options["api_key"] = api_key
            client_options["http_options"] = http_options
            self.interactions = FakeInteractions()

    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-123")
    monkeypatch.setattr(genai, "Client", FakeClient)
    assert client.generate_text("hi") == "xin chào bạn"
    assert client_options["request"]["timeout"] == client.REQUEST_TIMEOUT
    assert client_options["http_options"].retry_options.attempts == 0


def test_timeout_becomes_clear_error_without_leaking_key(monkeypatch):
    import httpx

    import app.ai.client as client
    from google.genai._gaos.lib.compat_errors import APITimeoutError

    def fake_call(settings, prompt, system_prompt=None):
        raise APITimeoutError(httpx.Request("POST", "https://example.test"))

    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-123")
    monkeypatch.setattr(client, "_call_api", fake_call)
    with pytest.raises(client.LLMUnavailable) as exc:
        client.generate_text("hi")
    assert "SECRET-123" not in str(exc.value)
    assert "Hết thời gian chờ" in str(exc.value)


def test_provider_error_does_not_leak_details(monkeypatch):
    import httpx

    import app.ai.client as client
    from google.genai._gaos.lib.compat_errors import APIError

    def fake_call(settings, prompt, system_prompt=None):
        raise APIError(
            "internal details SECRET-123",
            httpx.Request("POST", "https://example.test"),
            body={"secret": "SECRET-123"},
        )

    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-123")
    monkeypatch.setattr(client, "_call_api", fake_call)
    with pytest.raises(client.LLMUnavailable) as exc:
        client.generate_text("hi")
    assert "SECRET-123" not in str(exc.value)
    assert "APIError" in str(exc.value)
