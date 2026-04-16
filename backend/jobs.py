from __future__ import annotations

import json
import time
from typing import Any
from uuid import UUID

from backend.db import connect, db_lock, init_db
from backend.models import PathAnalysisRequest

# init_db imported lazily from main; jobs.ensure_db calls init_db


def ensure_db() -> None:
    init_db()


def create_job(request: PathAnalysisRequest) -> UUID:
    ensure_db()
    from uuid import uuid4

    job_id = uuid4()
    payload = request.model_dump(mode="json")
    with db_lock:
        conn = connect()
        conn.execute(
            """
            INSERT INTO analysis_jobs (id, status, request_json, result_json, error_message, created_at)
            VALUES (?, ?, ?, NULL, NULL, ?)
            """,
            (str(job_id), "pending", json.dumps(payload), time.time()),
        )
        conn.commit()
        conn.close()
    return job_id


def complete_job(job_id: UUID, result: dict[str, Any]) -> None:
    with db_lock:
        conn = connect()
        conn.execute(
            """
            UPDATE analysis_jobs
            SET status = ?, result_json = ?, error_message = NULL
            WHERE id = ?
            """,
            ("completed", json.dumps(result), str(job_id)),
        )
        conn.commit()
        conn.close()


def fail_job(job_id: UUID, message: str) -> None:
    with db_lock:
        conn = connect()
        conn.execute(
            """
            UPDATE analysis_jobs
            SET status = ?, error_message = ?, result_json = NULL
            WHERE id = ?
            """,
            ("failed", message, str(job_id)),
        )
        conn.commit()
        conn.close()


def get_job(job_id: UUID) -> dict[str, Any] | None:
    ensure_db()
    with db_lock:
        conn = connect()
        row = conn.execute("SELECT * FROM analysis_jobs WHERE id = ?", (str(job_id),)).fetchone()
        conn.close()
    if row is None:
        return None
    return dict(row)
