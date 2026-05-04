# API

Base service: FastAPI app at `multi_agent_moderation.service.app`.

## Endpoints

### GET /health

Returns service status.

### POST /moderate

Moderate a single item.

Request body:
- item: { item_id, content, source?, meta? }
- use_langgraph: boolean
- audit: boolean

### POST /moderate/batch

Moderate multiple items in one request.

Request body:
- items: [ { item_id, content, source?, meta? } ]
- use_langgraph: boolean
- audit: boolean

### POST /moderate/async

Submit an async batch job.

Request body:
- items: [ { item_id, content, source?, meta? } ]
- use_langgraph: boolean
- audit: boolean

### GET /jobs/{job_id}

Query job status and result payload.
