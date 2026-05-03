from pathlib import Path

from multi_agent_moderation.schemas import ModerationResult, QualitySignal, ComplianceSignal, ReviewDecision
from multi_agent_moderation.tools.audit_store import append_audit_record_db


def test_audit_store_writes_db(tmp_path: Path) -> None:
    result = ModerationResult(
        item_id="t1",
        final_action="allow",
        quality=QualitySignal(risk_level="low", duplicate_score=0.1),
        compliance=ComplianceSignal(risk_level="pass", labels=[]),
        review=ReviewDecision(need_review=False, reason="ok", action="allow"),
    )

    db_path = tmp_path / "audit.db"
    append_audit_record_db(result, db_path, meta={"source": "test"})
    assert db_path.exists()
