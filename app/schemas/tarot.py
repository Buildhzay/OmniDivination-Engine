from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.engine.tarot import MAX_CARDS


class TarotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(default=3, ge=1, le=MAX_CARDS, description="Số lá bài cần rút")


class TarotCardOut(BaseModel):
    position: int
    card_id: int
    name_vi: str
    name_en: str
    is_reversed: bool
    keywords: list[str]
    safety_note: str | None = None


class TarotResponse(BaseModel):
    seed: int
    cards: list[TarotCardOut]


class TarotInterpretRequest(TarotRequest):
    topic: Literal["general", "career"] = Field(
        default="general",
        description="Chủ đề quan tâm",
    )


class TarotInterpretResponse(TarotResponse):
    interpretation: str
    disclaimer: str
