"""Configuration loader - loads config from TOML or JSON files with merge support."""

import copy
import json
import shutil
import tomllib
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path.home() / ".ai-digest"
_JSON_PATH = _CONFIG_DIR / "config.json"
_TOML_PATH = _CONFIG_DIR / "config.toml"


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load configuration with TOML base + JSON override merge.

    If both config.toml and config.json exist, TOML provides base settings
    and JSON overrides sources.enabled and sources.custom per config-schema.md.

    Args:
        config_path: Explicit path (skips merge logic). None = auto-detect.

    Returns:
        Merged configuration dictionary
    """
    if config_path is not None:
        return _normalize_sources(_load_single(config_path))

    toml_exists = _TOML_PATH.exists()
    json_exists = _JSON_PATH.exists()

    if toml_exists and json_exists:
        base = _load_single(_TOML_PATH)
        overrides = _load_single(_JSON_PATH)
        return _normalize_sources(_merge_configs(base, overrides))

    if toml_exists:
        return _normalize_sources(_load_single(_TOML_PATH))

    if json_exists:
        return _normalize_sources(_load_single(_JSON_PATH))

    # No config file — return defaults
    return _get_default_config()


def _normalize_sources(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy sources format (flat list) to new dict format.

    Legacy: {"sources": [{"source_id": "x", "enabled": true, ...}, ...]}
    New:    {"sources": {"enabled": ["x", ...], "custom": [...]}}
    """
    sources = config.get("sources")
    if not isinstance(sources, list):
        return config

    from .sources import get_default_sources

    builtin_ids = {s.source_id for s in get_default_sources()}
    enabled = []
    custom = []

    for s in sources:
        sid = s.get("source_id", "")
        if s.get("enabled", True):
            enabled.append(sid)
        if sid not in builtin_ids:
            custom.append({
                "source_id": sid,
                "name": s.get("name", sid),
                "fetch_method": s.get("fetch_method", "rss"),
                "url": s.get("url", ""),
            })

    config["sources"] = {"enabled": enabled, "custom": custom}
    return config


def _load_single(path: Path) -> dict[str, Any]:
    """Load a single TOML or JSON config file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    if path.suffix == ".toml":
        with open(path, "rb") as f:
            return tomllib.load(f)
    elif path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}. Use .toml or .json")


def _merge_configs(base: dict, overrides: dict) -> dict[str, Any]:
    """Merge TOML base with JSON overrides (sources.enabled and sources.custom)."""
    merged = copy.deepcopy(base)
    if "sources" in overrides:
        merged.setdefault("sources", {})
        if "enabled" in overrides["sources"]:
            merged["sources"]["enabled"] = overrides["sources"]["enabled"]
        if "custom" in overrides["sources"]:
            merged["sources"]["custom"] = overrides["sources"]["custom"]
    if "podcast" in overrides:
        merged["podcast"] = overrides["podcast"]
    return merged


def save_config(config: dict[str, Any]) -> Path:
    """
    Save configuration to ~/.ai-digest/config.json.

    Per config-schema.md Config Write Contract:
    1. Read current config (already done by caller)
    2. Modify in-memory (already done by caller)
    3. Backup existing config.json to config.json.bak
    4. Write to config.json via stdlib json

    Returns:
        Path to the written config file
    """
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Backup existing JSON if present
    if _JSON_PATH.exists():
        shutil.copy2(_JSON_PATH, _JSON_PATH.with_suffix(".json.bak"))

    with open(_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return _JSON_PATH


def get_json_config_path() -> Path:
    """Get the JSON config path used for programmatic writes."""
    return _JSON_PATH


def get_default_config_path() -> Path:
    """Get default config path (~/.ai-digest/config.toml)."""
    return _TOML_PATH


def _get_default_config() -> dict[str, Any]:
    """Return built-in default configuration."""
    from .sources import get_default_sources

    return {
        "sources": {
            "enabled": [s.source_id for s in get_default_sources()],
            "custom": [],
        },
        "cache": {
            "directory": str(_CONFIG_DIR / "cache"),
            "retention_days": 30,
        },
        "fetcher": {
            "timeout_seconds": 30,
            "max_retries": 3,
            "retry_delays": [1, 2, 4],
            "user_agent": "ai-daily-digest/1.0 (local CLI tool)",
        },
        "summarizer": {
            "compression_ratio": 0.5,
            "min_sentence_length": 5,
            "stopwords_enabled": True,
        },
        "deduplicator": {
            "similarity_threshold": 0.75,
            "compare_title": True,
            "compare_content": True,
        },
        "podcast": {
            "default_model": "base",
            "cleanup_audio": True,
            "max_duration_seconds": 7200,
        },
    }


def ensure_config_exists() -> Path:
    """
    Ensure config file exists, create with defaults if missing.

    Returns:
        Path to config file
    """
    if _TOML_PATH.exists():
        return _TOML_PATH

    if _JSON_PATH.exists():
        return _JSON_PATH

    # Neither exists — create default JSON
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    default_config = _get_default_config()
    with open(_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)

    return _JSON_PATH
