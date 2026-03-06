"""RSS feed fetcher for blogs and news sources."""

import logging
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser

logger = logging.getLogger(__name__)


def fetch_rss_feed(feed_url: str, source_name: str, hours_ago: int = 48) -> list[dict]:
    """
    Fetch articles from RSS/Atom feed with time filtering.
    
    Args:
        feed_url: URL of RSS/Atom feed
        source_name: Name of source for logging
        hours_ago: Time window in hours (default: 48)
        
    Returns:
        List of article dictionaries
    """
    logger.debug(f"Fetching RSS feed: {source_name} ({feed_url})")
    
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    articles = []
    
    for entry in feed.entries:
        # Extract publication date
        pub_dt = None
        
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_dt = datetime.fromtimestamp(
                mktime(entry.published_parsed),
                tz=timezone.utc
            )
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub_dt = datetime.fromtimestamp(
                mktime(entry.updated_parsed),
                tz=timezone.utc
            )
        
        # Skip if no date or too old
        if pub_dt is None or pub_dt < cutoff:
            continue
        
        # Skip if missing required fields
        if not entry.get("title") or not entry.get("link"):
            continue
        
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published_at": pub_dt.isoformat(),
            "content": entry.get("summary", entry.get("description", "")),
            "author": entry.get("author", ""),
            "metadata": {
                "source": source_name,
                "feed_url": feed_url,
            }
        })
    
    logger.info(f"Fetched {len(articles)} articles from {source_name}")
    return articles
