from fastapi import APIRouter

from app.engine.tarot import draw_cards, get_card
from app.schemas.tarot import TarotCardOut, TarotRequest, TarotResponse

router = APIRouter()


@router.post("/tarot", response_model=TarotResponse)
def tarot(req: TarotRequest) -> TarotResponse:
    draw = draw_cards(count=req.count)
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
