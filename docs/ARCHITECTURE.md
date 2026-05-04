# Architecture

## Flow

1. Input item with content and meta
2. Compliance agent evaluates rules + semantic signals
3. Quality agent evaluates similarity/duplication
4. Review agent prepares review payload and suggestions
5. Orchestrator routes final action (allow/review/block)
6. Audit trail is recorded (JSONL and optional SQLite)

## Components

- Orchestrators: `Orchestrator` and optional `LangGraphOrchestrator`
- Agents: quality, compliance, review
- Tools: module adapters, result sink, audit logger
- Service: optional FastAPI endpoints with async queue

## Data Contracts

- Input: `ModerationItem`
- Output: `ModerationResult` with quality/compliance/review signals

See `src/multi_agent_moderation/schemas/models.py` for definitions.
