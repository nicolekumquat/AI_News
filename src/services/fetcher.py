"""Unified fetcher service with retry logic and orchestration."""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable

from models.news_article import NewsArticle
from models.news_source import NewsSource
from services.content_extractor import enrich_articles
from services.fetchers import arxiv, hackernews, reddit, rss

logger = logging.getLogger(__name__)


def fetch_with_retry(
    fetch_fn: Callable[[], Any],
    source_name: str,
    max_retries: int = 3,
    delays: list[int] = None,
) -> Any:
    """
    Retry fetch function with exponential backoff.
    
    Per FR-009: 3 retries with delays [1, 2, 4] seconds.
    
    Args:
        fetch_fn: Function to execute
        source_name: Name of source for logging
        max_retries: Maximum number of retry attempts
        delays: List of delays between retries (default: [1, 2, 4])
        
    Returns:
        Result from fetch_fn on success
        
    Raises:
        Last exception if all retries fail
    """
    if delays is None:
        delays = [1, 2, 4]
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return fetch_fn()
        except Exception as e:
            last_exception = e
            logger.warning(
                f"{source_name} attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            
            if attempt < max_retries - 1:
                delay = delays[attempt] if attempt < len(delays) else delays[-1]
                logger.info(f"Retrying {source_name} in {delay}s...")
                time.sleep(delay)
    
    logger.error(f"{source_name}: all {max_retries} retries exhausted")
    raise last_exception


def fetch_all_sources(
    sources: list[NewsSource],
    hours_ago: int = 48,
) -> tuple[list[NewsArticle], list[str], list[str]]:
    """
    Fetch articles from all enabled sources.
    
    Args:
        sources: List of NewsSource objects
        hours_ago: Time window in hours
        
    Returns:
        Tuple of (articles, sources_fetched, sources_failed)
    """
    all_articles = []
    sources_fetched = []
    sources_failed = []
    fetched_at = datetime.now(timezone.utc)
    
    for source in sources:
        if not source.enabled:
            logger.debug(f"Skipping disabled source: {source.name}")
            continue

        logger.info(f"Fetching from {source.name}...")

        try:
            # Route to appropriate fetcher
            if source.source_id == "hackernews":
                raw_articles = fetch_with_retry(
                    lambda: hackernews.fetch_hn_posts(hours_ago=hours_ago),
                    source.name
                )
            elif source.source_id.startswith("reddit-"):
                # Extract subreddit from URL: .../r/<name>/...
                import re
                match = re.search(r'/r/([^/]+)/', source.url)
                sub = match.group(1) if match else "MachineLearning"
                raw_articles = fetch_with_retry(
                    lambda s=sub: reddit.fetch_reddit_posts(subreddit=s),
                    source.name
                )
            elif source.source_id == "arxiv":
                raw_articles = fetch_with_retry(
                    lambda: arxiv.fetch_arxiv_papers(hours_ago=hours_ago),
                    source.name
                )
            elif source.fetch_method == "rss":
                # Blogs/newsletters post weekly/biweekly — use 14-day window
                rss_hours = max(hours_ago, 336)
                raw_articles = fetch_with_retry(
                    lambda u=source.url, n=source.name, h=rss_hours: rss.fetch_rss_feed(u, n, hours_ago=h),
                    source.name
                )
            else:
                logger.warning(f"Unknown fetch method for {source.name}: {source.fetch_method}")
                continue

            # Enrich articles with short content by fetching full pages
            if raw_articles:
                raw_articles = enrich_articles(raw_articles)

            # Convert to NewsArticle objects with validation
            for raw_article in raw_articles:
                try:
                    article = NewsArticle(
                        title=raw_article["title"],
                        url=raw_article["url"],
                        source_id=source.source_id,
                        published_at=datetime.fromisoformat(raw_article["published_at"]),
                        fetched_at=fetched_at,
                        content=raw_article.get("content", raw_article["title"]),
                        author=raw_article.get("author"),
                        metadata=raw_article.get("metadata"),
                    )
                    all_articles.append(article)
                except (ValueError, KeyError) as e:
                    logger.warning(
                        f"Rejected article from {source.name}: {e} - "
                        f"Title: {raw_article.get('title', 'N/A')[:50]}"
                    )
            
            sources_fetched.append(source.source_id)
            source.last_fetch_at = fetched_at
            source.fetch_count += 1
            
        except Exception as e:
            logger.error(f"Failed to fetch from {source.name}: {e}")
            sources_failed.append(source.source_id)
            source.error_count += 1
    
    logger.info(
        f"Fetched {len(all_articles)} articles from {len(sources_fetched)} sources "
        f"({len(sources_failed)} failed)"
    )
    
    return all_articles, sources_fetched, sources_failed
