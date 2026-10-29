"""Ghép: kết quả đã tính -> ngữ cảnh an toàn -> LLM -> bộ lọc đầu ra.
Không nhận họ tên hay ngày sinh."""

import logging
from collections.abc import Callable

from app.ai.client import generate_text
from app.ai.context_builder import build_numerology_context, build_tarot_context
from app.ai.prompts import SYSTEM_PROMPT
from app.safety.output_filter import (
    OutputRejected,
    check_numerology_output,
    check_tarot_output,
)

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "Nội dung chỉ mang tính giải trí và gợi mở tự suy ngẫm, không phải dự đoán chắc chắn "
    "và không thay thế tư vấn y tế, tài chính hay pháp lý."
)

MAX_ATTEMPTS = 2  # 1 lần đầu + 1 lần thử lại
RETRY_NOTE = (
    "\n\nLưu ý: bản trước chưa đạt kiểm tra. Chỉ dùng đúng các con số và lá bài đã cho, "
    "giữ giọng gợi mở, tránh khẳng định tuyệt đối."
)


def _generate_checked(context: str, check: Callable[[str], list[str]]) -> str:
    problems: list[str] = []
    for attempt in range(MAX_ATTEMPTS):
        prompt = context if attempt == 0 else context + RETRY_NOTE
        text = generate_text(prompt, system_prompt=SYSTEM_PROMPT)
        problems = check(text)
        if not problems:
            return text
        logger.warning("Đầu ra AI bị từ chối (lần %d): %s", attempt + 1, problems)
    raise OutputRejected("; ".join(problems))


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
    return _generate_checked(
        context,
        lambda text: check_numerology_output(
            text,
            life_path=life_path,
            personal_year=personal_year,
            soul_urge=soul_urge,
            expression=expression,
        ),
    )


def interpret_tarot(cards: list[dict], topic: str = "general") -> str:
    context = build_tarot_context(cards, topic=topic)
    drawn_names = [card["name_vi"] for card in cards]
    return _generate_checked(context, lambda text: check_tarot_output(text, drawn_names))
