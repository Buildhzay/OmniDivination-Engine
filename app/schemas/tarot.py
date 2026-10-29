from pydantic import BaseModel, Field

from app.engine.tarot import MAX_CARDS


class TarotRequest(BaseModel):
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
