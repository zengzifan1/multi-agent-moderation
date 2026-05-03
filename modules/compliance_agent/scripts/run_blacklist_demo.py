import json
from pathlib import Path

from core import analyze_batch


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    sample_path = root / "data" / "sample_inputs.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    results = analyze_batch(items)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
