"""Unit tests for source management service (TDD — write first, verify FAIL)."""

import pytest
from unittest.mock import patch, MagicMock


class TestGenerateSourceId:
    """T007: Unit tests for generate_source_id() slug generation."""

    def test_basic_name_to_slug(self):
        from services.source_manager import generate_source_id

        assert generate_source_id("My AI Blog") == "my-ai-blog"

    def test_strips_non_alphanumeric(self):
        from services.source_manager import generate_source_id

        assert generate_source_id("Sam's Blog!") == "sams-blog"

    def test_collapses_multiple_hyphens(self):
        from services.source_manager import generate_source_id

        assert generate_source_id("Some --- Blog") == "some-blog"

    def test_strips_leading_trailing_hyphens(self):
        from services.source_manager import generate_source_id

        assert generate_source_id("  My Blog  ") == "my-blog"

    def test_uniqueness_check_appends_suffix(self):
        from services.source_manager import generate_source_id

        existing = {"my-blog"}
        result = generate_source_id("My Blog", existing_ids=existing)
        assert result == "my-blog-2"

    def test_uniqueness_check_increments(self):
        from services.source_manager import generate_source_id

        existing = {"my-blog", "my-blog-2"}
        result = generate_source_id("My Blog", existing_ids=existing)
        assert result == "my-blog-3"


class TestListSources:
    """T008: Unit tests for list_sources() merging built-in + custom with status."""

    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_returns_all_builtin_sources(self, mock_defaults, mock_config):
        from services.source_manager import list_sources
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {"enabled": ["hackernews"], "custom": []},
        }

        sources = list_sources()
        assert len(sources) == 1
        assert sources[0]["source_id"] == "hackernews"
        assert sources[0]["is_builtin"] is True

    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_includes_custom_sources(self, mock_defaults, mock_config):
        from services.source_manager import list_sources
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {
                "enabled": ["hackernews", "my-blog"],
                "custom": [
                    {
                        "source_id": "my-blog",
                        "name": "My Blog",
                        "fetch_method": "rss",
                        "url": "https://myblog.com/feed.xml",
                    },
                ],
            },
        }

        sources = list_sources()
        custom = [s for s in sources if not s["is_builtin"]]
        assert len(custom) == 1
        assert custom[0]["source_id"] == "my-blog"

    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_disabled_source_shows_disabled(self, mock_defaults, mock_config):
        from services.source_manager import list_sources
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
            NewsSource(
                source_id="arxiv",
                name="ArXiv",
                fetch_method="api",
                url="http://export.arxiv.org/api/query",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {"enabled": ["hackernews"], "custom": []},
        }

        sources = list_sources()
        arxiv = [s for s in sources if s["source_id"] == "arxiv"][0]
        assert arxiv["enabled"] is False


class TestAddSource:
    """T009: Unit tests for add_source()."""

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_add_valid_source(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import add_source
        from models.news_source import NewsSource

        mock_defaults.return_value = []
        mock_config.return_value = {"sources": {"enabled": [], "custom": []}}

        result = add_source(name="My Blog", url="https://myblog.com/feed.xml", method="rss")
        assert result["source_id"] == "my-blog"
        assert "error" not in result
        mock_save.assert_called_once()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_add_duplicate_id_rejected(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import add_source
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
        ]
        mock_config.return_value = {"sources": {"enabled": ["hackernews"], "custom": []}}

        result = add_source(name="HackerNews", url="https://other.com/feed", method="rss")
        assert "error" in result
        mock_save.assert_not_called()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_add_invalid_url_rejected(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import add_source

        mock_defaults.return_value = []
        mock_config.return_value = {"sources": {"enabled": [], "custom": []}}

        result = add_source(name="Bad Source", url="not-a-url", method="rss")
        assert "error" in result
        mock_save.assert_not_called()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_add_invalid_method_rejected(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import add_source

        mock_defaults.return_value = []
        mock_config.return_value = {"sources": {"enabled": [], "custom": []}}

        result = add_source(name="Bad Method", url="https://ok.com/feed", method="xml")
        assert "error" in result
        mock_save.assert_not_called()


class TestRemoveSource:
    """T010: Unit tests for remove_source()."""

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_remove_custom_source(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import remove_source

        mock_defaults.return_value = []
        mock_config.return_value = {
            "sources": {
                "enabled": ["my-blog"],
                "custom": [
                    {
                        "source_id": "my-blog",
                        "name": "My Blog",
                        "fetch_method": "rss",
                        "url": "https://myblog.com/feed.xml",
                    },
                ],
            },
        }

        result = remove_source("my-blog")
        assert "error" not in result
        assert result["source_id"] == "my-blog"
        mock_save.assert_called_once()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_remove_builtin_rejected(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import remove_source
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
        ]
        mock_config.return_value = {"sources": {"enabled": ["hackernews"], "custom": []}}

        result = remove_source("hackernews")
        assert "error" in result
        assert "disable" in result["error"].lower()
        mock_save.assert_not_called()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_remove_nonexistent(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import remove_source

        mock_defaults.return_value = []
        mock_config.return_value = {"sources": {"enabled": [], "custom": []}}

        result = remove_source("nonexistent")
        assert "error" in result
        mock_save.assert_not_called()


class TestEnableDisableSource:
    """T011: Unit tests for enable_source() and disable_source()."""

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_disable_source(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import disable_source
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
            NewsSource(
                source_id="arxiv",
                name="ArXiv",
                fetch_method="api",
                url="http://export.arxiv.org/api/query",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {"enabled": ["hackernews", "arxiv"], "custom": []},
        }

        result = disable_source("hackernews")
        assert "error" not in result
        assert result["source_id"] == "hackernews"
        mock_save.assert_called_once()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_enable_source(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import enable_source
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {"enabled": [], "custom": []},
        }

        result = enable_source("hackernews")
        assert "error" not in result
        mock_save.assert_called_once()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_disable_last_source_rejected(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import disable_source
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {"enabled": ["hackernews"], "custom": []},
        }

        result = disable_source("hackernews")
        assert "error" in result
        assert "at least one" in result["error"].lower()
        mock_save.assert_not_called()

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_enable_already_enabled(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import enable_source
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {"enabled": ["hackernews"], "custom": []},
        }

        result = enable_source("hackernews")
        assert result.get("already") is True

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_disable_already_disabled(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import disable_source
        from models.news_source import NewsSource

        mock_defaults.return_value = [
            NewsSource(
                source_id="hackernews",
                name="HackerNews",
                fetch_method="api",
                url="https://hn.algolia.com/api/v1/search_by_date",
                enabled=True,
            ),
            NewsSource(
                source_id="arxiv",
                name="ArXiv",
                fetch_method="api",
                url="http://export.arxiv.org/api/query",
                enabled=True,
            ),
        ]
        mock_config.return_value = {
            "sources": {"enabled": ["arxiv"], "custom": []},
        }

        result = disable_source("hackernews")
        assert result.get("already") is True

    @patch("services.source_manager.save_config")
    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_enable_nonexistent(self, mock_defaults, mock_config, mock_save):
        from services.source_manager import enable_source

        mock_defaults.return_value = []
        mock_config.return_value = {"sources": {"enabled": [], "custom": []}}

        result = enable_source("nonexistent")
        assert "error" in result
