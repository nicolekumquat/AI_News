"""Source management service — CRUD operations for news sources."""

import re

from config.loader import load_config, save_config
from config.sources import get_default_sources


def generate_source_id(name: str, existing_ids: set[str] | None = None) -> str:
    """Generate a slug-style source ID from a display name.

    Args:
        name: Human-readable source name
        existing_ids: Set of IDs to check uniqueness against

    Returns:
        Unique lowercase-hyphenated ID
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")

    if existing_ids is None:
        return slug

    if slug not in existing_ids:
        return slug

    counter = 2
    while f"{slug}-{counter}" in existing_ids:
        counter += 1
    return f"{slug}-{counter}"


def _get_all_source_ids(config: dict) -> set[str]:
    """Collect all source IDs (built-in + custom)."""
    builtin_ids = {s.source_id for s in get_default_sources()}
    custom_ids = {c["source_id"] for c in config.get("sources", {}).get("custom", [])}
    return builtin_ids | custom_ids


def _get_builtin_ids() -> set[str]:
    return {s.source_id for s in get_default_sources()}


def _find_source_name(source_id: str, config: dict) -> str | None:
    """Look up the display name for a source ID."""
    for s in get_default_sources():
        if s.source_id == source_id:
            return s.name
    for c in config.get("sources", {}).get("custom", []):
        if c["source_id"] == source_id:
            return c["name"]
    return None


def list_sources() -> list[dict]:
    """List all sources (built-in + custom) with enabled status.

    Returns:
        Sorted list of dicts with keys: source_id, name, fetch_method, url, enabled, is_builtin
    """
    config = load_config()
    enabled_list = config.get("sources", {}).get("enabled", [])
    custom_list = config.get("sources", {}).get("custom", [])

    sources: list[dict] = []

    # Built-in sources
    for s in get_default_sources():
        sources.append({
            "source_id": s.source_id,
            "name": s.name,
            "fetch_method": s.fetch_method,
            "url": s.url,
            "enabled": s.source_id in enabled_list,
            "is_builtin": True,
        })

    # Custom sources
    for c in custom_list:
        sources.append({
            "source_id": c["source_id"],
            "name": c["name"],
            "fetch_method": c.get("fetch_method", "rss"),
            "url": c["url"],
            "enabled": c["source_id"] in enabled_list,
            "is_builtin": False,
        })

    return sorted(sources, key=lambda s: (not s["is_builtin"], s["source_id"]))


def add_source(name: str, url: str, method: str = "rss") -> dict:
    """Add a new custom source.

    Returns:
        Dict with source_id, name, url, method on success; or error key on failure.
    """
    # Validate URL
    if not url.startswith(("http://", "https://")):
        return {"error": f"Invalid URL: {url}\nURL must start with http:// or https://"}

    # Validate method
    if method not in ("rss", "api", "html"):
        return {"error": f"Invalid fetch method: {method}\nValid methods: rss, api, html"}

    config = load_config()
    all_ids = _get_all_source_ids(config)

    source_id = generate_source_id(name)

    if source_id in all_ids:
        return {
            "error": (
                f"Source ID '{source_id}' already exists.\n"
                "Use a different name or remove the existing source first."
            )
        }

    # Append to config
    sources = config.setdefault("sources", {})
    custom = sources.setdefault("custom", [])
    enabled = sources.setdefault("enabled", [])

    custom.append({
        "source_id": source_id,
        "name": name,
        "fetch_method": method,
        "url": url,
    })
    enabled.append(source_id)

    save_config(config)
    return {"source_id": source_id, "name": name, "url": url, "method": method}


def remove_source(source_id: str) -> dict:
    """Remove a custom source. Built-in sources cannot be removed.

    Returns:
        Dict with source_id, name on success; or error key on failure.
    """
    config = load_config()
    builtin_ids = _get_builtin_ids()

    if source_id in builtin_ids:
        return {
            "error": f"Cannot remove built-in source '{source_id}'.\n"
                     f"Use 'ai-digest sources disable {source_id}' to disable it instead."
        }

    custom_list = config.get("sources", {}).get("custom", [])
    target = None
    for c in custom_list:
        if c["source_id"] == source_id:
            target = c
            break

    if target is None:
        return {
            "error": (
                f"Source '{source_id}' not found.\n"
                "Run 'ai-digest sources list' to see available sources."
            )
        }

    custom_list.remove(target)
    enabled = config.get("sources", {}).get("enabled", [])
    if source_id in enabled:
        enabled.remove(source_id)

    save_config(config)
    return {"source_id": source_id, "name": target["name"]}


def enable_source(source_id: str) -> dict:
    """Enable a source.

    Returns:
        Dict with source_id, name on success; already=True if no-op; or error key.
    """
    config = load_config()
    all_ids = _get_all_source_ids(config)

    if source_id not in all_ids:
        return {
            "error": (
                f"Source '{source_id}' not found.\n"
                "Run 'ai-digest sources list' to see available sources."
            )
        }

    enabled = config.setdefault("sources", {}).setdefault("enabled", [])
    if source_id in enabled:
        name = _find_source_name(source_id, config)
        return {"source_id": source_id, "name": name, "already": True}

    enabled.append(source_id)
    save_config(config)
    name = _find_source_name(source_id, config)
    return {"source_id": source_id, "name": name}


def disable_source(source_id: str) -> dict:
    """Disable a source.

    Returns:
        Dict with source_id, name on success; already=True if no-op; or error key.
    """
    config = load_config()
    all_ids = _get_all_source_ids(config)

    if source_id not in all_ids:
        return {
            "error": (
                f"Source '{source_id}' not found.\n"
                "Run 'ai-digest sources list' to see available sources."
            )
        }

    enabled = config.setdefault("sources", {}).setdefault("enabled", [])

    if source_id not in enabled:
        name = _find_source_name(source_id, config)
        return {"source_id": source_id, "name": name, "already": True}

    # Last-source guard
    if len(enabled) <= 1:
        return {"error": f"Cannot disable '{source_id}' — at least one source must remain enabled."}

    enabled.remove(source_id)
    save_config(config)
    name = _find_source_name(source_id, config)
    return {"source_id": source_id, "name": name}
