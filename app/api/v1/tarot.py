from fastapi import APIRouter, Header, Request

from app.ai.interpreter import DISCLAIMER, interpret_tarot
from app.api.v1.llm_errors import call_interpreter
from app.api.v1.reading_storage import (
    persist_reading_if_owned,
    resolve_optional_owner,
)
from app.engine.tarot import draw_cards, get_card
from app.schemas.tarot import (
    TarotCardOut,
    TarotInterpretRequest,
    TarotInterpretResponse,
    TarotRequest,
    TarotResponse,
)
from app.rate_limit import limiter

router = APIRouter()


def _draw(count: int) -> TarotResponse:
    draw = draw_cards(count=count)
    cards = []
    for pos, item in enumerate(draw["cards"], start=1):
        info = get_card(item["card_id"])
        cards.append(
            TarotCardOut(
                position=pos,
                card_id=item["card_id"],
                name_vi=info["name_vi"],
                name_en=info["name_en"],
                is_reversed=item["is_reversed"],
                keywords=info["reversed"] if item["is_reversed"] else info["upright"],
                safety_note=info.get("safety_note"),
            )
        )
    return TarotResponse(seed=draw["seed"], cards=cards)


@router.post("/tarot", response_model=TarotResponse)
@limiter.limit("60/minute")
def tarot(
    request: Request,
    req: TarotRequest,
    reading_token: str | None = Header(default=None, alias="X-Reading-Token"),
) -> TarotResponse:
    owner_id = resolve_optional_owner(reading_token)
    result = _draw(req.count)
    persist_reading_if_owned(owner_id, "tarot", result.model_dump(mode="json"))
    return result


@router.post("/tarot/interpret", response_model=TarotInterpretResponse)
@limiter.limit("10/minute")
def tarot_interpret(
    request: Request,
    req: TarotInterpretRequest,
    reading_token: str | None = Header(default=None, alias="X-Reading-Token"),
) -> TarotInterpretResponse:
    owner_id = resolve_optional_owner(reading_token)
    result = _draw(req.count)
    text = call_interpreter(
        interpret_tarot,
        [card.model_dump() for card in result.cards],
        topic=req.topic,
    )
    interpreted = TarotInterpretResponse(
        **result.model_dump(),
        interpretation=text,
        disclaimer=DISCLAIMER,
    )
    persist_reading_if_owned(
        owner_id,
        "tarot",
        interpreted.model_dump(mode="json"),
    )
    return interpreted
