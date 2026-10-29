import json
import os
import sqlite3
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.ai import interpreter
from app.main import app
from app.rate_limit import limiter

client = TestClient(app)
SESSION = "/api/v1/readings/session"
HISTORY = "/api/v1/readings/history"
NUMEROLOGY = "/api/v1/divination/numerology"
NUMEROLOGY_INTERPRET = "/api/v1/divination/numerology/interpret"


@pytest.fixture(autouse=True)
def isolate_database_and_rate_limit(tmp_path, monkeypatch):
    limiter.reset()
    monkeypatch.setenv(
        "OMNIDIVINATION_DB_PATH",
        str(tmp_path / "readings.sqlite3"),
    )
    yield
    limiter.reset()


def _create_session() -> tuple[str, str]:
    response = client.post(SESSION)
    assert response.status_code == 201
    data = response.json()
    UUID(data["user_id"])
    assert data["reading_token"]
    return data["user_id"], data["reading_token"]


def test_reading_token_is_required_and_session_token_is_not_stored_plaintext():
    response = client.get(HISTORY)
    assert response.status_code == 401

    user_id, token = _create_session()
    history = client.get(HISTORY, headers={"X-Reading-Token": token})

    assert history.status_code == 200
    assert history.json() == []
    with sqlite3.connect(os.environ["OMNIDIVINATION_DB_PATH"]) as connection:
        stored_token_hash = connection.execute(
            "SELECT token_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()[0]
    assert stored_token_hash != token


def test_readings_are_saved_without_name_or_birth_date(monkeypatch):
    monkeypatch.setattr(
        interpreter,
        "generate_text",
        lambda prompt, system_prompt=None: "Số chủ đạo: 9. Năm cá nhân: 2.",
    )
    _, token = _create_session()
    headers = {"X-Reading-Token": token}
    payload = {
        "dob": "2006-07-03",
        "full_name": "Nguyễn Văn A",
        "target_year": 2026,
    }

    calculated = client.post(NUMEROLOGY, json=payload, headers=headers)
    assert calculated.status_code == 200
    interpreted = client.post(NUMEROLOGY_INTERPRET, json=payload, headers=headers)
    assert interpreted.status_code == 200

    history = client.get(HISTORY, headers=headers)
    assert history.status_code == 200
    records = history.json()
    assert len(records) == 2
    assert all(record["module"] == "numerology" for record in records)
    serialized_history = json.dumps(records, ensure_ascii=False)
    assert "Nguyễn Văn A" not in serialized_history
    assert "2006-07-03" not in serialized_history


def test_reading_history_isolated_by_owner_token():
    _, owner_token = _create_session()
    _, other_token = _create_session()
    response = client.post(
        NUMEROLOGY,
        json={"dob": "2006-07-03", "target_year": 2026},
        headers={"X-Reading-Token": owner_token},
    )
    assert response.status_code == 200

    owner_history = client.get(HISTORY, headers={"X-Reading-Token": owner_token})
    other_history = client.get(HISTORY, headers={"X-Reading-Token": other_token})

    assert len(owner_history.json()) == 1
    assert other_history.json() == []


def test_reading_token_can_delete_only_its_own_readings():
    _, owner_token = _create_session()
    _, other_token = _create_session()
    response = client.post(
        NUMEROLOGY,
        json={"dob": "2006-07-03"},
        headers={"X-Reading-Token": owner_token},
    )
    assert response.status_code == 200

    owner_history = client.get(HISTORY, headers={"X-Reading-Token": owner_token})
    reading_id = owner_history.json()[0]["id"]
    assert client.delete(
        f"{HISTORY}/{reading_id}",
        headers={"X-Reading-Token": other_token},
    ).status_code == 404
    assert client.delete(
        f"{HISTORY}/{reading_id}",
        headers={"X-Reading-Token": owner_token},
    ).status_code == 204
    assert client.get(HISTORY, headers={"X-Reading-Token": owner_token}).json() == []


def test_history_requires_valid_token_and_supports_pagination():
    _, owner_token = _create_session()
    headers = {"X-Reading-Token": owner_token}
    for year in (2024, 2025, 2026):
        response = client.post(
            NUMEROLOGY,
            json={"dob": "2006-07-03", "target_year": year},
            headers=headers,
        )
        assert response.status_code == 200

    first_page = client.get(HISTORY, headers=headers, params={"limit": 2})
    second_page = client.get(HISTORY, headers=headers, params={"limit": 2, "offset": 2})

    assert first_page.status_code == 200
    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 1
    assert first_page.json()[0]["result"]["target_year"] == 2026
    assert client.get(HISTORY, headers={"X-Reading-Token": "invalid"}).status_code == 401


def test_calculation_without_token_does_not_persist_reading():
    response = client.post(
        NUMEROLOGY,
        json={"dob": "2006-07-03"},
    )
    assert response.status_code == 200
    assert not os.path.exists(os.environ["OMNIDIVINATION_DB_PATH"])


def test_audit_events_are_persisted_without_prompt_or_personal_data(
    tmp_path,
    monkeypatch,
):
    from app.ai import interpreter

    monkeypatch.setattr(
        interpreter,
        "generate_text",
        lambda prompt, system_prompt=None: "Số chủ đạo: 9. Năm cá nhân: 2.",
    )
    response = client.post(
        NUMEROLOGY_INTERPRET,
        json={
            "dob": "2006-07-03",
            "full_name": "Nguyễn Văn A",
            "target_year": 2026,
        },
    )
    assert response.status_code == 200

    with sqlite3.connect(os.environ["OMNIDIVINATION_DB_PATH"]) as connection:
        event = connection.execute(
            """
            SELECT request_id, module, endpoint, accepted, rejected, reason
            FROM audit_events
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    assert event == (
        response.headers["x-request-id"],
        "numerology",
        NUMEROLOGY_INTERPRET,
        1,
        0,
        None,
    )
    with open(os.environ["OMNIDIVINATION_DB_PATH"], "rb") as database_file:
        database_bytes = database_file.read()
    assert b"Nguyen Van A" not in database_bytes
    assert b"2006-07-03" not in database_bytes
