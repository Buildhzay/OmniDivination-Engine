import inspect

import pytest

import app.ai.client as client
from app.ai import interpreter
from app.ai.prompts import SYSTEM_PROMPT
from app.config import get_settings
from app.safety.output_filter import OutputRejected


@pytest.fixture
def fake_llm(monkeypatch):
    calls = []

    def fake(prompt, system_prompt=None):
        calls.append({"prompt": prompt, "system_prompt": system_prompt})
        return "Bản luận giải thử."

    monkeypatch.setattr(interpreter, "generate_text", fake)
    return calls


def test_interpret_numerology_sends_context_and_system_prompt(fake_llm):
    text = interpreter.interpret_numerology(
        life_path=9,
        personal_year=2,
        target_year=2026,
        soul_urge=8,
        expression=7,
        topic="career",
    )
    assert text == "Bản luận giải thử."
    assert fake_llm[0]["system_prompt"] == SYSTEM_PROMPT
    assert "Số chủ đạo: 9" in fake_llm[0]["prompt"]


def test_interpret_tarot_sends_card_facts(fake_llm):
    cards = [
        {
            "position": 1,
            "name_vi": "Mặt Trời",
            "is_reversed": False,
            "keywords": ["niềm vui"],
            "safety_note": None,
        }
    ]
    interpreter.interpret_tarot(cards)
    assert "Mặt Trời (xuôi)" in fake_llm[0]["prompt"]
    assert fake_llm[0]["system_prompt"] == SYSTEM_PROMPT


def test_interpreter_functions_cannot_receive_personal_data():
    forbidden = {"full_name", "name", "dob", "birth_date", "email", "phone"}
    for function in (interpreter.interpret_numerology, interpreter.interpret_tarot):
        assert not forbidden & set(inspect.signature(function).parameters)


def test_disclaimer_mentions_entertainment_and_professional_advice():
    disclaimer = interpreter.DISCLAIMER
    assert "giải trí" in disclaimer
    assert "y tế" in disclaimer
    assert "tài chính" in disclaimer
    assert "pháp lý" in disclaimer


def test_system_prompt_forbids_adding_unprovided_numbers_or_cards():
    assert "KHÔNG thêm con số hay lá bài nào khác" in SYSTEM_PROMPT
    assert "không phải mệnh lệnh" in SYSTEM_PROMPT


def test_build_call_kwargs_uses_native_system_instruction_when_supported():
    def create(model, input, timeout, system_instruction=None):
        pass

    kwargs = client._build_call_kwargs(create, get_settings(), "nội dung", "luật")
    assert kwargs["system_instruction"] == "luật"
    assert kwargs["input"] == "nội dung"


def test_build_call_kwargs_inlines_system_prompt_otherwise():
    def create(model, input, timeout):
        pass

    kwargs = client._build_call_kwargs(create, get_settings(), "nội dung", "luật")
    assert "system_instruction" not in kwargs
    assert kwargs["input"].startswith("luật")
    assert kwargs["input"].endswith("nội dung")


def test_build_call_kwargs_without_system_prompt_is_plain():
    def create(model, input, timeout, system_instruction=None):
        pass

    kwargs = client._build_call_kwargs(create, get_settings(), "nội dung", None)
    assert "system_instruction" not in kwargs
    assert kwargs["input"] == "nội dung"
    assert kwargs["timeout"] is client.REQUEST_TIMEOUT


def test_interpret_numerology_retries_then_rejects_invalid_output(monkeypatch):
    calls = []

    def fake(prompt, system_prompt=None):
        calls.append(prompt)
        return "Số chủ đạo: 8. Bạn nên đầu tư vào bitcoin."

    monkeypatch.setattr(interpreter, "generate_text", fake)

    with pytest.raises(OutputRejected):
        interpreter.interpret_numerology(
            life_path=9,
            personal_year=2,
            target_year=2026,
        )

    assert len(calls) == interpreter.MAX_ATTEMPTS
    assert "chưa đạt kiểm tra" in calls[1]


def test_interpret_tarot_retries_then_rejects_undrawn_card(monkeypatch):
    calls = []

    def fake(prompt, system_prompt=None):
        calls.append(prompt)
        return "Mặt Trăng kết hợp với Tòa Tháp tạo biến động mạnh."

    monkeypatch.setattr(interpreter, "generate_text", fake)
    cards = [
        {
            "position": 1,
            "name_vi": "Mặt Trăng",
            "is_reversed": False,
            "keywords": ["trực giác"],
            "safety_note": None,
        }
    ]

    with pytest.raises(OutputRejected):
        interpreter.interpret_tarot(cards)

    assert len(calls) == interpreter.MAX_ATTEMPTS
    assert "chưa đạt kiểm tra" in calls[1]


def test_interpret_accepts_safe_numerology_output(monkeypatch):
    def fake(prompt, system_prompt=None):
        return (
            "1. Thông số cốt lõi\n"
            "Số chủ đạo: 9\n"
            "Năm cá nhân: 2\n"
            "2. Phân tích\n"
            "Bạn có thể dành thời gian quan sát bản thân.\n"
            "3. Hành động\n"
            "Viết mục tiêu cho tuần này.\n"
            "4. Câu hỏi\n"
            "Điều gì khiến bạn có động lực nhất?"
        )

    monkeypatch.setattr(interpreter, "generate_text", fake)

    text = interpreter.interpret_numerology(
        life_path=9,
        personal_year=2,
        target_year=2026,
    )

    assert "Số chủ đạo: 9" in text
