import json
from pathlib import Path
from typing import Iterable, List, Dict, Any, Union

from .schemas import ModerationItem, ModerationResult, moderation_result_to_dict


def load_items(path: Union[str, Path]) -> List[ModerationItem]:
    data_path = Path(path)
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    items: List[ModerationItem] = []
    for entry in payload:
        items.append(
            ModerationItem(
                item_id=str(entry.get("item_id") or entry.get("id") or ""),
                content=entry.get("content", ""),
                source=entry.get("source"),
                meta=entry.get("meta", {}),
            )
        )
    return items


def items_to_dicts(items: Iterable[ModerationItem]) -> List[Dict[str, Any]]:
    return [
        {
            "item_id": item.item_id,
            "content": item.content,
            "source": item.source,
            "meta": item.meta,
        }
        for item in items
    ]


def save_results(path: Union[str, Path], results: Iterable[ModerationResult]) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [moderation_result_to_dict(result) for result in results]
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
