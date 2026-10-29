from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
NUM = "/api/v1/divination/numerology"
TAROT = "/api/v1/divination/tarot"


def test_numerology_basic():
    response = client.post(NUM, json={"dob": "2006-07-03", "target_year": 2026})
    assert response.status_code == 200
    assert response.json() == {
        "life_path": 9,
        "personal_year": 2,
        "target_year": 2026,
        "soul_urge": None,
        "expression": None,
    }


def test_numerology_with_name():
    response = client.post(
        NUM,
        json={"dob": "2006-07-03", "full_name": "Nguyễn Văn A", "target_year": 2026},
    )
    assert response.status_code == 200
    assert response.json()["soul_urge"] == 8
    assert response.json()["expression"] == 7


def test_numerology_does_not_echo_personal_data():
    response = client.post(
        NUM,
        json={"dob": "2006-07-03", "full_name": "Nguyễn Văn A"},
    )
    text = response.text
    assert "Nguyễn" not in text and "Nguy" not in text
    assert "2006-07-03" not in text


def test_numerology_default_year_is_current():
    from datetime import date

    response = client.post(NUM, json={"dob": "2006-07-03"})
    assert response.json()["target_year"] == date.today().year


def test_numerology_rejects_bad_input():
    bad_payloads = [
        {"dob": "2006-02-31"},
        {"dob": "3000-01-01"},
        {"dob": "1800-01-01"},
        {"dob": "abc"},
        {},
        {"dob": "2006-07-03", "full_name": "123"},
        {"dob": "2006-07-03", "full_name": "A" * 101},
        {"dob": "2006-07-03", "target_year": 1500},
    ]
    for payload in bad_payloads:
        assert client.post(NUM, json=payload).status_code == 422, payload


def test_tarot_default_three_cards():
    response = client.post(TAROT, json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data["cards"]) == 3
    assert [card["position"] for card in data["cards"]] == [1, 2, 3]
    assert len({card["card_id"] for card in data["cards"]}) == 3
    for card in data["cards"]:
        assert card["name_vi"] and len(card["keywords"]) >= 2


def test_tarot_count_limits():
    assert len(client.post(TAROT, json={"count": 1}).json()["cards"]) == 1
    assert len(client.post(TAROT, json={"count": 10}).json()["cards"]) == 10
    for bad_count in (0, 11, -3, "abc"):
        assert client.post(TAROT, json={"count": bad_count}).status_code == 422


def test_tarot_seed_is_returned_and_replayable():
    from app.engine.tarot import draw_cards

    response = client.post(TAROT, json={"count": 5}).json()
    replay = draw_cards(5, seed=response["seed"])
    assert [card["card_id"] for card in response["cards"]] == [
        card["card_id"] for card in replay["cards"]
    ]
