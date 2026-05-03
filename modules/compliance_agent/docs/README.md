# Compliance Agent Docs

- API: API.md

All examples are synthetic.

## Rule Schema

Each rule in rules/rules.json uses the following fields:

- id: unique rule id
- level: high | medium | low
- category: risk category label
- keyword: match token (case-insensitive)
- platforms (optional): list of platform names where the rule applies

## Output Notes

- evidence_complete: true when at least one evidence span is present
- action_hint: allow | review | block for routing

## Minimal RAG

- data/knowledge_base.json provides local knowledge snippets
- retrieve_knowledge performs simple token match and returns Top-K chunks
