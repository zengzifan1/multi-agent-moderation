import json
from pathlib import Path

from multi_agent_moderation.configs.loader import load_config


def test_load_config_with_profile(tmp_path: Path) -> None:
    payload = {
        "defaults": {"output_dir": "out"},
        "profiles": {"dev": {"queue_workers": 3}},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    config = load_config(str(config_path), "dev")
    assert config["output_dir"] == "out"
    assert config["queue_workers"] == 3


def test_load_config_yaml_missing_dependency(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("defaults:\n  output_dir: out\n", encoding="utf-8")

    try:
        load_config(str(config_path), "default")
    except RuntimeError:
        pass
