from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path

db_lock = threading.Lock()


def database_path() -> Path:
    custom = os.environ.get("CODESHIELD_DB_PATH")
    if custom:
        return Path(custom)
    return Path.cwd() / "data" / "codeshield.db"


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db_lock:
        conn = connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                request_json TEXT NOT NULL,
                result_json TEXT,
                error_message TEXT,
                created_at REAL NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
