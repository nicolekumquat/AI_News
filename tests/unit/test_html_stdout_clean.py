"""Tests for BUG-001: HTML output must not contain logging/stdout noise."""

import logging
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest


class TestLoggingGoesToStderr:
    """Console log handler must write to stderr, not stdout."""

    def test_console_handler_uses_stderr(self, tmp_path):
        from config.logging import setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)

        root = logging.getLogger()
        stream_handlers = [
            h for h in root.handlers if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) == 1
        assert stream_handlers[0].stream is sys.stderr

    def test_log_messages_do_not_appear_on_stdout(self, tmp_path):
        from config.logging import setup_logging

        log_file = tmp_path / "test.log"
        captured_stdout = StringIO()

        old_stdout = sys.stdout
        sys.stdout = captured_stdout
        try:
            setup_logging(log_file=log_file)
            logger = logging.getLogger("test.stdout_check")
            logger.info("This should NOT appear on stdout")
            logger.warning("Neither should this")
        finally:
            sys.stdout = old_stdout

        stdout_output = captured_stdout.getvalue()
        assert "This should NOT appear on stdout" not in stdout_output
        assert "Neither should this" not in stdout_output

    def test_log_messages_appear_on_stderr(self, tmp_path):
        from config.logging import setup_logging

        log_file = tmp_path / "test.log"
        captured_stderr = StringIO()

        old_stderr = sys.stderr
        sys.stderr = captured_stderr
        try:
            setup_logging(log_file=log_file)
            logger = logging.getLogger("test.stderr_check")
            logger.info("This SHOULD appear on stderr")
        finally:
            sys.stderr = old_stderr

        stderr_output = captured_stderr.getvalue()
        assert "This SHOULD appear on stderr" in stderr_output


class TestHtmlOutputClean:
    """When --html is used, stdout must contain only valid HTML."""

    @patch("cli.__main__.fetch_all_sources")
    @patch("cli.__main__.generate_digest")
    @patch("cli.__main__.CacheService")
    @patch("cli.__main__.ensure_config_exists")
    @patch("cli.__main__.load_config")
    @patch("cli.__main__.get_default_sources")
    def test_html_stdout_starts_with_html_tag(
        self, mock_sources, mock_config, mock_ensure, mock_cache_cls,
        mock_generate, mock_fetch, tmp_path, monkeypatch
    ):
        from models.news_article import NewsArticle
        from models.digest import Digest
        from models.digest_entry import DigestEntry
        from datetime import datetime

        # Setup mocks
        mock_config.return_value = {}
        mock_ensure.return_value = str(tmp_path / "config.yaml")
        mock_sources.return_value = []

        cache_instance = MagicMock()
        cache_instance.load_digest.return_value = None
        cache_instance.is_digest_fresh.return_value = False
        mock_cache_cls.return_value = cache_instance

        article = NewsArticle(
            article_id="test-1",
            title="Test Article About AI",
            url="https://example.com/test",
            source_id="test",
            published_at=datetime(2026, 3, 6, 12, 0, 0),
            fetched_at=datetime(2026, 3, 6, 12, 0, 0),
            content="A test article summary that is long enough to pass validation requirements for content.",
        )
        mock_fetch.return_value = ([article], ["test"], [])

        digest = Digest(
            digest_id="2026-03-06",
            date=datetime(2026, 3, 6).date(),
            entries=["entry-1"],
            total_articles_fetched=1,
            total_articles_curated=1,
            duplicates_removed=0,
            sources_fetched=["test"],
            sources_failed=[],
            created_at=datetime(2026, 3, 6, 12, 0, 0),
        )
        entry = DigestEntry(
            entry_id="entry-1",
            article_id="test-1",
            summary="Test summary of an AI article.",
            summary_method="frequency",
            compression_ratio=0.3,
            processed_at=datetime(2026, 3, 6, 12, 0, 0),
        )
        mock_generate.return_value = (digest, [entry])

        # Capture stdout
        captured_stdout = StringIO()
        old_stdout = sys.stdout

        # Mock sys.argv for --html and patch sys.exit
        monkeypatch.setattr("sys.argv", ["ai-digest", "--html"])
        sys.stdout = captured_stdout
        try:
            from cli.__main__ import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        finally:
            sys.stdout = old_stdout

        html_output = captured_stdout.getvalue()
        stripped = html_output.lstrip()
        assert stripped.startswith("<!DOCTYPE") or stripped.startswith("<html"), \
            f"HTML output must start with HTML tag, got: {stripped[:100]}"

        # Verify no log lines leaked into stdout
        for line in html_output.splitlines():
            assert not line.startswith("INFO:"), f"Log line found in stdout: {line}"
            assert not line.startswith("WARNING:"), f"Log line found in stdout: {line}"
            assert not line.startswith("ERROR:"), f"Log line found in stdout: {line}"
            assert not line.startswith("DEBUG:"), f"Log line found in stdout: {line}"
