import json
import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.db.database import initialize_database, save_reading
from app.main import app
from app.rate_limit import limiter

client = TestClient(app)
LUNAR = "/api/v1/divination/lunar"
SESSION = "/api/v1/readings/session"
HISTORY = "/api/v1/readings/history"


@pytest.fixture(autouse=True)
def isolate_database_and_rate_limit(tmp_path, monkeypatch):
    limiter.reset()
    monkeypatch.setenv(
        "OMNIDIVINATION_DB_PATH",
        str(tmp_path / "lunar.sqlite3"),
    )
    yield
    limiter.reset()


def test_lunar_api_returns_lunar_date_and_can_chi() -> None:
    response = client.post(
        LUNAR,
        json={"dob": "2006-07-03", "birth_time": "15:30"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "solar_date": "2006-07-03",
        "lunar_date": {
            "day": 9,
            "month": 6,
            "year": 2006,
            "is_leap_month": False,
        },
        "can_chi": {
            "year": "Bính Tuất",
            "month": "Ất Mùi",
            "day": "Quý Tỵ",
            "hour": "Canh Thân",
        },
    }


def test_lunar_api_allows_missing_birth_time() -> None:
    response = client.post(LUNAR, json={"dob": "2024-02-10"})

    assert response.status_code == 200
    assert response.json()["can_chi"]["hour"] is None


def test_lunar_api_year_changes_at_lunar_new_year() -> None:
    before_new_year = client.post(LUNAR, json={"dob": "2024-02-09"})
    lunar_new_year = client.post(LUNAR, json={"dob": "2024-02-10"})

    assert before_new_year.json()["can_chi"]["year"] == "Quý Mão"
    assert lunar_new_year.json()["can_chi"]["year"] == "Giáp Thìn"


def test_lunar_api_rejects_future_dates_timezone_and_extra_fields() -> None:
    future = client.post(LUNAR, json={"dob": "2999-01-01"})
    timezone_aware = client.post(
        LUNAR,
        json={"dob": "2006-07-03", "birth_time": "15:30:00+07:00"},
    )
    extra_field = client.post(
        LUNAR,
        json={"dob": "2006-07-03", "full_name": "Sensitive name"},
    )

    assert future.status_code == 422
    assert timezone_aware.status_code == 422
    assert extra_field.status_code == 422


def test_lunar_reading_history_omits_solar_birth_date() -> None:
    session = client.post(SESSION)
    token = session.json()["reading_token"]
    response = client.post(
        LUNAR,
        json={"dob": "2006-07-03", "birth_time": "15:30"},
        headers={"X-Reading-Token": token},
    )
    history = client.get(HISTORY, headers={"X-Reading-Token": token})

    assert response.status_code == 200
    assert history.status_code == 200
    records = history.json()
    assert len(records) == 1
    assert records[0]["module"] == "lunar"
    assert "solar_date" not in records[0]["result"]
    assert "2006-07-03" not in json.dumps(records, ensure_ascii=False)


def test_database_migrates_existing_readings_table(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    monkeypatch.setenv("OMNIDIVINATION_DB_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE readings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                module TEXT NOT NULL CHECK (module IN ('numerology', 'tarot')),
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX idx_readings_user_created
                ON readings(user_id, created_at DESC);
            INSERT INTO users VALUES ('user-1', 'hash', '2026-01-01T00:00:00+00:00');
            INSERT INTO readings VALUES (
                'reading-1', 'user-1', 'numerology', '{"life_path":9}',
                '2026-01-01T00:00:00+00:00'
            );
            """
        )

    initialize_database()
    with sqlite3.connect(database_path) as connection:
        legacy_record = connection.execute(
            "SELECT module, result_json FROM readings WHERE id = 'reading-1'"
        ).fetchone()
        check_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'readings'"
        ).fetchone()[0]

    assert legacy_record == ("numerology", '{"life_path":9}')
    assert "lunar" in check_sql
    save_reading("user-1", "lunar", {"lunar_date": {"day": 1}})
    with sqlite3.connect(os.environ["OMNIDIVINATION_DB_PATH"]) as connection:
        assert connection.execute(
            "SELECT module FROM readings WHERE module = 'lunar'"
        ).fetchone() == ("lunar",)
