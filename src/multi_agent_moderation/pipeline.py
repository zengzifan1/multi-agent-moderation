from typing import List, Optional, Dict

from .chains import Orchestrator, LangGraphOrchestrator
from .schemas import ModerationItem, ModerationResult, moderation_result_to_dict
from .tools import (
    save_moderation_result,
    save_moderation_results,
    append_audit_record,
    append_audit_record_db,
)
from .configs import settings


def _get_orchestrator(use_langgraph: bool = False) -> object:
    if use_langgraph:
        return LangGraphOrchestrator()
    return Orchestrator()


def run_item(item: ModerationItem, use_langgraph: bool = False) -> ModerationResult:
    orchestrator = _get_orchestrator(use_langgraph)
    return orchestrator.run(item)


def run_item_dict(item: ModerationItem, use_langgraph: bool = False) -> dict:
    return moderation_result_to_dict(run_item(item, use_langgraph=use_langgraph))


def run_batch(items: List[ModerationItem], use_langgraph: bool = False) -> List[ModerationResult]:
    orchestrator = _get_orchestrator(use_langgraph)
    return orchestrator.run_batch(items)


def run_batch_dict(items: List[ModerationItem], use_langgraph: bool = False) -> List[dict]:
    return [moderation_result_to_dict(result) for result in run_batch(items, use_langgraph=use_langgraph)]


def run_item_and_save(
    item: ModerationItem,
    output_path: str,
    use_langgraph: bool = False,
) -> str:
    result = run_item(item, use_langgraph=use_langgraph)
    path = save_moderation_result(result, output_path)
    return str(path)


def run_item_and_audit(
    item: ModerationItem,
    audit_path: Optional[str] = None,
    meta: Optional[Dict[str, str]] = None,
    use_langgraph: bool = False,
) -> str:
    result = run_item(item, use_langgraph=use_langgraph)
    if not settings.ENABLE_AUDIT:
        return ""
    if audit_path is None:
        audit_path = str(settings.AUDIT_LOG_PATH)
    path = append_audit_record(result, audit_path, meta=meta)
    if settings.ENABLE_AUDIT_DB:
        append_audit_record_db(result, settings.AUDIT_DB_PATH, meta=meta)
    return str(path)


def run_batch_and_save(
    items: List[ModerationItem],
    output_path: str,
    use_langgraph: bool = False,
) -> str:
    results = run_batch(items, use_langgraph=use_langgraph)
    path = save_moderation_results(results, output_path)
    return str(path)


def run_batch_and_audit(
    items: List[ModerationItem],
    audit_path: Optional[str] = None,
    meta: Optional[Dict[str, str]] = None,
    use_langgraph: bool = False,
) -> str:
    if not settings.ENABLE_AUDIT:
        return ""
    if audit_path is None:
        audit_path = str(settings.AUDIT_LOG_PATH)
    for item in items:
        result = run_item(item, use_langgraph=use_langgraph)
        append_audit_record(result, audit_path, meta=meta)
        if settings.ENABLE_AUDIT_DB:
            append_audit_record_db(result, settings.AUDIT_DB_PATH, meta=meta)
    return audit_path
