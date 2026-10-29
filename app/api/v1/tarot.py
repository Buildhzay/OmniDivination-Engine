from fastapi import APIRouter

from app.ai.interpreter import DISCLAIMER, interpret_tarot
from app.api.v1.llm_errors import call_interpreter
from app.engine.tarot import draw_cards, get_card
from app.schemas.tarot import (
    TarotCardOut,
    TarotInterpretRequest,
    TarotInterpretResponse,
    TarotRequest,
    TarotResponse,
)

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
def tarot(req: TarotRequest) -> TarotResponse:
    return _draw(req.count)


@router.post("/tarot/interpret", response_model=TarotInterpretResponse)
def tarot_interpret(req: TarotInterpretRequest) -> TarotInterpretResponse:
    result = _draw(req.count)
    text = call_interpreter(
        interpret_tarot,
        [card.model_dump() for card in result.cards],
        topic=req.topic,
    )
    return TarotInterpretResponse(
        **result.model_dump(),
        interpretation=text,
        disclaimer=DISCLAIMER,
    )
