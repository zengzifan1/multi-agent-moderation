from multi_agent_moderation.schemas import ModerationItem
from multi_agent_moderation.chains.langgraph_orchestrator import LangGraphOrchestrator
from multi_agent_moderation.configs import settings


def main() -> None:
    item = ModerationItem(
        item_id="demo-graph-1",
        content="This is the best deal, totally free.",
        source="demo",
        meta={"title": "Sample Title", "kb_path": settings.COMPLIANCE_KB_PATH},
    )
    result = LangGraphOrchestrator().run(item)
    print(result)


if __name__ == "__main__":
    main()
