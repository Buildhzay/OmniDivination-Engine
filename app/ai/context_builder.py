"""Chuyển kết quả đã tính thành văn bản gửi cho LLM.

Các hàm chỉ nhận con số và thông tin lá bài, không nhận dữ liệu cá nhân.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

MEANINGS_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "numerology_meanings.json"
)

TOPIC_LABELS = {
    "general": "tự khám phá bản thân nói chung",
    "career": "định hướng sự nghiệp",
}


@lru_cache(maxsize=1)
def _meanings() -> dict[str, dict[str, list[str]]]:
    """Tải từ khóa thần số học một lần từ tệp JSON."""
    with open(MEANINGS_PATH, encoding="utf-8") as file:
        return json.load(file)


def _number_keywords(number: int) -> str:
    table = _meanings()["numbers"]
    if str(number) not in table:
        raise ValueError(f"Không có ý nghĩa cho số {number}")
    return ", ".join(table[str(number)])


def _year_keywords(number: int) -> str:
    table = _meanings()["personal_year"]
    if str(number) not in table:
        raise ValueError(f"Không có ý nghĩa cho năm cá nhân {number}")
    return ", ".join(table[str(number)])


def _topic_label(topic: str) -> str:
    if topic not in TOPIC_LABELS:
        raise ValueError(f"Chủ đề không hợp lệ: {topic}")
    return TOPIC_LABELS[topic]


def build_numerology_context(
    life_path: int,
    personal_year: int,
    target_year: int,
    soul_urge: int | None = None,
    expression: int | None = None,
    topic: str = "general",
) -> str:
    lines = [
        "<du_lieu_tinh_toan>",
        "Loại: Thần số học",
        f"Chủ đề người dùng quan tâm: {_topic_label(topic)}",
        f"- Số chủ đạo: {life_path} (từ khóa: {_number_keywords(life_path)})",
        (
            f"- Năm cá nhân {target_year}: {personal_year} "
            f"(từ khóa: {_year_keywords(personal_year)})"
        ),
    ]
    if soul_urge is not None:
        lines.append(
            f"- Số Linh hồn: {soul_urge} (từ khóa: {_number_keywords(soul_urge)})"
        )
    if expression is not None:
        lines.append(
            f"- Số Sức mạnh: {expression} (từ khóa: {_number_keywords(expression)})"
        )
    lines.append("</du_lieu_tinh_toan>")
    lines.append("Hãy viết phần luận giải theo đúng cấu trúc 4 phần đã quy định.")
    return "\n".join(lines)


def build_tarot_context(cards: list[dict[str, Any]], topic: str = "general") -> str:
    """Tạo ngữ cảnh từ các lá rút được và từ khóa tương ứng."""
    if not cards:
        raise ValueError("Cần ít nhất một lá bài")
    lines = [
        "<du_lieu_tinh_toan>",
        f"Loại: Tarot, {len(cards)} lá (vị trí theo thứ tự rút)",
        f"Chủ đề người dùng quan tâm: {_topic_label(topic)}",
    ]
    for card in cards:
        facing = "ngược" if card["is_reversed"] else "xuôi"
        lines.append(
            f"- Lá {card['position']}: {card['name_vi']} ({facing}), "
            f"từ khóa: {', '.join(card['keywords'])}"
        )
        if card.get("safety_note"):
            lines.append(f"  Ghi chú an toàn: {card['safety_note']}")
    lines.append("</du_lieu_tinh_toan>")
    lines.append("Hãy viết phần luận giải theo đúng cấu trúc 4 phần đã quy định.")
    return "\n".join(lines)
