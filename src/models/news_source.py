"""NewsSource entity - represents a configured news source."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NewsSource:
    """Represents a configured source for fetching AI news."""

    source_id: str
    name: str
    fetch_method: str  # "api", "rss", "html"
    url: str
    enabled: bool = True
    last_fetch_at: Optional[datetime] = None
    fetch_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        """Validate NewsSource attributes."""
        # Validate source_id format
        if not re.match(r"^[a-z0-9-]+$", self.source_id):
            raise ValueError(
                f"source_id must be lowercase alphanumeric with hyphens: {self.source_id}"
            )

        # Validate fetch_method
        if self.fetch_method not in ("api", "rss", "html"):
            raise ValueError(f"fetch_method must be 'api', 'rss', or 'html': {self.fetch_method}")

        # Validate URL
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"url must start with http:// or https://: {self.url}")

        # Validate counts
        if self.fetch_count < 0:
            raise ValueError(f"fetch_count must be >= 0: {self.fetch_count}")
        if self.error_count < 0:
            raise ValueError(f"error_count must be >= 0: {self.error_count}")

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "name": self.name,
            "fetch_method": self.fetch_method,
            "url": self.url,
            "enabled": self.enabled,
            "last_fetch_at": self.last_fetch_at.isoformat() if self.last_fetch_at else None,
            "fetch_count": self.fetch_count,
            "error_count": self.error_count,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create NewsSource from dictionary."""
        data = data.copy()
        if data.get("last_fetch_at"):
            data["last_fetch_at"] = datetime.fromisoformat(data["last_fetch_at"])
        return cls(**data)
