"""Ghép kết quả đã tính, ngữ cảnh an toàn và lời gọi LLM."""

from app.ai.client import generate_text
from app.ai.context_builder import build_numerology_context, build_tarot_context
from app.ai.prompts import SYSTEM_PROMPT

DISCLAIMER = (
    "Nội dung chỉ mang tính giải trí và gợi mở tự suy ngẫm, không phải dự đoán chắc chắn "
    "và không thay thế tư vấn y tế, tài chính hay pháp lý."
)


def interpret_numerology(
    *,
    life_path: int,
    personal_year: int,
    target_year: int,
    soul_urge: int | None = None,
    expression: int | None = None,
    topic: str = "general",
) -> str:
    context = build_numerology_context(
        life_path,
        personal_year,
        target_year,
        soul_urge=soul_urge,
        expression=expression,
        topic=topic,
    )
    return generate_text(context, system_prompt=SYSTEM_PROMPT)


def interpret_tarot(cards: list[dict], topic: str = "general") -> str:
    context = build_tarot_context(cards, topic=topic)
    return generate_text(context, system_prompt=SYSTEM_PROMPT)
