from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict


@dataclass
class ModerationItem:
    item_id: str
    content: str
    source: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict)


@dataclass
class QualitySignal:
    risk_level: str
    duplicate_score: float
    evidence: Dict[str, str] = field(default_factory=dict)


@dataclass
class ComplianceSignal:
    risk_level: str
    labels: List[str]
    evidence: Dict[str, object] = field(default_factory=dict)


@dataclass
class ReviewDecision:
    need_review: bool
    reason: str
    action: str = "review"
    review_payload: Dict[str, object] = field(default_factory=dict)
    decision_basis: Dict[str, object] = field(default_factory=dict)
    trace: Dict[str, object] = field(default_factory=dict)


@dataclass
class ModerationResult:
    item_id: str
    final_action: str
    quality: QualitySignal
    compliance: ComplianceSignal
    review: ReviewDecision


def moderation_result_to_dict(result: ModerationResult) -> Dict[str, object]:
    return asdict(result)
