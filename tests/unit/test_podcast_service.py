"""Unit tests for podcast service (TDD — write first, verify FAIL)."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


class TestPodcastEpisodeDataclass:
    """T026: Unit tests for PodcastEpisode dataclass validation."""

    def test_valid_episode(self):
        from models.podcast import PodcastEpisode

        ep = PodcastEpisode(
            url="https://example.com/episode.mp3",
            title="Test Episode",
        )
        assert ep.url == "https://example.com/episode.mp3"
        assert ep.title == "Test Episode"
        assert ep.episode_id  # UUID auto-generated

    def test_invalid_url_rejected(self):
        from models.podcast import PodcastEpisode

        with pytest.raises(ValueError, match="url"):
            PodcastEpisode(url="not-a-url", title="Test Episode")

    def test_short_title_rejected(self):
        from models.podcast import PodcastEpisode

        with pytest.raises(ValueError, match="title"):
            PodcastEpisode(url="https://example.com/ep.mp3", title="AB")

    def test_negative_duration_rejected(self):
        from models.podcast import PodcastEpisode

        with pytest.raises(ValueError, match="duration"):
            PodcastEpisode(
                url="https://example.com/ep.mp3",
                title="Test Episode",
                duration_seconds=-5,
            )


class TestPodcastSummaryDataclass:
    """T027: Unit tests for PodcastSummary dataclass validation."""

    def test_valid_summary(self):
        from models.podcast import PodcastSummary

        ps = PodcastSummary(
            episode_id="abc-123",
            transcript="x" * 200,
            transcript_word_count=8500,
            summary="A concise summary of the podcast episode content.",
            summary_word_count=450,
            compression_ratio=0.05,
            model_size="base",
            transcription_time_seconds=187.5,
        )
        assert ps.summary_id  # UUID auto-generated
        assert ps.compression_ratio == 0.05

    def test_short_transcript_rejected(self):
        from models.podcast import PodcastSummary

        with pytest.raises(ValueError, match="transcript"):
            PodcastSummary(
                episode_id="abc-123",
                transcript="too short",
                transcript_word_count=2,
                summary="A summary",
                summary_word_count=2,
                compression_ratio=0.05,
                model_size="base",
                transcription_time_seconds=10.0,
            )

    def test_empty_summary_rejected(self):
        from models.podcast import PodcastSummary

        with pytest.raises(ValueError, match="summary"):
            PodcastSummary(
                episode_id="abc-123",
                transcript="x" * 200,
                transcript_word_count=8500,
                summary="",
                summary_word_count=0,
                compression_ratio=0.05,
                model_size="base",
                transcription_time_seconds=10.0,
            )

    def test_invalid_compression_ratio(self):
        from models.podcast import PodcastSummary

        with pytest.raises(ValueError, match="compression_ratio"):
            PodcastSummary(
                episode_id="abc-123",
                transcript="x" * 200,
                transcript_word_count=8500,
                summary="A valid summary.",
                summary_word_count=450,
                compression_ratio=0.8,  # too high for podcasts
                model_size="base",
                transcription_time_seconds=10.0,
            )

    def test_invalid_model_size(self):
        from models.podcast import PodcastSummary

        with pytest.raises(ValueError, match="model_size"):
            PodcastSummary(
                episode_id="abc-123",
                transcript="x" * 200,
                transcript_word_count=8500,
                summary="A valid summary.",
                summary_word_count=450,
                compression_ratio=0.05,
                model_size="huge",
                transcription_time_seconds=10.0,
            )


class TestCheckPodcastDependencies:
    """T028: Unit tests for check_podcast_dependencies()."""

    @patch("shutil.which", return_value="/usr/bin/yt-dlp")
    def test_all_deps_present(self, mock_which):
        from services.podcast_service import check_podcast_dependencies

        with patch.dict("sys.modules", {"faster_whisper": MagicMock()}):
            errors = check_podcast_dependencies()
            assert errors == []

    @patch("shutil.which", return_value=None)
    def test_missing_ytdlp(self, mock_which):
        from services.podcast_service import check_podcast_dependencies

        with patch.dict("sys.modules", {"faster_whisper": MagicMock()}):
            errors = check_podcast_dependencies()
            assert any("yt-dlp" in e for e in errors)

    @patch("shutil.which", return_value="/usr/bin/yt-dlp")
    def test_missing_faster_whisper(self, mock_which):
        from services.podcast_service import check_podcast_dependencies

        import sys
        saved = sys.modules.get("faster_whisper")
        sys.modules["faster_whisper"] = None  # simulate import failure
        try:
            errors = check_podcast_dependencies()
            assert any("faster-whisper" in e or "faster_whisper" in e for e in errors)
        finally:
            if saved is not None:
                sys.modules["faster_whisper"] = saved
            else:
                sys.modules.pop("faster_whisper", None)


class TestDownloadPodcastAudio:
    """T029: Unit tests for download_podcast_audio()."""

    @patch("services.podcast_service._find_audio_file", return_value="/tmp/test/audio.wav")
    @patch("subprocess.run")
    def test_download_success(self, mock_run, mock_find):
        from services.podcast_service import download_podcast_audio

        mock_run.return_value = MagicMock(returncode=0, stdout="[info] Downloading\n")
        result = download_podcast_audio("https://example.com/episode.mp3", "/tmp/test")
        assert result is not None
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_download_failure(self, mock_run):
        from services.podcast_service import download_podcast_audio

        mock_run.return_value = MagicMock(returncode=1, stderr="ERROR: unable to download")
        with pytest.raises(RuntimeError, match="download"):
            download_podcast_audio("https://example.com/bad.mp3", "/tmp/test")

    @patch("subprocess.run")
    def test_download_timeout(self, mock_run):
        import subprocess
        from services.podcast_service import download_podcast_audio

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="yt-dlp", timeout=300)
        with pytest.raises(RuntimeError, match="[Tt]imeout"):
            download_podcast_audio("https://example.com/long.mp3", "/tmp/test")


class TestTranscribeAudio:
    """T030: Unit tests for transcribe_audio()."""

    def test_transcribe_returns_text(self):
        from services.podcast_service import transcribe_audio

        mock_model = MagicMock()
        segments = [
            MagicMock(text=" Hello world."),
            MagicMock(text=" This is a test."),
        ]
        info = MagicMock(duration=120.0)
        mock_model.transcribe.return_value = (segments, info)

        with patch("services.podcast_service._load_whisper_model", return_value=mock_model):
            transcript, duration = transcribe_audio("/tmp/audio.wav", model_size="base")
            assert "Hello world" in transcript
            assert "This is a test" in transcript
            assert duration == 120.0

    def test_transcribe_selects_model(self):
        from services.podcast_service import transcribe_audio

        mock_model = MagicMock()
        segments = [MagicMock(text=" Test.")]
        info = MagicMock(duration=60.0)
        mock_model.transcribe.return_value = (segments, info)

        with patch("services.podcast_service._load_whisper_model", return_value=mock_model) as mock_load:
            transcribe_audio("/tmp/audio.wav", model_size="small")
            mock_load.assert_called_once_with("small")


class TestCleanTranscript:
    """T031: Unit tests for clean_transcript()."""

    def test_removes_filler_words(self):
        from services.podcast_service import clean_transcript

        text = "So um I think uh this is you know really like important"
        cleaned = clean_transcript(text)
        assert "um" not in cleaned.split()
        assert "uh" not in cleaned.split()
        assert "you know" not in cleaned
        assert "important" in cleaned

    def test_collapses_whitespace(self):
        from services.podcast_service import clean_transcript

        text = "Hello   world.   This   is   a   test."
        cleaned = clean_transcript(text)
        assert "  " not in cleaned

    def test_preserves_meaningful_content(self):
        from services.podcast_service import clean_transcript

        text = "The transformer architecture uses attention mechanisms for parallel processing."
        cleaned = clean_transcript(text)
        assert cleaned.strip() == text.strip()


class TestSummarizePodcast:
    """T032: Unit tests for summarize_podcast() full pipeline."""

    @patch("services.podcast_service.clean_transcript")
    @patch("services.podcast_service.transcribe_audio")
    @patch("services.podcast_service.download_podcast_audio")
    def test_full_pipeline(self, mock_download, mock_transcribe, mock_clean):
        from services.podcast_service import summarize_podcast

        mock_download.return_value = "/tmp/audio.wav"
        long_transcript = "This is a detailed podcast transcript. " * 50
        mock_transcribe.return_value = (long_transcript, 3600.0)
        mock_clean.return_value = long_transcript

        with patch("services.podcast_service._summarize_text") as mock_summarize:
            mock_summarize.return_value = "A concise summary of the podcast."

            result = summarize_podcast(
                "https://example.com/episode.mp3",
                model="base",
            )

            assert result.summary == "A concise summary of the podcast."
            assert result.episode.url == "https://example.com/episode.mp3"
            mock_download.assert_called_once()
            mock_transcribe.assert_called_once()
