"""Đọc cấu hình từ biến môi trường / file .env. KHÔNG bao giờ in hoặc log API key."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None = field(repr=False)
    llm_model: str
    app_env: str


def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        llm_model=os.getenv("LLM_MODEL", "gemini-3.8-flash"),
        app_env=os.getenv("APP_ENV", "development"),
    )
