from multi_agent_moderation.schemas import ModerationItem
from multi_agent_moderation.chains import Orchestrator


def test_orchestrator_runs():
    item = ModerationItem(item_id="t1", content="test")
    result = Orchestrator().run(item)
    assert result.item_id == "t1"
