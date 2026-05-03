import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Union

from ..schemas import ModerationResult, moderation_result_to_dict


def init_audit_db(db_path: Union[str, Path]) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                meta TEXT,
                result_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
    return path


def append_audit_record_db(
    result: ModerationResult,
    db_path: Union[str, Path],
    meta: Optional[Dict[str, str]] = None,
) -> Path:
    path = init_audit_db(db_path)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
        "result": moderation_result_to_dict(result),
    }
    with sqlite3.connect(str(path)) as conn:
        conn.execute(
            "INSERT INTO audit_logs (timestamp, meta, result_json) VALUES (?, ?, ?)",
            (
                record["timestamp"],
                json.dumps(record["meta"], ensure_ascii=False),
                json.dumps(record["result"], ensure_ascii=False),
            ),
        )
        conn.commit()
    return path
