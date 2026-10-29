"""Liệt kê model khả dụng cho key của bạn: python -m app.ai.list_models"""

import httpx

from app.config import get_settings


def main() -> None:
    key = get_settings().gemini_api_key
    if not key:
        print("Thiếu GEMINI_API_KEY")
        return
    try:
        response = httpx.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            headers={"x-goog-api-key": key},
            timeout=httpx.Timeout(15.0),
        )
    except httpx.TimeoutException:
        print("HẾT THỜI GIAN CHỜ (15s): máy chủ không trả lời")
        return
    except httpx.HTTPError as error:
        print("LỖI MẠNG:", type(error).__name__)
        return

    print("HTTP", response.status_code)
    if response.status_code == 200:
        for model in response.json().get("models", []):
            name = model.get("name", "").removeprefix("models/")
            if "gemini" in name:
                print(" -", name)
    else:
        print(response.text[:300].replace(key, "[REDACTED]"))


if __name__ == "__main__":
    main()
