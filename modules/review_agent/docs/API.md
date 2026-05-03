# Review Agent API

## review_decision

Inputs:
- compliance_result: dict
- quality_signal: dict
- rules_path: str | None

Output (dict):
- need_review: bool
- action: allow | review
- reason: str
- review_payload: dict
- decision_basis: dict
- trace: dict

decision_basis fields:
- compliance_level: str
- quality_level: str
- action_hint: str
- evidence_complete: bool
- evidence_versions: dict (rules, knowledge_base)

review_payload fields:
- risk_level: str
- risk_types: list[str]
- highlight_spans: list[dict]
- suggestions: list[str]
- replacements: list[dict]
- references: list[dict]
- evidence_complete: bool
- action_hint: str
- auto_recheck: bool
- evidence_versions: dict (rules, knowledge_base)
