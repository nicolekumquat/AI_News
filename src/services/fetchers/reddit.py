"""Reddit fetcher for r/MachineLearning."""

import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


def fetch_reddit_posts(
    subreddit: str = "MachineLearning",
    sort: str = "top",
    time_filter: str = "day",
    limit: int = 50,
) -> list[dict]:
    """
    Fetch posts from Reddit using native JSON endpoint.
    
    CRITICAL: Must set custom User-Agent or get HTTP 429.
    
    Args:
        subreddit: Subreddit name
        sort: Sort type (top, hot, new)
        time_filter: Time filter (day, week, month)
        limit: Maximum number of posts
        
    Returns:
        List of article dictionaries
    """
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    headers = {
        "User-Agent": "ai-daily-digest:v1.0 (local CLI tool; once-daily fetch)"
    }
    params = {"t": time_filter, "limit": limit}
    
    logger.debug(f"Fetching Reddit r/{subreddit}: {sort}/{time_filter}")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    posts = data.get("data", {}).get("children", [])
    
    articles = []
    for post in posts:
        post_data = post.get("data", {})
        
        # Skip if no title or URL
        if not post_data.get("title") or not post_data.get("url"):
            continue
        
        articles.append({
            "title": post_data.get("title", ""),
            "url": post_data.get("url", ""),
            "published_at": datetime.fromtimestamp(
                post_data.get("created_utc", 0),
                tz=timezone.utc
            ).isoformat(),
            "content": post_data.get("selftext", post_data.get("title", "")),
            "author": post_data.get("author", ""),
            "metadata": {
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
                "subreddit": subreddit,
            }
        })
    
    logger.info(f"Fetched {len(articles)} posts from Reddit r/{subreddit}")
    return articles
