# Compliance Agent API

## analyze_compliance

Inputs:
- text: str
- platform: str | None
- rules_path: str | None
- knowledge_snippets: list[dict] | None

Output (dict):
- risk_level: pass | low | medium | high
- risk_types: list[str]
- evidence_spans: list[dict]
- hit_items: list[dict]
- hit_count: int
- references: list[dict]
- reasons: list[str]
- action_hint: allow | review | block
- evidence_complete: bool
- versions: dict (rules, knowledge_base)
- components: dict (rule + semantic)

## analyze_item

Input (dict):
- id: str | int
- title: str
- content: str
- platform: str | None
- knowledge: list[dict] | None
- kb_path: str | None

Output: same as analyze_compliance

## analyze_batch

Input: list of items
Output: list of {id, result}

## retrieve_knowledge

Input:
- text: str
- kb_path: str | None
- top_k: int

Output:
- list of knowledge chunks
