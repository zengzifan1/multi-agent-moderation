from pathlib import Path
import sys

from ..schemas import QualitySignal, ComplianceSignal, ReviewDecision
from ..configs import settings


def _load_review_agent_module() -> bool:
    module_root = Path(__file__).resolve().parents[3] / "modules" / "review_agent"
    if not module_root.exists():
        return False
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))
    return True


def review_tool(quality: QualitySignal, compliance: ComplianceSignal) -> ReviewDecision:
    need_review = quality.risk_level != "low" or compliance.risk_level not in {"pass", "low"}
    reason = "rule: compliance or quality indicates risk"
    action = "review" if need_review else "allow"
    review_payload = {}
    decision_basis = {}
    trace = {}

    if _load_review_agent_module():
        try:
            from core import review_decision

            result = review_decision(
                compliance_result={
                    "risk_level": compliance.risk_level,
                    "risk_types": compliance.labels,
                    "evidence_spans": compliance.evidence.get("spans", []),
                    "references": compliance.evidence.get("references", []),
                    "evidence_complete": compliance.evidence.get("evidence_complete", True),
                    "action_hint": compliance.evidence.get("action_hint", "allow"),
                    "versions": compliance.evidence.get("versions", {}),
                },
                quality_signal={"risk_level": quality.risk_level},
                rules_path=settings.REVIEW_REPLACEMENT_RULES_PATH,
            )
            need_review = bool(result.get("need_review", need_review))
            reason = result.get("reason", reason)
            action = result.get("action", action)
            review_payload = result.get("review_payload", review_payload)
            decision_basis = result.get("decision_basis", decision_basis)
            trace = result.get("trace", trace)
        except Exception as exc:
            reason = f"fallback: {exc}"

    return ReviewDecision(
        need_review=need_review,
        reason=reason,
        action=action,
        review_payload=review_payload,
        decision_basis=decision_basis,
        trace=trace,
    )
