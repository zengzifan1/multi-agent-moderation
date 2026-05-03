from ..schemas import ModerationItem, ComplianceSignal
from ..tools import compliance_tool


class ComplianceAgent:
    def run(self, item: ModerationItem) -> ComplianceSignal:
        return compliance_tool(item)
