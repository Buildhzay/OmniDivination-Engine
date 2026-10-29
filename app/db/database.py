import hashlib
import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH_ENV = "OMNIDIVINATION_DB_PATH"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "omnidivination.db"


def get_database_path() -> Path:
    configured_path = os.getenv(DB_PATH_ENV)
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    return DEFAULT_DB_PATH


def _connect() -> sqlite3.Connection:
    path = get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS readings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                module TEXT NOT NULL CHECK (module IN ('numerology', 'tarot', 'lunar')),
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_readings_user_created
                ON readings(user_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                request_id TEXT NOT NULL,
                module TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                accepted INTEGER NOT NULL,
                rejected INTEGER NOT NULL,
                reason TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp
                ON audit_events(timestamp DESC);
            """
        )
        readings_schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'readings'"
        ).fetchone()
        if readings_schema is not None and "'lunar'" not in str(readings_schema["sql"]):
            connection.executescript(
                """
                BEGIN IMMEDIATE;

                CREATE TABLE readings_new (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    module TEXT NOT NULL
                        CHECK (module IN ('numerology', 'tarot', 'lunar')),
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                INSERT INTO readings_new (id, user_id, module, result_json, created_at)
                SELECT id, user_id, module, result_json, created_at FROM readings;

                DROP TABLE readings;
                ALTER TABLE readings_new RENAME TO readings;

                CREATE INDEX IF NOT EXISTS idx_readings_user_created
                    ON readings(user_id, created_at DESC);

                COMMIT;
                """
            )


def create_reading_session() -> tuple[str, str]:
    initialize_database()
    user_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute(
            "INSERT INTO users (id, token_hash, created_at) VALUES (?, ?, ?)",
            (user_id, token_hash, created_at),
        )
    return user_id, token


def get_user_id_for_token(token: str) -> str | None:
    initialize_database()
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _connect() as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
    return str(row["id"]) if row else None


def save_reading(user_id: str, module: str, result: dict[str, Any]) -> str:
    if module not in {"numerology", "tarot", "lunar"}:
        raise ValueError(f"Unsupported reading module: {module}")
    initialize_database()
    reading_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    result_json = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO readings (id, user_id, module, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (reading_id, user_id, module, result_json, created_at),
        )
    return reading_id


def list_readings(
    user_id: str,
    *,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    initialize_database()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, module, result_json, created_at
            FROM readings
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        ).fetchall()
    return [
        {
            "id": str(row["id"]),
            "module": str(row["module"]),
            "created_at": str(row["created_at"]),
            "result": json.loads(row["result_json"]),
        }
        for row in rows
    ]


def delete_reading(user_id: str, reading_id: str) -> bool:
    initialize_database()
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM readings WHERE id = ? AND user_id = ?",
            (reading_id, user_id),
        )
    return cursor.rowcount == 1


def save_audit_event(
    *,
    timestamp: str,
    request_id: str,
    module: str,
    endpoint: str,
    accepted: bool,
    reason: str | None,
) -> None:
    initialize_database()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO audit_events (
                timestamp, request_id, module, endpoint, accepted, rejected, reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                request_id,
                module,
                endpoint,
                int(accepted),
                int(not accepted),
                reason,
            ),
        )
