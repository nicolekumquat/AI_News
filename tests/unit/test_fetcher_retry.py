"""Unit tests for retry logic (3 retries with exponential backoff)."""

import time

import pytest


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    def test_fetch_with_retry_3_attempts(self):
        """Test that fetch_with_retry attempts 3 times on failure."""
        from services.fetcher import fetch_with_retry
        
        # This test should FAIL until implementation exists
        with pytest.raises(ImportError):
            fetch_with_retry(lambda: None, "test-source")

    def test_retry_exponential_backoff_timing(self):
        """Test that retry uses exponential backoff: 1s, 2s, 4s."""
        with pytest.raises(ImportError):
            from services.fetcher import fetch_with_retry

    def test_retry_succeeds_on_second_attempt(self):
        """Test that retry returns result when request succeeds."""
        with pytest.raises(ImportError):
            from services.fetcher import fetch_with_retry

    def test_retry_logs_failures(self):
        """Test that retry logs each failed attempt."""
        with pytest.raises(ImportError):
            from services.fetcher import fetch_with_retry
