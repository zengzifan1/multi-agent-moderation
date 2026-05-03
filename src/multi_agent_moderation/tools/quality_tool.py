from pathlib import Path
import json
import sys

from ..schemas import ModerationItem, QualitySignal
from ..quality_runtime import analyze_dedup_in_memory, max_duplicate_score
from ..configs import settings


def _load_quality_agent_module() -> bool:
    module_root = Path(__file__).resolve().parents[3] / "modules" / "quality_agent"
    if not module_root.exists():
        return False
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))
    return True


def quality_tool(item: ModerationItem) -> QualitySignal:
    score = 0.0
    evidence = {"method": "cosine"}

    batch_items = item.meta.get("batch_items")
    history_items = item.meta.get("history_items")
    if batch_items is not None or history_items is not None:
        if batch_items is None:
            batch_items = [{"id": item.item_id, "content": item.content}]
        if history_items is None:
            history_items = []
        result = analyze_dedup_in_memory(batch_items, history_items)
        score = max_duplicate_score(result)
        evidence.update(
            {
                "mode": "in_memory",
                "batch_high_sim_pairs": result.get("batch_high_sim_pairs", []),
                "batch_to_history": result.get("batch_to_history", []),
            }
        )
    elif _load_quality_agent_module():
        try:
            from agents.text_quality import analyze_dedup

            data_dir = Path(__file__).resolve().parents[3] / "modules" / "quality_agent" / "data"
            outputs_dir = Path(__file__).resolve().parents[3] / "modules" / "quality_agent" / "outputs"
            batch_path = Path(item.meta.get("batch_path", data_dir / "batch_notes.json"))
            history_path = Path(item.meta.get("history_path", data_dir / "history_notes.json"))
            output_path = Path(item.meta.get("output_path", settings.QUALITY_OUTPUT_PATH))

            analyze_dedup(str(batch_path), str(history_path), str(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            scores = [x.get("max_duplicate_score", 0.0) for x in result.get("batch_to_history", [])]
            score = max(scores) if scores else 0.0
            evidence.update(
                {
                    "mode": "file",
                    "output": str(output_path),
                    "batch_path": str(batch_path),
                    "history_path": str(history_path),
                }
            )
        except Exception as exc:
            evidence.update({"error": str(exc)})

    risk = "low"
    if score >= settings.QUALITY_HIGH_THRESHOLD:
        risk = "high"
    elif score >= settings.QUALITY_MEDIUM_THRESHOLD:
        risk = "medium"

    return QualitySignal(risk_level=risk, duplicate_score=score, evidence=evidence)
