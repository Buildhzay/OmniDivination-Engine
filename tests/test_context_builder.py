import inspect

import pytest

from app.ai import context_builder as cb
from app.ai.prompts import SYSTEM_PROMPT


def test_numerology_context_contains_facts_and_keywords():
    text = cb.build_numerology_context(
        9,
        2,
        2026,
        soul_urge=8,
        expression=7,
        topic="career",
    )
    assert "Số chủ đạo: 9" in text
    assert "Năm cá nhân 2026: 2" in text
    assert "Số Linh hồn: 8" in text
    assert "Số Sức mạnh: 7" in text
    assert "định hướng sự nghiệp" in text
    assert "nhân văn" in text
    assert text.startswith("<du_lieu_tinh_toan>")
    assert "</du_lieu_tinh_toan>" in text


def test_optional_numbers_omitted_when_absent():
    text = cb.build_numerology_context(9, 2, 2026)
    assert "Linh hồn" not in text and "Sức mạnh" not in text


def test_master_numbers_supported():
    for number in (11, 22, 33):
        assert str(number) in cb.build_numerology_context(number, 5, 2026)


def test_builders_cannot_receive_personal_data():
    forbidden = {
        "full_name",
        "name",
        "dob",
        "birth_date",
        "birthday",
        "email",
        "phone",
    }
    for function in (cb.build_numerology_context, cb.build_tarot_context):
        assert not forbidden & set(inspect.signature(function).parameters)


def test_unknown_number_or_topic_rejected():
    with pytest.raises(ValueError):
        cb.build_numerology_context(10, 2, 2026)
    with pytest.raises(ValueError):
        cb.build_numerology_context(9, 11, 2026)
    with pytest.raises(ValueError):
        cb.build_numerology_context(9, 2, 2026, topic="health")


CARDS = [
    {
        "position": 1,
        "name_vi": "Cái Chết",
        "is_reversed": False,
        "keywords": ["kết thúc", "chuyển hóa"],
        "safety_note": "Chỉ là biểu tượng, không phải dự báo cái chết.",
    },
    {
        "position": 2,
        "name_vi": "Mặt Trời",
        "is_reversed": True,
        "keywords": ["vui chậm lại"],
        "safety_note": None,
    },
]


def test_tarot_context_orientation_keywords_and_safety_note():
    text = cb.build_tarot_context(CARDS)
    assert "Lá 1: Cái Chết (xuôi)" in text
    assert "Lá 2: Mặt Trời (ngược)" in text
    assert "Ghi chú an toàn: Chỉ là biểu tượng" in text
    assert text.count("Ghi chú an toàn") == 1


def test_tarot_context_rejects_empty():
    with pytest.raises(ValueError):
        cb.build_tarot_context([])


def test_meanings_cover_every_possible_result():
    from app.engine.numerology import MASTER_NUMBERS

    for number in list(range(1, 10)) + list(MASTER_NUMBERS):
        assert cb._number_keywords(number)
    for number in range(1, 10):
        assert cb._year_keywords(number)


def test_system_prompt_keeps_key_rules():
    for phrase in (
        "không phải dự đoán chắc chắn",
        "<du_lieu_tinh_toan>",
        "chẩn đoán bệnh",
        "đầu tư",
        "đe dọa",
        "Câu hỏi tự suy ngẫm",
    ):
        assert phrase in SYSTEM_PROMPT
