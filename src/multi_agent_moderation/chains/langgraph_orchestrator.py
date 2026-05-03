from typing import TypedDict, List

from ..agents import QualityAgent, ComplianceAgent, ReviewAgent
from ..configs import settings
from ..schemas import (
    ModerationItem,
    ModerationResult,
    QualitySignal,
    ComplianceSignal,
    ReviewDecision,
    moderation_result_to_dict,
)


class ModerationState(TypedDict, total=False):
    item: ModerationItem
    quality: QualitySignal
    compliance: ComplianceSignal
    review: ReviewDecision
    final_action: str


def _import_langgraph() -> tuple[object, object]:
    try:
        from langgraph.graph import StateGraph, END
    except Exception as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "langgraph is required for LangGraphOrchestrator. "
            "Install with `pip install langgraph`."
        ) from exc
    return StateGraph, END


def _decide_action(compliance: ComplianceSignal, review: ReviewDecision) -> str:
    action = settings.DEFAULT_ACTION
    action_hint = compliance.evidence.get("action_hint", "allow")
    if action_hint == settings.BLOCK_ACTION:
        return settings.BLOCK_ACTION
    if action_hint == settings.REVIEW_ACTION or review.action == settings.REVIEW_ACTION or review.need_review:
        return settings.REVIEW_ACTION
    if compliance.labels and any(label in settings.COMPLIANCE_BLOCK_LABELS for label in compliance.labels):
        return settings.BLOCK_ACTION
    return action


class LangGraphOrchestrator:
    def __init__(self) -> None:
        self.quality_agent = QualityAgent()
        self.compliance_agent = ComplianceAgent()
        self.review_agent = ReviewAgent()
        self._graph = None

    def _quality_node(self, state: ModerationState) -> dict:
        return {"quality": self.quality_agent.run(state["item"])}

    def _compliance_node(self, state: ModerationState) -> dict:
        return {"compliance": self.compliance_agent.run(state["item"])}

    def _review_node(self, state: ModerationState) -> dict:
        return {
            "review": self.review_agent.run(state["quality"], state["compliance"])
        }

    def _decide_node(self, state: ModerationState) -> dict:
        action = _decide_action(state["compliance"], state["review"])
        return {"final_action": action}

    def _build_graph(self) -> object:
        StateGraph, END = _import_langgraph()
        graph = StateGraph(ModerationState)
        graph.add_node("quality", self._quality_node)
        graph.add_node("compliance", self._compliance_node)
        graph.add_node("review", self._review_node)
        graph.add_node("decide", self._decide_node)
        graph.set_entry_point("quality")
        graph.add_edge("quality", "compliance")
        graph.add_edge("compliance", "review")
        graph.add_edge("review", "decide")
        graph.add_edge("decide", END)
        return graph.compile()

    def run(self, item: ModerationItem) -> ModerationResult:
        if self._graph is None:
            self._graph = self._build_graph()

        result = self._graph.invoke({"item": item})
        return ModerationResult(
            item_id=item.item_id,
            final_action=result["final_action"],
            quality=result["quality"],
            compliance=result["compliance"],
            review=result["review"],
        )

    def run_dict(self, item: ModerationItem) -> dict:
        return moderation_result_to_dict(self.run(item))

    def run_batch(self, items: List[ModerationItem]) -> List[ModerationResult]:
        return [self.run(item) for item in items]

    def run_batch_dict(self, items: List[ModerationItem]) -> List[dict]:
        return [moderation_result_to_dict(result) for result in self.run_batch(items)]
