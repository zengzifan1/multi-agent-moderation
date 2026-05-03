from typing import List, Optional, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ..pipeline import run_item_dict, run_batch_dict, run_item_and_audit
from ..schemas import ModerationItem
from .queue import enqueue_batch, get_job

app = FastAPI(title="multi-agent-moderation")


class ModerationItemPayload(BaseModel):
    item_id: str = Field(..., min_length=1)
    content: str
    source: Optional[str] = None
    meta: Dict[str, object] = Field(default_factory=dict)


class ModerateRequest(BaseModel):
    item: ModerationItemPayload
    use_langgraph: bool = False
    audit: bool = False


class ModerateBatchRequest(BaseModel):
    items: List[ModerationItemPayload]
    use_langgraph: bool = False
    audit: bool = False


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/moderate")
def moderate(request: ModerateRequest) -> Dict[str, object]:
    item = ModerationItem(
        item_id=request.item.item_id,
        content=request.item.content,
        source=request.item.source,
        meta=request.item.meta,
    )
    result = run_item_dict(item, use_langgraph=request.use_langgraph)
    if request.audit:
        run_item_and_audit(item)
    return result


@app.post("/moderate/batch")
def moderate_batch(request: ModerateBatchRequest) -> List[Dict[str, object]]:
    items = [
        ModerationItem(
            item_id=item.item_id,
            content=item.content,
            source=item.source,
            meta=item.meta,
        )
        for item in request.items
    ]
    return run_batch_dict(items, use_langgraph=request.use_langgraph)


@app.post("/moderate/async")
def moderate_async(request: ModerateBatchRequest) -> Dict[str, str]:
    items = [
        ModerationItem(
            item_id=item.item_id,
            content=item.content,
            source=item.source,
            meta=item.meta,
        )
        for item in request.items
    ]
    job_id = enqueue_batch(items, use_langgraph=request.use_langgraph)
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def job_status(job_id: str) -> Dict[str, object]:
    return get_job(job_id)
