"""ArXiv fetcher with client-side date filtering."""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_arxiv_papers(hours_ago: int = 48, max_results: int = 100) -> list[dict]:
    """
    Fetch AI/ML papers from ArXiv using REST API.
    
    Note: API does not support date filtering - must filter client-side.
    
    Args:
        hours_ago: Time window in hours (default: 48)
        max_results: Maximum results to fetch
        
    Returns:
        List of article dictionaries
    """
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    
    logger.debug(f"Fetching ArXiv papers: {params}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    # Parse Atom XML
    root = ET.fromstring(response.text)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    papers = []
    
    for entry in root.findall("atom:entry", ARXIV_NS):
        # Extract publication date
        published_elem = entry.find("atom:published", ARXIV_NS)
        if published_elem is None:
            continue
        
        published_str = published_elem.text
        pub_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        
        # Client-side filtering by date
        if pub_dt < cutoff:
            break  # sorted descending, so we can stop
        
        title_elem = entry.find("atom:title", ARXIV_NS)
        summary_elem = entry.find("atom:summary", ARXIV_NS)
        id_elem = entry.find("atom:id", ARXIV_NS)
        
        if title_elem is None or id_elem is None:
            continue
        
        papers.append({
            "title": title_elem.text.strip().replace("\n", " "),
            "url": id_elem.text.strip(),
            "published_at": published_str,
            "content": summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else "",
            "author": "",
            "metadata": {
                "source": "arxiv",
                "categories": ["cs.AI", "cs.LG", "cs.CL"],
            }
        })
    
    logger.info(f"Fetched {len(papers)} papers from ArXiv")
    return papers
