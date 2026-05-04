from pathlib import Path
import sys

from ..schemas import ModerationItem, ComplianceSignal
from ..configs import settings


def _load_compliance_agent_module() -> bool:
    module_root = Path(__file__).resolve().parents[3] / "modules" / "compliance_agent"
    if not module_root.exists():
        return False
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))
    return True


def compliance_tool(item: ModerationItem) -> ComplianceSignal:
    labels = []
    risk = "pass"
    evidence = {"source": "rules"}

    if _load_compliance_agent_module():
        try:
            from core import analyze_item

            payload = {
                "id": item.item_id,
                "title": item.meta.get("title", ""),
                "content": item.content,
                "platform": item.source,
                "kb_path": item.meta.get("kb_path"),
                "knowledge": item.meta.get("knowledge"),
            }
            rules_path = item.meta.get("rules_path") or settings.COMPLIANCE_RULES_PATH
            result = analyze_item(payload, rules_path=rules_path)
            risk = result.get("risk_level", "pass")
            labels = result.get("risk_types", [])
            evidence = {
                "spans": result.get("evidence_spans", []),
                "references": result.get("references", []),
                "action_hint": result.get("action_hint", "allow"),
                "evidence_complete": result.get("evidence_complete", False),
                "hit_count": result.get("hit_count", 0),
                "versions": result.get("versions", {}),
            }
        except Exception as exc:
            evidence = {"source": "rules", "error": str(exc)}

    return ComplianceSignal(risk_level=risk, labels=labels, evidence=evidence)
