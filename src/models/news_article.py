"""NewsArticle entity - represents a fetched article."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class NewsArticle:
    """Represents a fetched article with original content."""

    title: str
    url: str
    source_id: str
    published_at: datetime
    fetched_at: datetime
    content: str
    article_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self):
        """Validate NewsArticle attributes."""
        # Validate required fields
        if not self.title or len(self.title) < 5:
            raise ValueError("title must not be empty and have at least 5 characters")

        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"url must start with http:// or https://: {self.url}")

        if not self.source_id:
            raise ValueError("source_id is required")

        # Use title as fallback content for feeds with short descriptions
        if not self.content or len(self.content) < 50:
            if self.title and len(self.title) >= 10:
                self.content = self.title
            else:
                raise ValueError("content must have at least 50 characters")

        # Validate published_at <= fetched_at
        if self.published_at > self.fetched_at:
            raise ValueError("published_at cannot be in the future relative to fetched_at")

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "article_id": self.article_id,
            "title": self.title,
            "url": self.url,
            "source_id": self.source_id,
            "published_at": self.published_at.isoformat(),
            "fetched_at": self.fetched_at.isoformat(),
            "content": self.content,
            "author": self.author,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create NewsArticle from dictionary."""
        data = data.copy()
        data["published_at"] = datetime.fromisoformat(data["published_at"])
        data["fetched_at"] = datetime.fromisoformat(data["fetched_at"])
        return cls(**data)
