"""HackerNews fetcher using Algolia API."""

import logging
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


def fetch_hn_posts(hours_ago: int = 48, min_points: int = 5, max_results: int = 50) -> list[dict]:
    """
    Fetch AI-related posts from HackerNews using Algolia Search API.
    
    Args:
        hours_ago: Time window in hours (default: 48)
        min_points: Minimum points threshold
        max_results: Maximum number of results
        
    Returns:
        List of article dictionaries with title, url, published_at, content
    """
    cutoff_timestamp = int(time.time()) - (hours_ago * 3600)
    
    url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {
        "query": 'AI OR "artificial intelligence" OR "machine learning" OR LLM OR GPT OR Claude',
        "tags": "story",
        "numericFilters": f"created_at_i>{cutoff_timestamp},points>{min_points}",
        "hitsPerPage": max_results,
    }
    
    logger.debug(f"Fetching HackerNews posts: {params}")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    articles = []
    
    for hit in data.get("hits", []):
        # Skip if no URL
        if not hit.get("url"):
            continue
        
        articles.append({
            "title": hit.get("title", ""),
            "url": hit.get("url", ""),
            "published_at": datetime.fromtimestamp(
                hit.get("created_at_i", time.time()), 
                tz=timezone.utc
            ).isoformat(),
            "content": hit.get("story_text", hit.get("title", "")),
            "author": hit.get("author", ""),
            "metadata": {
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "hn_id": hit.get("objectID", ""),
            }
        })
    
    logger.info(f"Fetched {len(articles)} articles from HackerNews")
    return articles
