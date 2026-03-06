"""Cache service for storing and retrieving digests."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class CacheService:
    """Service for caching articles and digests to local filesystem."""

    def __init__(self, cache_dir: Optional[Path] = None, retention_days: int = 30):
        """
        Initialize cache service.
        
        Args:
            cache_dir: Directory for cache files (default: ~/.ai-digest/cache)
            retention_days: Number of days to retain cached data
        """
        self.cache_dir = cache_dir or Path.home() / ".ai-digest" / "cache"
        self.retention_days = retention_days
        
        # Create cache directories
        self.articles_dir = self.cache_dir / "articles"
        self.digests_dir = self.cache_dir / "digests"
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.digests_dir.mkdir(parents=True, exist_ok=True)

    def save_articles(self, date_str: str, articles: list[dict]) -> None:
        """
        Save articles for a specific date.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            articles: List of article dictionaries
        """
        file_path = self.articles_dir / f"{date_str}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2)

    def load_articles(self, date_str: str) -> Optional[list[dict]]:
        """
        Load articles for a specific date.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            List of article dictionaries or None if not cached
        """
        file_path = self.articles_dir / f"{date_str}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_digest(self, digest_data: dict, entries_data: list[dict]) -> None:
        """
        Save digest and its entries.
        
        Args:
            digest_data: Digest dictionary
            entries_data: List of DigestEntry dictionaries
        """
        date_str = digest_data["digest_id"]
        file_path = self.digests_dir / f"{date_str}.json"
        
        data = {
            "digest": digest_data,
            "entries": entries_data,
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_digest(self, date_str: str) -> Optional[dict]:
        """
        Load digest and its entries for a specific date.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            Dictionary with "digest" and "entries" keys, or None if not cached
        """
        file_path = self.digests_dir / f"{date_str}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_digest_fresh(self, date_str: str, max_age_hours: int = 24) -> bool:
        """
        Check if cached digest is still fresh.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            max_age_hours: Maximum age in hours to consider fresh
            
        Returns:
            True if digest exists and is fresh, False otherwise
        """
        file_path = self.digests_dir / f"{date_str}.json"
        if not file_path.exists():
            return False
        
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        age = datetime.now() - file_mtime
        return age < timedelta(hours=max_age_hours)

    def cleanup_old_cache(self) -> None:
        """Remove cache files older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        for file_path in self.articles_dir.glob("*.json"):
            if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                file_path.unlink()
        
        for file_path in self.digests_dir.glob("*.json"):
            if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                file_path.unlink()
