import json
from pathlib import Path

from core import review_decision


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    sample_path = root / "data" / "sample_inputs.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    rules_path = root / "data" / "replacement_rules.json"
    result = review_decision(payload.get("compliance", {}), payload.get("quality", {}), rules_path=str(rules_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
