"""Thử sinh văn bản bằng REST thuần: python -m app.ai.rest_probe"""

import sys

import httpx

from app.config import get_settings


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

    settings = get_settings()
    key = settings.gemini_api_key
    if not key:
        print("Thiếu GEMINI_API_KEY")
        return

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.llm_model}:generateContent"
    )
    body = {
        "contents": [
            {"parts": [{"text": "Chào bằng đúng một câu tiếng Việt ngắn."}]}
        ]
    }
    try:
        response = httpx.post(
            url,
            headers={"x-goog-api-key": key},
            json=body,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    except httpx.TimeoutException:
        print("HẾT THỜI GIAN CHỜ (60s)")
        return
    except httpx.HTTPError as error:
        print("LỖI MẠNG:", type(error).__name__)
        return

    print("Model:", settings.llm_model, "| HTTP", response.status_code)
    if response.status_code == 200:
        try:
            answer = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            print("Trả lời:", answer.replace(key, "[REDACTED]"))
        except (KeyError, IndexError, ValueError):
            print(
                "Phản hồi 200 nhưng cấu trúc lạ:",
                response.text[:300].replace(key, "[REDACTED]"),
            )
    else:
        print(response.text[:300].replace(key, "[REDACTED]"))


if __name__ == "__main__":
    main()
