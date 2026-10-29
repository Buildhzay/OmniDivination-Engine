"""Chạy thử kết nối LLM: python -m app.ai.check"""

import sys

from app.ai.client import LLMNotConfigured, LLMUnavailable, generate_text
from app.config import get_settings


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")

    settings = get_settings()
    print(
        f"Model: {settings.llm_model} | API key configured: "
        f"{bool(settings.gemini_api_key)}"
    )
    try:
        print("Response:", generate_text("Chào bằng đúng một câu tiếng Việt ngắn."))
    except LLMNotConfigured as error:
        print("CONFIGURATION ERROR:", error)
    except LLMUnavailable as error:
        print("LLM ERROR:", error)


if __name__ == "__main__":
    main()
