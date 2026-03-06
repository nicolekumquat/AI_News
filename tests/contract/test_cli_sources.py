"""Contract tests for CLI sources subcommands (TDD — write first, verify FAIL)."""

import subprocess
import sys
import pytest
from unittest.mock import patch, MagicMock


def run_cli(*args):
    """Helper: run ai-digest CLI and capture output."""
    from cli.commands import parse_args
    return parse_args(list(args))


class TestSourcesListContract:
    """T012: Contract test for `ai-digest sources list` output format."""

    def test_list_parses_correctly(self):
        parsed = run_cli("sources", "list")
        assert parsed.command == "sources"
        assert parsed.sources_action == "list"

    @patch("services.source_manager.load_config")
    @patch("services.source_manager.get_default_sources")
    def test_list_output_contains_status_indicators(self, mock_defaults, mock_config, capsys):
        from services.source_manager import list_sources
        from cli.formatter import format_sources_list
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
        output = format_sources_list(sources)
        assert "✓" in output or "✗" in output
        assert "hackernews" in output


class TestSourcesAddContract:
    """T013: Contract test for `ai-digest sources add` success and error cases."""

    def test_add_parses_all_args(self):
        parsed = run_cli("sources", "add", "--name", "Test Blog", "--url", "https://test.com/feed.xml", "--method", "rss")
        assert parsed.command == "sources"
        assert parsed.sources_action == "add"
        assert parsed.name == "Test Blog"
        assert parsed.url == "https://test.com/feed.xml"
        assert parsed.method == "rss"

    def test_add_method_defaults_to_rss(self):
        parsed = run_cli("sources", "add", "--name", "Test Blog", "--url", "https://test.com/feed.xml")
        assert parsed.method == "rss"

    def test_add_invalid_method_rejected_by_argparse(self):
        with pytest.raises(SystemExit):
            run_cli("sources", "add", "--name", "Bad", "--url", "https://x.com/feed", "--method", "xml")


class TestSourcesRemoveContract:
    """T014: Contract test for `ai-digest sources remove`."""

    def test_remove_parses_source_id(self):
        parsed = run_cli("sources", "remove", "my-blog")
        assert parsed.command == "sources"
        assert parsed.sources_action == "remove"
        assert parsed.source_id == "my-blog"


class TestSourcesEnableDisableContract:
    """T015: Contract test for `ai-digest sources enable/disable`."""

    def test_enable_parses_source_id(self):
        parsed = run_cli("sources", "enable", "hackernews")
        assert parsed.command == "sources"
        assert parsed.sources_action == "enable"
        assert parsed.source_id == "hackernews"

    def test_disable_parses_source_id(self):
        parsed = run_cli("sources", "disable", "hackernews")
        assert parsed.command == "sources"
        assert parsed.sources_action == "disable"
        assert parsed.source_id == "hackernews"
