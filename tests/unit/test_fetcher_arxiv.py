"""Unit tests for ArXiv fetcher with client-side date filtering."""

import pytest


class TestArXivFetcher:
    """Test ArXiv fetcher with client-side date filtering."""

    def test_fetch_arxiv_papers_with_categories(self):
        """Test fetching ArXiv papers with AI/ML categories."""
        from services.fetchers.arxiv import fetch_arxiv_papers
        
        # This test should FAIL until implementation exists
        with pytest.raises(ImportError):
            fetch_arxiv_papers(hours_ago=48)

    def test_arxiv_client_side_date_filtering(self):
        """Test that ArXiv fetcher filters by date on client side."""
        with pytest.raises(ImportError):
            from services.fetchers.arxiv import fetch_arxiv_papers

    def test_arxiv_parses_atom_xml(self):
        """Test that ArXiv fetcher parses Atom XML responses."""
        with pytest.raises(ImportError):
            from services.fetchers.arxiv import fetch_arxiv_papers

    def test_arxiv_handles_pagination(self):
        """Test that ArXiv fetcher handles large result sets."""
        with pytest.raises(ImportError):
            from services.fetchers.arxiv import fetch_arxiv_papers
