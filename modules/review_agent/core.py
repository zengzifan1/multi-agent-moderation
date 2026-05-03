import json
from pathlib import Path
from typing import Dict, List, Optional


def _suggestions(compliance_result: Dict) -> List[str]:
    level = compliance_result.get("risk_level")
    if level in {"high", "medium"}:
        return ["Revise risky phrases", "Add evidence or clarification"]
    if level == "low":
        return ["Tone down exaggerated wording"]
    return ["No action required"]


def _load_replacement_rules(rules_path: Optional[str]) -> List[Dict]:
    if rules_path is None:
        rules_path = Path(__file__).resolve().parent / "data" / "replacement_rules.json"
    if not Path(rules_path).exists():
        return []
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _replacement_candidates(compliance_result: Dict, rules_path: Optional[str] = None) -> List[Dict]:
    rules = _load_replacement_rules(rules_path)
    candidates = []
    for span in compliance_result.get("evidence_spans", []):
        keyword = span.get("keyword")
        if not keyword:
            continue
        matched = False
        for rule in rules:
            if rule.get("original") == keyword:
                candidates.append({
                    "original": keyword,
                    "replacement": rule.get("replacement", "[redacted]"),
                    "reason": rule.get("reason", "rule-based"),
                })
                matched = True
                break
        if not matched:
            candidates.append({
                "original": keyword,
                "replacement": "[redacted]",
                "reason": "rule-based placeholder",
            })
    return candidates


def _needs_review(compliance_result: Dict, quality_signal: Dict) -> bool:
    compliance_level = compliance_result.get("risk_level", "pass")
    quality_level = quality_signal.get("risk_level", "low")
    action_hint = compliance_result.get("action_hint")
    evidence_complete = compliance_result.get("evidence_complete", True)

    if action_hint in {"review", "block"}:
        return True
    if not evidence_complete:
        return True
    return compliance_level in {"high", "medium"} or quality_level in {"medium", "high"}


def review_decision(compliance_result: Dict, quality_signal: Dict, rules_path: Optional[str] = None) -> Dict:
    compliance_level = compliance_result.get("risk_level", "pass")
    quality_level = quality_signal.get("risk_level", "low")
    evidence_versions = compliance_result.get("versions", {})

    need_review = _needs_review(compliance_result, quality_signal)
    action = "review" if need_review else "allow"

    return {
        "need_review": need_review,
        "action": action,
        "reason": "rule: compliance or quality indicates risk",
        "review_payload": {
            "risk_level": compliance_level,
            "risk_types": compliance_result.get("risk_types", []),
            "highlight_spans": compliance_result.get("evidence_spans", []),
            "suggestions": _suggestions(compliance_result),
            "replacements": _replacement_candidates(compliance_result, rules_path=rules_path),
            "references": compliance_result.get("references", []),
            "evidence_complete": compliance_result.get("evidence_complete", True),
            "action_hint": compliance_result.get("action_hint", "allow"),
            "auto_recheck": True,
            "evidence_versions": evidence_versions,
        },
        "decision_basis": {
            "compliance_level": compliance_level,
            "quality_level": quality_level,
            "action_hint": compliance_result.get("action_hint", "allow"),
            "evidence_complete": compliance_result.get("evidence_complete", True),
            "evidence_versions": evidence_versions,
        },
        "trace": {
            "compliance_level": compliance_level,
            "quality_level": quality_level,
        },
    }
