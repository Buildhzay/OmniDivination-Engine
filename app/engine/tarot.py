"""Engine Tarot: rút bài ngẫu nhiên có seed, tra cứu lá bài. Không gọi mạng, không gọi AI."""

import json
import random
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any

DECK_PATH = Path(__file__).resolve().parent.parent / "data" / "tarot_cards.json"
DECK_SIZE = 78
MAX_CARDS = 10


@lru_cache(maxsize=1)
def load_deck() -> dict[int, dict[str, Any]]:
    """Đọc bộ bài từ file JSON, trả về dict {id: thông tin lá bài}."""
    with open(DECK_PATH, encoding="utf-8") as file:
        cards = json.load(file)
    return {card["id"]: card for card in cards}


def get_card(card_id: int) -> dict[str, Any]:
    deck = load_deck()
    if card_id not in deck:
        raise ValueError(f"Không có lá bài id={card_id}")
    return deck[card_id]


def draw_cards(count: int = 3, seed: int | None = None) -> dict[str, Any]:
    """Rút `count` lá khác nhau. Cùng seed thì luôn ra cùng kết quả.

    Nếu không truyền seed, hệ thống tự sinh một seed ngẫu nhiên mạnh
    và trả về cùng kết quả để có thể lưu lại, tái hiện sau này.
    """
    if not 1 <= count <= MAX_CARDS:
        raise ValueError(f"count phải từ 1 đến {MAX_CARDS}")
    if seed is None:
        seed = secrets.randbits(63)

    rng = random.Random(seed)
    ids = rng.sample(range(1, DECK_SIZE + 1), count)
    cards = [{"card_id": card_id, "is_reversed": rng.random() < 0.5} for card_id in ids]
    return {"seed": seed, "cards": cards}
