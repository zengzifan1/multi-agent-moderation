import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .configs import settings

_MODEL: Optional[SentenceTransformer] = None


def _get_model(model_dir: Optional[str] = None) -> SentenceTransformer:
    global _MODEL
    if _MODEL is not None and model_dir is None:
        return _MODEL

    default_path = settings.BASE_DIR / "modules/quality_agent/models/bge-base-zh-v1.5"
    model_path = Path(model_dir or os.getenv("QUALITY_AGENT_MODEL_DIR") or default_path)
    if not model_path.exists():
        raise FileNotFoundError(
            "Model files not found. Set QUALITY_AGENT_MODEL_DIR or download "
            "the model into modules/quality_agent/models/bge-base-zh-v1.5."
        )
    model = SentenceTransformer(str(model_path))
    if model_dir is None:
        _MODEL = model
    return model


def _normalize_similarity(sim: np.ndarray) -> np.ndarray:
    return np.where(sim < 0, (sim + 1) / 2, sim)


def analyze_dedup_in_memory(
    batch_items: List[Dict[str, str]],
    history_items: List[Dict[str, str]],
    model_dir: Optional[str] = None,
    threshold: float = 0.9,
) -> Dict[str, List[Dict[str, object]]]:
    if not batch_items:
        return {"batch_high_sim_pairs": [], "batch_to_history": []}

    batch_texts = [item.get("content", "") for item in batch_items]
    history_texts = [item.get("content", "") for item in history_items]

    model = _get_model(model_dir)
    batch_embs = model.encode(batch_texts, show_progress_bar=False, batch_size=32)
    history_embs = model.encode(history_texts, show_progress_bar=False, batch_size=32) if history_texts else None

    batch_high_sim_pairs: List[Dict[str, object]] = []
    if len(batch_items) > 1:
        sim_matrix = _normalize_similarity(cosine_similarity(batch_embs, batch_embs))
        n = len(batch_items)
        for i in range(n):
            for j in range(i + 1, n):
                score = float(sim_matrix[i][j])
                if score >= threshold:
                    batch_high_sim_pairs.append(
                        {
                            "batch_id1": batch_items[i].get("id") or batch_items[i].get("item_id"),
                            "batch_id2": batch_items[j].get("id") or batch_items[j].get("item_id"),
                            "duplicate_score": score,
                        }
                    )

    batch_to_history: List[Dict[str, object]] = []
    if history_embs is not None and len(history_items) > 0:
        for item, emb in zip(batch_items, batch_embs):
            scores = _normalize_similarity(cosine_similarity([emb], history_embs)[0])
            max_idx = int(np.argmax(scores))
            max_score = float(scores[max_idx])
            batch_to_history.append(
                {
                    "batch_id": item.get("id") or item.get("item_id"),
                    "most_similar_history_id": history_items[max_idx].get("id") or history_items[max_idx].get("item_id"),
                    "max_duplicate_score": max_score,
                }
            )

    return {
        "batch_high_sim_pairs": batch_high_sim_pairs,
        "batch_to_history": batch_to_history,
    }


def max_duplicate_score(result: Dict[str, List[Dict[str, object]]]) -> float:
    scores = [x.get("max_duplicate_score", 0.0) for x in result.get("batch_to_history", [])]
    return float(max(scores)) if scores else 0.0
