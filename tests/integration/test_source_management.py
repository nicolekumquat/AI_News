"""Integration test for full source management lifecycle (TDD — write first, verify FAIL)."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from models.news_source import NewsSource


# Minimal built-in for testing
_TEST_BUILTINS = [
    NewsSource(
        source_id="hackernews",
        name="HackerNews",
        fetch_method="api",
        url="https://hn.algolia.com/api/v1/search_by_date",
        enabled=True,
    ),
    NewsSource(
        source_id="arxiv",
        name="ArXiv AI/ML",
        fetch_method="api",
        url="http://export.arxiv.org/api/query",
        enabled=True,
    ),
]


class TestSourceManagementLifecycle:
    """T016: Full add → list → disable → enable → remove → list lifecycle."""

    def test_full_lifecycle(self, tmp_path):
        config_json = tmp_path / "config.json"
        initial_config = {
            "sources": {
                "enabled": ["hackernews", "arxiv"],
                "custom": [],
            },
        }
        config_json.write_text(json.dumps(initial_config), encoding="utf-8")

        with (
            patch("services.source_manager.get_default_sources", return_value=_TEST_BUILTINS),
            patch("config.loader._CONFIG_DIR", tmp_path),
            patch("config.loader._JSON_PATH", config_json),
            patch("config.loader._TOML_PATH", tmp_path / "config.toml"),
        ):
            from services.source_manager import (
                add_source,
                disable_source,
                enable_source,
                list_sources,
                remove_source,
            )

            # 1. Add a custom source
            result = add_source(
                name="Test Blog",
                url="https://test.com/feed.xml",
                method="rss",
            )
            assert "error" not in result
            assert result["source_id"] == "test-blog"

            # 2. List — should include the new source
            sources = list_sources()
            ids = [s["source_id"] for s in sources]
            assert "test-blog" in ids

            # 3. Disable hackernews
            result = disable_source("hackernews")
            assert "error" not in result

            # 4. Verify disabled
            sources = list_sources()
            hn = [s for s in sources if s["source_id"] == "hackernews"][0]
            assert hn["enabled"] is False

            # 5. Re-enable
            result = enable_source("hackernews")
            assert "error" not in result

            # 6. Remove custom source
            result = remove_source("test-blog")
            assert "error" not in result

            # 7. Verify gone
            sources = list_sources()
            ids = [s["source_id"] for s in sources]
            assert "test-blog" not in ids

            # 8. Verify config persisted correctly
            saved = json.loads(config_json.read_text(encoding="utf-8"))
            custom_ids = [c["source_id"] for c in saved["sources"].get("custom", [])]
            assert "test-blog" not in custom_ids
