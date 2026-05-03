from ..schemas import QualitySignal, ComplianceSignal, ReviewDecision
from ..tools import review_tool


class ReviewAgent:
    def run(self, quality: QualitySignal, compliance: ComplianceSignal) -> ReviewDecision:
        return review_tool(quality, compliance)
