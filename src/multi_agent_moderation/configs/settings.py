import os
from pathlib import Path

from .loader import load_config

QUALITY_HIGH_THRESHOLD = 0.9
QUALITY_MEDIUM_THRESHOLD = 0.75

COMPLIANCE_BLOCK_LABELS = {"spam", "scam", "illegal"}

DEFAULT_ACTION = "allow"
REVIEW_ACTION = "review"
BLOCK_ACTION = "block"

BASE_DIR = Path(__file__).resolve().parents[3]

_config_path = os.getenv("MAM_CONFIG_PATH")
_config_profile = os.getenv("MAM_PROFILE", "default")
_config = load_config(_config_path, _config_profile)


def _get_config_value(key: str, env_name: str, default):
	env_value = os.getenv(env_name)
	if env_value is not None:
		return env_value
	if key in _config:
		return _config[key]
	return default


def _get_bool(key: str, env_name: str, default: bool) -> bool:
	value = _get_config_value(key, env_name, default)
	if isinstance(value, bool):
		return value
	return str(value).lower() in {"1", "true", "yes"}


OUTPUT_DIR = Path(_get_config_value("output_dir", "MAM_OUTPUT_DIR", BASE_DIR / "outputs"))
AUDIT_LOG_PATH = Path(_get_config_value("audit_log_path", "MAM_AUDIT_LOG_PATH", OUTPUT_DIR / "audit_log.jsonl"))
ENABLE_AUDIT = _get_bool("enable_audit", "MAM_ENABLE_AUDIT", True)
AUDIT_DB_PATH = Path(_get_config_value("audit_db_path", "MAM_AUDIT_DB_PATH", OUTPUT_DIR / "audit.db"))
ENABLE_AUDIT_DB = _get_bool("enable_audit_db", "MAM_ENABLE_AUDIT_DB", True)
QUEUE_WORKERS = int(_get_config_value("queue_workers", "MAM_QUEUE_WORKERS", 2))
JOB_DB_PATH = Path(_get_config_value("job_db_path", "MAM_JOB_DB_PATH", OUTPUT_DIR / "jobs.db"))

# Relative paths (repo-root) for minimal RAG and review replacements
COMPLIANCE_KB_PATH = str(
	Path(
		_get_config_value(
			"compliance_kb_path",
			"MAM_COMPLIANCE_KB_PATH",
			BASE_DIR / "modules/compliance_agent/data/knowledge_base.json",
		)
	)
)
COMPLIANCE_RULES_PATH = str(
	Path(
		_get_config_value(
			"compliance_rules_path",
			"MAM_COMPLIANCE_RULES_PATH",
			BASE_DIR / "modules/compliance_agent/rules/rules.json",
		)
	)
)
REVIEW_REPLACEMENT_RULES_PATH = str(
	Path(
		_get_config_value(
			"review_replacement_rules_path",
			"MAM_REVIEW_REPLACEMENT_RULES_PATH",
			BASE_DIR / "modules/review_agent/data/replacement_rules.json",
		)
	)
)

QUALITY_OUTPUT_PATH = str(
	Path(_get_config_value("quality_output_path", "MAM_QUALITY_OUTPUT_PATH", OUTPUT_DIR / "quality_dedup.json"))
)
