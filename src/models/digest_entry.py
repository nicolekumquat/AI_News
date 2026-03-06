"""DigestEntry entity - represents a processed article in a digest."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DigestEntry:
    """Represents a processed article ready for inclusion in a digest."""

    article_id: str
    summary: str
    summary_method: str  # "frequency", "fallback"
    compression_ratio: float
    processed_at: datetime
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

    def __post_init__(self):
        """Validate DigestEntry attributes."""
        # Validate summary
        if not self.summary:
            raise ValueError("summary must not be empty")

        # Validate summary_method
        if self.summary_method not in ("frequency", "fallback"):
            raise ValueError(
                f"summary_method must be 'frequency' or 'fallback': {self.summary_method}"
            )

        # Validate compression_ratio
        if not (0.05 < self.compression_ratio <= 0.55):
            raise ValueError(
                f"compression_ratio must be in range (0.05, 0.55]: {self.compression_ratio}"
            )

        # Validate duplicate state
        if self.is_duplicate and not self.duplicate_of:
            raise ValueError("duplicate_of must be set when is_duplicate is True")
        if not self.is_duplicate and self.duplicate_of:
            raise ValueError("duplicate_of must be None when is_duplicate is False")

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "entry_id": self.entry_id,
            "article_id": self.article_id,
            "summary": self.summary,
            "summary_method": self.summary_method,
            "compression_ratio": self.compression_ratio,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "processed_at": self.processed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create DigestEntry from dictionary."""
        data = data.copy()
        data["processed_at"] = datetime.fromisoformat(data["processed_at"])
        return cls(**data)
