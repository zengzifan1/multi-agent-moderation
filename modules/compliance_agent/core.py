import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EvidenceSpan:
    text: str
    start: int
    end: int
    keyword: str
    category: str
    level: str
    rule_id: str


def _resolve_rules_path(rules_path: Optional[str]) -> Path:
    if rules_path is None:
        return Path(__file__).resolve().parent / "rules" / "rules.json"
    return Path(rules_path)


def _resolve_kb_path(kb_path: Optional[str]) -> Path:
    if kb_path is None:
        return Path(__file__).resolve().parent / "data" / "knowledge_base.json"
    return Path(kb_path)


def _file_version(path: Optional[Path]) -> Optional[str]:
    if path is None or not path.exists():
        return None
    digest = hashlib.sha1(path.read_bytes()).hexdigest()
    return digest[:8]


def _load_rules(rules_path: Optional[str]) -> List[Dict[str, str]]:
    resolved = _resolve_rules_path(rules_path)
    with open(resolved, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_knowledge(kb_path: Optional[str]) -> List[Dict[str, str]]:
    resolved = _resolve_kb_path(kb_path)
    if not resolved.exists():
        return []
    with open(resolved, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: str) -> str:
    return text.lower()


def _build_text(item: Dict) -> str:
    title = item.get("title", "")
    content = item.get("content", "")
    return f"{title}\n{content}".strip()


def retrieve_knowledge(text: str, kb_path: Optional[str] = None, top_k: int = 2) -> List[Dict]:
    knowledge = _load_knowledge(kb_path)
    if not knowledge:
        return []
    normalized = _normalize(text)
    scored = []
    for chunk in knowledge:
        chunk_text = chunk.get("text", "").lower()
        score = 0
        for token in {"best", "free", "guarantee", "limited"}:
            if token in normalized and token in chunk_text:
                score += 1
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def _action_hint(level: str) -> str:
    if level == "high":
        return "block"
    if level == "medium":
        return "review"
    if level == "low":
        return "allow"
    return "allow"


def _severity(levels: List[str]) -> str:
    if "high" in levels:
        return "high"
    if "medium" in levels:
        return "medium"
    if "low" in levels:
        return "low"
    return "pass"


def analyze_blacklist(text: str, platform: Optional[str] = None, rules_path: Optional[str] = None) -> Dict:
    rules = _load_rules(rules_path)
    rules_version = _file_version(_resolve_rules_path(rules_path))
    normalized = _normalize(text)
    evidence: List[EvidenceSpan] = []

    for rule in rules:
        rule_platforms = rule.get("platforms")
        if rule_platforms and platform and platform not in rule_platforms:
            continue
        keyword = rule["keyword"].lower()
        start = 0
        while True:
            idx = normalized.find(keyword, start)
            if idx == -1:
                break
            end = idx + len(keyword)
            evidence.append(
                EvidenceSpan(
                    text=text,
                    start=idx,
                    end=end,
                    keyword=rule["keyword"],
                    category=rule["category"],
                    level=rule["level"],
                    rule_id=rule.get("id", "rule")
                )
            )
            start = end

    labels = sorted({e.category for e in evidence})
    levels = [e.level for e in evidence]
    action_hint = _action_hint(_severity(levels))
    return {
        "risk_level": _severity(levels),
        "risk_types": labels,
        "evidence_spans": [e.__dict__ for e in evidence],
        "hit_items": [{"keyword": e.keyword, "category": e.category, "level": e.level} for e in evidence],
        "hit_count": len(evidence),
        "references": [{"source": "rules", "platform": platform or "default", "version": rules_version}],
        "reasons": ["rule match" if evidence else "no rule hit"],
        "action_hint": action_hint,
        "evidence_complete": bool(evidence),
        "versions": {"rules": rules_version},
    }


def analyze_semantic(
    text: str,
    knowledge_snippets: Optional[List[Dict]] = None,
    knowledge_version: Optional[str] = None,
) -> Dict:
    normalized = _normalize(text)
    heuristics = [
        {"keyword": "free", "category": "marketing", "level": "medium"},
        {"keyword": "guarantee", "category": "marketing", "level": "medium"},
        {"keyword": "limited", "category": "exaggeration", "level": "low"},
    ]
    evidence = []
    for rule in heuristics:
        keyword = rule["keyword"]
        if keyword in normalized:
            start = normalized.find(keyword)
            end = start + len(keyword)
            evidence.append(
                EvidenceSpan(
                    text=text,
                    start=start,
                    end=end,
                    keyword=keyword,
                    category=rule["category"],
                    level=rule["level"],
                    rule_id="semantic-heuristic",
                )
            )
    labels = sorted({e.category for e in evidence})
    levels = [e.level for e in evidence]
    return {
        "risk_level": _severity(levels),
        "risk_types": labels,
        "evidence_spans": [e.__dict__ for e in evidence],
        "hit_items": [{"keyword": e.keyword, "category": e.category, "level": e.level} for e in evidence],
        "hit_count": len(evidence),
        "references": [
            {
                "source": "semantic",
                "model": "heuristic",
                "knowledge": knowledge_snippets or [],
                "version": knowledge_version,
            }
        ],
        "reasons": ["semantic heuristic" if evidence else "no semantic hit"],
        "action_hint": _action_hint(_severity(levels)),
        "evidence_complete": bool(evidence),
        "versions": {"knowledge_base": knowledge_version},
    }


def analyze_compliance(
    text: str,
    platform: Optional[str] = None,
    rules_path: Optional[str] = None,
    knowledge_snippets: Optional[List[Dict]] = None,
    rules_version: Optional[str] = None,
    knowledge_version: Optional[str] = None,
) -> Dict:
    rule_result = analyze_blacklist(text, platform=platform, rules_path=rules_path)
    semantic_result = analyze_semantic(
        text,
        knowledge_snippets=knowledge_snippets,
        knowledge_version=knowledge_version,
    )

    combined_levels = [rule_result["risk_level"], semantic_result["risk_level"]]
    risk_level = _severity(combined_levels)
    risk_types = sorted(set(rule_result["risk_types"] + semantic_result["risk_types"]))

    return {
        "risk_level": risk_level,
        "risk_types": risk_types,
        "evidence_spans": rule_result["evidence_spans"] + semantic_result["evidence_spans"],
        "hit_items": rule_result["hit_items"] + semantic_result["hit_items"],
        "hit_count": rule_result["hit_count"] + semantic_result["hit_count"],
        "references": rule_result["references"] + semantic_result["references"],
        "reasons": rule_result["reasons"] + semantic_result["reasons"],
        "action_hint": _action_hint(risk_level),
        "evidence_complete": rule_result["evidence_complete"] or semantic_result["evidence_complete"],
        "versions": {
            "rules": rules_version or rule_result.get("versions", {}).get("rules"),
            "knowledge_base": knowledge_version or semantic_result.get("versions", {}).get("knowledge_base"),
        },
        "components": {
            "rule": rule_result,
            "semantic": semantic_result,
        },
    }


def analyze_item(item: Dict, rules_path: Optional[str] = None) -> Dict:
    text = _build_text(item)
    kb_path = item.get("kb_path")
    knowledge = item.get("knowledge")
    rules_version = _file_version(_resolve_rules_path(rules_path))
    knowledge_version = _file_version(_resolve_kb_path(kb_path))
    if knowledge is None:
        knowledge = retrieve_knowledge(text, kb_path=kb_path)
    return analyze_compliance(
        text=text,
        platform=item.get("platform"),
        rules_path=rules_path,
        knowledge_snippets=knowledge,
        rules_version=rules_version,
        knowledge_version=knowledge_version,
    )


def analyze_batch(items: List[Dict], rules_path: Optional[str] = None) -> List[Dict]:
    results = []
    for item in items:
        result = analyze_item(item, rules_path=rules_path)
        results.append({"id": item.get("id"), "result": result})
    return results
