"""Podcast service — download, transcribe, and summarize podcast episodes."""

import glob
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass

from models.podcast import PodcastEpisode, PodcastSummary

logger = logging.getLogger(__name__)


@dataclass
class PodcastResult:
    """Container for summarize_podcast output."""

    episode: PodcastEpisode
    summary_obj: PodcastSummary

    @property
    def summary(self) -> str:
        return self.summary_obj.summary


def check_podcast_dependencies() -> list[str]:
    """Check that yt-dlp and faster-whisper are available.

    Returns:
        List of error strings (empty if all deps present).
    """
    errors = []
    if shutil.which("yt-dlp") is None:
        errors.append("yt-dlp is not installed or not on PATH")
    try:
        import importlib

        mod = importlib.import_module("faster_whisper")
        if mod is None:
            raise ImportError("faster_whisper is None")
    except (ImportError, ModuleNotFoundError):
        errors.append("faster-whisper is not installed (pip install faster-whisper)")
    return errors


def download_podcast_audio(url: str, output_dir: str) -> str:
    """Download podcast audio using yt-dlp.

    Args:
        url: Podcast episode URL.
        output_dir: Directory to store downloaded audio.

    Returns:
        Path to downloaded audio file.

    Raises:
        RuntimeError: On download failure or timeout.
    """
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "wav",
                "--output", os.path.join(output_dir, "%(title)s.%(ext)s"),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Timeout: download exceeded 300 seconds for {url}"
        ) from exc

    if result.returncode != 0:
        raise RuntimeError(f"Failed to download audio: {result.stderr}")

    audio_path = _find_audio_file(output_dir)
    return audio_path


def _find_audio_file(output_dir: str) -> str:
    """Find the downloaded audio file in the output directory."""
    for ext in ("*.wav", "*.mp3", "*.m4a", "*.opus", "*.ogg"):
        files = glob.glob(os.path.join(output_dir, ext))
        if files:
            return files[0]
    raise RuntimeError(f"No audio file found in {output_dir}")


def _load_whisper_model(model_size: str):
    """Load a faster-whisper model.

    Args:
        model_size: One of tiny, base, small, medium.

    Returns:
        WhisperModel instance.
    """
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(
    audio_path: str, model_size: str = "base"
) -> tuple[str, float]:
    """Transcribe audio using faster-whisper.

    Args:
        audio_path: Path to audio file.
        model_size: Whisper model size.

    Returns:
        Tuple of (transcript_text, duration_seconds).
    """
    model = _load_whisper_model(model_size)
    segments, info = model.transcribe(audio_path, beam_size=5)
    transcript = " ".join(seg.text for seg in segments).strip()
    return transcript, info.duration


def clean_transcript(text: str) -> str:
    """Remove filler words and collapse whitespace.

    Args:
        text: Raw transcript text.

    Returns:
        Cleaned transcript.
    """
    # Remove filler words (as standalone words)
    fillers = [
        r"\bum\b",
        r"\buh\b",
        r"\byou know\b",
        r"\blike\b",
        r"\bso\b",
    ]
    for pattern in fillers:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _summarize_text(text: str) -> str:
    """Summarize transcript text using extractive summarization.

    Reuses the existing frequency-based summarizer.
    """
    from services.summarizer import summarize

    return summarize(text, max_sentences=8)


def _cleanup_temp_dir(temp_dir: str) -> None:
    """Remove temporary download directory."""
    shutil.rmtree(temp_dir, ignore_errors=True)


def summarize_podcast(url: str, model: str = "base") -> PodcastResult:
    """Full podcast pipeline: download → transcribe → clean → summarize.

    Args:
        url: Podcast episode URL.
        model: Whisper model size (tiny, base, small, medium).

    Returns:
        PodcastResult with .episode and .summary_obj attributes.
    """
    temp_dir = tempfile.mkdtemp(prefix="podcast_")
    try:
        # Download
        audio_path = download_podcast_audio(url, temp_dir)

        # Transcribe
        start_time = time.monotonic()
        raw_transcript, duration = transcribe_audio(audio_path, model_size=model)
        transcription_time = time.monotonic() - start_time

        # Clean
        transcript = clean_transcript(raw_transcript)

        # Summarize
        summary_text = _summarize_text(transcript)

        # Build result objects
        transcript_word_count = len(transcript.split())
        summary_word_count = len(summary_text.split())
        compression_ratio = (
            summary_word_count / transcript_word_count
            if transcript_word_count > 0
            else 0.0
        )
        # Clamp ratio to valid range
        compression_ratio = max(0.01, min(0.5, compression_ratio))

        episode = PodcastEpisode(
            url=url,
            title=_extract_title(audio_path),
            audio_path=audio_path,
            duration_seconds=int(duration),
        )

        summary_obj = PodcastSummary(
            episode_id=episode.episode_id,
            transcript=transcript,
            transcript_word_count=transcript_word_count,
            summary=summary_text,
            summary_word_count=summary_word_count,
            compression_ratio=compression_ratio,
            model_size=model,
            transcription_time_seconds=transcription_time,
        )

        return PodcastResult(episode=episode, summary_obj=summary_obj)
    finally:
        _cleanup_temp_dir(temp_dir)


def _extract_title(audio_path: str) -> str:
    """Extract a title from the audio filename."""
    basename = os.path.splitext(os.path.basename(audio_path))[0]
    # Replace underscores/hyphens with spaces
    title = re.sub(r"[_-]+", " ", basename).strip()
    return title if len(title) >= 3 else "Untitled Episode"
