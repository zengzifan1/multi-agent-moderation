import json
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def load_config(path: Optional[str], profile: Optional[str] = None) -> Dict[str, object]:
    if not path:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        return {}

    if config_path.suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("pyyaml is required for YAML config files")
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    else:
        raw = json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        return {}

    defaults = raw.get("defaults") or raw.get("default") or {}
    profiles = raw.get("profiles") or {}
    if profile and profile in profiles:
        merged = {**defaults, **(profiles.get(profile) or {})}
        return merged

    if "profiles" in raw:
        return defaults
    return raw
