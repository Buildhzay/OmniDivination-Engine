import pytest
from fastapi.testclient import TestClient

from app.ai import interpreter
from app.ai.client import LLMNotConfigured, LLMUnavailable
from app.ai.prompts import SYSTEM_PROMPT
from app.main import app

client = TestClient(app)
NUM = "/api/v1/divination/numerology/interpret"
TAROT = "/api/v1/divination/tarot/interpret"


@pytest.fixture
def fake_llm(monkeypatch):
    calls = []

    def fake(prompt, system_prompt=None):
        calls.append({"prompt": prompt, "system_prompt": system_prompt})
        return "Bản luận giải thử."

    monkeypatch.setattr(interpreter, "generate_text", fake)
    return calls


def test_numerology_interpret_success(fake_llm):
    response = client.post(
        NUM,
        json={
            "dob": "2006-07-03",
            "full_name": "Nguyễn Văn A",
            "target_year": 2026,
            "topic": "career",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["life_path"] == 9 and data["personal_year"] == 2
    assert data["interpretation"] == "Bản luận giải thử."
    assert "giải trí" in data["disclaimer"]
    assert fake_llm[0]["system_prompt"] == SYSTEM_PROMPT


def test_personal_data_never_reaches_llm(fake_llm):
    client.post(
        NUM,
        json={
            "dob": "2006-07-03",
            "full_name": "Nguyễn Văn A",
            "target_year": 2026,
        },
    )
    sent = fake_llm[0]["prompt"] + fake_llm[0]["system_prompt"]
    assert "Nguy" not in sent and "Văn A" not in sent
    assert "2006" not in sent and "07-03" not in sent


def test_personal_data_not_in_response(fake_llm):
    response = client.post(
        NUM,
        json={"dob": "2006-07-03", "full_name": "Nguyễn Văn A"},
    )
    assert "Nguy" not in response.text
    assert "2006-07-03" not in response.text


def test_tarot_interpret_success(fake_llm):
    response = client.post(TAROT, json={"count": 3})
    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 3
    assert data["interpretation"] == "Bản luận giải thử." and data["disclaimer"]
    for card in data["cards"]:
        assert card["name_vi"] in fake_llm[0]["prompt"]


def test_invalid_input_rejected_before_calling_llm(fake_llm):
    assert client.post(NUM, json={"dob": "2006-02-31"}).status_code == 422
    assert (
        client.post(NUM, json={"dob": "2006-07-03", "topic": "health"}).status_code
        == 422
    )
    assert client.post(TAROT, json={"count": 99}).status_code == 422
    assert fake_llm == []


@pytest.mark.parametrize(
    ("exception", "status"),
    [
        (LLMNotConfigured("x SECRET-1"), 503),
        (LLMUnavailable("x SECRET-1"), 502),
    ],
)
def test_llm_errors_become_clean_http_errors(monkeypatch, exception, status):
    def fail(prompt, system_prompt=None):
        raise exception

    monkeypatch.setattr(interpreter, "generate_text", fail)
    for url, payload in ((NUM, {"dob": "2006-07-03"}), (TAROT, {"count": 1})):
        response = client.post(url, json=payload)
        assert response.status_code == status
        assert "SECRET-1" not in response.text
