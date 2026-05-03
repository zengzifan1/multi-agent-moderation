import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Union

from ..schemas import ModerationResult, moderation_result_to_dict


def append_audit_record(
    result: ModerationResult,
    audit_path: Union[str, Path],
    meta: Optional[Dict[str, str]] = None,
) -> Path:
    path = Path(audit_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
        "result": moderation_result_to_dict(result),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
