"""Contract tests for CLI podcast subcommand (TDD — write first, verify FAIL)."""

import pytest
from unittest.mock import patch, MagicMock


def run_cli(*args):
    """Helper: run ai-digest CLI and capture output."""
    from cli.commands import parse_args
    return parse_args(list(args))


class TestPodcastOutputContract:
    """T033: Contract test for `ai-digest podcast <URL>` output format."""

    def test_podcast_parses_url(self):
        parsed = run_cli("podcast", "https://example.com/episode.mp3")
        assert parsed.command == "podcast"
        assert parsed.url == "https://example.com/episode.mp3"

    def test_podcast_default_model_is_none(self):
        parsed = run_cli("podcast", "https://example.com/episode.mp3")
        assert parsed.model is None  # resolved from config at runtime

    def test_podcast_model_flag(self):
        parsed = run_cli("podcast", "https://example.com/episode.mp3", "--model", "small")
        assert parsed.model == "small"

    def test_podcast_output_format(self):
        from cli.formatter import format_podcast_summary

        mock_result = MagicMock()
        mock_result.episode.title = "GPT-5 Deep Dive"
        mock_result.episode.source_name = "Latent Space Podcast"
        mock_result.episode.url = "https://www.latent.space/p/gpt5-analysis"
        mock_result.episode.duration_seconds = 3420
        mock_result.summary_obj.transcript_word_count = 8500
        mock_result.summary_obj.model_size = "base"
        mock_result.summary_obj.summary = "A summary of the episode."
        mock_result.summary_obj.compression_ratio = 0.053
        mock_result.summary_obj.transcription_time_seconds = 187.5

        output = format_podcast_summary(mock_result)
        assert "Podcast Summary" in output
        assert "GPT-5 Deep Dive" in output
        assert "Latent Space Podcast" in output
        assert "base" in output
        assert "A summary of the episode." in output


class TestPodcastErrorContract:
    """T034: Contract test for `ai-digest podcast` error cases."""

    def test_invalid_model_rejected_by_argparse(self):
        with pytest.raises(SystemExit):
            run_cli("podcast", "https://example.com/ep.mp3", "--model", "huge")
