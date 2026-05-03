from typing import List

from ..schemas import ModerationItem, ModerationResult, moderation_result_to_dict
from ..configs import settings
from ..agents import QualityAgent, ComplianceAgent, ReviewAgent


class Orchestrator:
    def __init__(self) -> None:
        self.quality_agent = QualityAgent()
        self.compliance_agent = ComplianceAgent()
        self.review_agent = ReviewAgent()

    def run(self, item: ModerationItem) -> ModerationResult:
        quality = self.quality_agent.run(item)
        compliance = self.compliance_agent.run(item)
        review = self.review_agent.run(quality, compliance)

        action = settings.DEFAULT_ACTION
        action_hint = compliance.evidence.get("action_hint", "allow")
        if action_hint == settings.BLOCK_ACTION:
            action = settings.BLOCK_ACTION
        elif action_hint == settings.REVIEW_ACTION or review.action == settings.REVIEW_ACTION or review.need_review:
            action = settings.REVIEW_ACTION
        elif compliance.labels and any(label in settings.COMPLIANCE_BLOCK_LABELS for label in compliance.labels):
            action = settings.BLOCK_ACTION

        return ModerationResult(
            item_id=item.item_id,
            final_action=action,
            quality=quality,
            compliance=compliance,
            review=review,
        )

    def run_dict(self, item: ModerationItem) -> dict:
        return moderation_result_to_dict(self.run(item))

    def run_batch(self, items: List[ModerationItem]) -> List[ModerationResult]:
        return [self.run(item) for item in items]

    def run_batch_dict(self, items: List[ModerationItem]) -> List[dict]:
        return [moderation_result_to_dict(result) for result in self.run_batch(items)]
