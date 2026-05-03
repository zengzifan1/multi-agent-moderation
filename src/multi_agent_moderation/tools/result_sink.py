import json
from pathlib import Path
from typing import Union, Iterable, List

from ..schemas import ModerationResult, moderation_result_to_dict


def save_moderation_result(result: ModerationResult, output_path: Union[str, Path]) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = moderation_result_to_dict(result)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_moderation_results(results: Iterable[ModerationResult], output_path: Union[str, Path]) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: List[dict] = [moderation_result_to_dict(result) for result in results]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
