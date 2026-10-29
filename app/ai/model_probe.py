"""Thử nhiều model sinh văn bản, mỗi model tối đa 20 giây: python -m app.ai.model_probe"""

import sys
import time

import httpx

from app.config import get_settings

CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]


def probe(key: str, model: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    body = {
        "contents": [
            {"parts": [{"text": "Chào bằng đúng một câu tiếng Việt ngắn."}]}
        ]
    }
    start = time.perf_counter()
    try:
        response = httpx.post(
            url,
            headers={"x-goog-api-key": key},
            json=body,
            timeout=httpx.Timeout(20.0, connect=10.0),
        )
    except httpx.TimeoutException:
        return "HẾT GIỜ (20s)"
    except httpx.HTTPError as error:
        return f"LỖI MẠNG ({type(error).__name__})"

    elapsed = time.perf_counter() - start
    if response.status_code == 200:
        return f"OK trong {elapsed:.1f}s"
    return f"HTTP {response.status_code} trong {elapsed:.1f}s"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

    key = get_settings().gemini_api_key
    if not key:
        print("Thiếu GEMINI_API_KEY")
        return
    for model in CANDIDATES:
        print(f"{model:28} -> {probe(key, model)}", flush=True)


if __name__ == "__main__":
    main()
