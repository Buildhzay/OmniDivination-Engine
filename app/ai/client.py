"""Lớp mỏng bọc LLM. Mọi nơi khác trong dự án chỉ gọi generate_text()."""

import inspect

import httpx

from app.config import Settings, get_settings

REQUEST_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class LLMNotConfigured(RuntimeError):
    """Thiếu cấu hình, ví dụ chưa có API key."""


class LLMUnavailable(RuntimeError):
    """Gọi LLM thất bại do timeout, lỗi mạng hoặc lỗi từ dịch vụ."""


def _build_call_kwargs(
    create_fn,
    settings: Settings,
    prompt: str,
    system_prompt: str | None,
) -> dict:
    """Tạo tham số tương thích cho SDK, ghép system prompt nếu cần."""
    kwargs = {
        "model": settings.llm_model,
        "input": prompt,
        "timeout": REQUEST_TIMEOUT,
    }
    if system_prompt:
        try:
            parameters = inspect.signature(create_fn).parameters
        except (TypeError, ValueError):
            parameters = {}
        if "system_instruction" in parameters:
            kwargs["system_instruction"] = system_prompt
        else:
            kwargs["input"] = f"{system_prompt}\n\n---\n\n{prompt}"
    return kwargs


def _call_api(
    settings: Settings,
    prompt: str,
    system_prompt: str | None = None,
) -> str:
    """Gọi Gemini thật. Tách riêng để test có thể thay bằng bản giả."""
    from google import genai

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=genai.types.HttpOptions(
            retry_options=genai.types.HttpRetryOptions(attempts=0)
        ),
    )
    create = client.interactions.create
    interaction = create(
        **_build_call_kwargs(create, settings, prompt, system_prompt)
    )
    return interaction.output_text


def generate_text(prompt: str, system_prompt: str | None = None) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise LLMNotConfigured(
            "Chưa có GEMINI_API_KEY. Hãy tạo file .env (xem .env.example)."
        )

    from google.genai.errors import APIError
    from google.genai._gaos.lib.compat_errors import (
        APIError as InteractionAPIError,
        APITimeoutError,
    )

    try:
        return _call_api(settings, prompt, system_prompt)
    except (httpx.TimeoutException, APITimeoutError):
        raise LLMUnavailable(
            "Hết thời gian chờ phản hồi từ LLM. Hãy thử lại sau."
        ) from None
    except (httpx.HTTPError, APIError, InteractionAPIError) as error:
        raise LLMUnavailable(f"Gọi LLM thất bại ({type(error).__name__}).") from None
