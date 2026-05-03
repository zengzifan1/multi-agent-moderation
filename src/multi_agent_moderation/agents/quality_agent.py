from ..schemas import ModerationItem, QualitySignal
from ..tools import quality_tool


class QualityAgent:
    def run(self, item: ModerationItem) -> QualitySignal:
        return quality_tool(item)
