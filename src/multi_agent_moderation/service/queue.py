import json
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

from ..configs import settings
from ..schemas import ModerationItem
from ..pipeline import run_batch_dict

_executor = ThreadPoolExecutor(max_workers=settings.QUEUE_WORKERS)


def _init_job_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                result_json TEXT
            )
            """
        )
        conn.commit()


def _update_job(db_path: Path, job_id: str, status: str, result_json: Optional[str] = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, status, created_at, updated_at, result_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at, result_json=excluded.result_json
            """,
            (job_id, status, now, now, result_json),
        )
        conn.commit()


def _process_job(db_path: Path, job_id: str, items: List[ModerationItem], use_langgraph: bool) -> None:
    try:
        result = run_batch_dict(items, use_langgraph=use_langgraph)
        _update_job(db_path, job_id, "done", json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        _update_job(db_path, job_id, "failed", json.dumps({"error": str(exc)}, ensure_ascii=False))


def enqueue_batch(items: List[ModerationItem], use_langgraph: bool = False) -> str:
    db_path = settings.JOB_DB_PATH
    _init_job_db(db_path)
    job_id = str(uuid.uuid4())
    _update_job(db_path, job_id, "queued")
    _executor.submit(_process_job, db_path, job_id, items, use_langgraph)
    return job_id


def get_job(job_id: str) -> Dict[str, object]:
    db_path = settings.JOB_DB_PATH
    _init_job_db(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute("SELECT status, result_json FROM jobs WHERE id = ?", (job_id,))
        row = cur.fetchone()
    if not row:
        return {"id": job_id, "status": "not_found"}
    status, result_json = row
    payload = None
    if result_json:
        try:
            payload = json.loads(result_json)
        except Exception:
            payload = result_json
    return {"id": job_id, "status": status, "result": payload}
