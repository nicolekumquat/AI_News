"""Podcast data models — PodcastEpisode and PodcastSummary."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class PodcastEpisode:
    """Represents a podcast episode to be transcribed and summarized."""

    url: str
    title: str
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    audio_path: str | None = None
    duration_seconds: int | None = None
    source_name: str | None = None
    downloaded_at: datetime | None = None

    def __post_init__(self):
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"url must start with http:// or https://: {self.url}")
        if len(self.title) < 3:
            raise ValueError(f"title must be at least 3 characters: '{self.title}'")
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValueError(f"duration_seconds must be >= 0: {self.duration_seconds}")


@dataclass
class PodcastSummary:
    """Represents the result of transcribing and summarizing a podcast."""

    episode_id: str
    transcript: str
    transcript_word_count: int
    summary: str
    summary_word_count: int
    compression_ratio: float
    model_size: str
    transcription_time_seconds: float
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    processed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    _VALID_MODELS = ("tiny", "base", "small", "medium")

    def __post_init__(self):
        if len(self.transcript) < 100:
            raise ValueError(
                f"transcript must be at least 100 characters, got {len(self.transcript)}"
            )
        if not self.summary:
            raise ValueError("summary must not be empty")
        if not (0.01 <= self.compression_ratio <= 0.5):
            raise ValueError(
                f"compression_ratio must be between 0.01 and 0.5, got {self.compression_ratio}"
            )
        if self.model_size not in self._VALID_MODELS:
            raise ValueError(
                f"model_size must be one of {self._VALID_MODELS}, got '{self.model_size}'"
            )
