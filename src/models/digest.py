"""Digest entity - represents a daily collection of digest entries."""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Digest:
    """Represents a daily collection of DigestEntry items."""

    digest_id: str  # Format: YYYY-MM-DD
    date: date
    entries: list[str]  # List of entry_id references
    total_articles_fetched: int
    total_articles_curated: int  # Articles after ranking/curation
    duplicates_removed: int
    sources_fetched: list[str]
    sources_failed: list[str]
    created_at: datetime
    cache_status: str = "fresh"  # "fresh", "cached", "stale"

    def __post_init__(self):
        """Validate Digest attributes."""
        # Validate digest_id format (YYYY-MM-DD)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.digest_id):
            raise ValueError(
                f"digest_id must match format YYYY-MM-DD: {self.digest_id}"
            )

        # Validate cache_status
        if self.cache_status not in ("fresh", "cached", "stale"):
            raise ValueError(
                f"cache_status must be 'fresh', 'cached', or 'stale': "
                f"{self.cache_status}"
            )

        # Validate curated count matches entries
        if self.total_articles_curated != len(self.entries):
            raise ValueError(
                f"total_articles_curated ({self.total_articles_curated}) "
                f"must equal len(entries) ({len(self.entries)})"
            )

        # Curated cannot exceed fetched
        if self.total_articles_curated > self.total_articles_fetched:
            raise ValueError(
                f"total_articles_curated ({self.total_articles_curated}) "
                f"cannot exceed total_articles_fetched "
                f"({self.total_articles_fetched})"
            )

        # Validate sources are disjoint
        if set(self.sources_fetched) & set(self.sources_failed):
            raise ValueError(
                "sources_fetched and sources_failed must be disjoint sets"
            )

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "digest_id": self.digest_id,
            "date": self.date.isoformat(),
            "entries": self.entries,
            "total_articles_fetched": self.total_articles_fetched,
            "total_articles_curated": self.total_articles_curated,
            "duplicates_removed": self.duplicates_removed,
            "sources_fetched": self.sources_fetched,
            "sources_failed": self.sources_failed,
            "created_at": self.created_at.isoformat(),
            "cache_status": self.cache_status,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create Digest from dictionary."""
        data = data.copy()
        data["date"] = date.fromisoformat(data["date"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
