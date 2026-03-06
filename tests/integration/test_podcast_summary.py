"""Integration test for full podcast pipeline (TDD — write first, verify FAIL)."""

import pytest
from unittest.mock import patch, MagicMock


class TestPodcastPipeline:
    """T035: Full download → transcribe → clean → summarize pipeline with mocks."""

    @patch("time.monotonic", side_effect=[0.0, 5.0])
    @patch("services.podcast_service._summarize_text")
    @patch("services.podcast_service._load_whisper_model")
    @patch("subprocess.run")
    def test_end_to_end_pipeline(self, mock_run, mock_load_model, mock_summarize_text, mock_time):
        from services.podcast_service import summarize_podcast

        # Mock yt-dlp download
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        # Mock whisper model
        mock_model = MagicMock()
        long_text = "This is a detailed transcript of a podcast episode about AI. " * 30
        segments = [MagicMock(text=long_text)]
        info = MagicMock(duration=3600.0)
        mock_model.transcribe.return_value = (segments, info)
        mock_load_model.return_value = mock_model

        # Mock summarization
        mock_summarize_text.return_value = "A concise summary."

        with patch("services.podcast_service._find_audio_file", return_value="/tmp/fake.wav"):
            with patch("services.podcast_service._cleanup_temp_dir"):
                result = summarize_podcast(
                    "https://example.com/episode.mp3",
                    model="tiny",
                )

        assert result.episode.url == "https://example.com/episode.mp3"
        assert result.summary_obj.model_size == "tiny"
        assert result.summary_obj.summary == "A concise summary."
        assert result.summary_obj.transcript_word_count > 0
        assert result.summary_obj.transcription_time_seconds > 0
