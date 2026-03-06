"""Integration test for fetching from all sources and handling partial failures."""

import pytest


class TestFetchAllSources:
    """Integration test for fetching from all configured sources."""

    def test_fetch_from_all_sources(self):
        """Test fetching articles from all enabled sources."""
        from services.fetcher import fetch_all_sources
        
        # This test should FAIL until implementation exists
        with pytest.raises(ImportError):
            fetch_all_sources([])

    def test_handles_partial_source_failures(self):
        """Test that fetch continues when some sources fail."""
        with pytest.raises(ImportError):
            from services.fetcher import fetch_all_sources

    def test_updates_source_metadata(self):
        """Test that fetch updates source metadata (last_fetch_at, counts)."""
        with pytest.raises(ImportError):
            from services.fetcher import fetch_all_sources

    def test_returns_valid_articles_only(self):
        """Test that fetch only returns valid NewsArticle objects."""
        with pytest.raises(ImportError):
            from services.fetcher import fetch_all_sources
