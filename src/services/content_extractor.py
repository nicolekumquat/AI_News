"""Extract article content from web pages when RSS provides only teasers."""

import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Minimum RSS content length before we fetch the full page
MIN_CONTENT_LENGTH = 300

# Max content to store (avoid huge pages)
MAX_CONTENT_LENGTH = 15000

# Request timeout for fetching article pages
FETCH_TIMEOUT = 15

# Selectors to try for article body, in priority order
ARTICLE_SELECTORS = [
    "article .body",
    "article .post-content",
    ".post-body",
    ".entry-content",
    ".article-content",
    ".post-content",
    ".article-body",
    ".blog-post-body",
    ".markup",
    "article",
    '[role="article"]',
    ".post",
    "main",
]

# Elements to strip before extracting text
STRIP_TAGS = [
    "script", "style", "nav", "header", "footer",
    "aside", "iframe", "form", "button", "svg",
    "figcaption", "figure img",
    # Newsletter/Substack specific
    ".subscription-widget", ".subscribe-widget",
    ".share-dialog", ".social-share",
    ".post-footer", ".article-footer",
    ".podcast-links", ".listen-links",
    ".sponsor", ".sponsorship", ".ad",
    ".cta", ".call-to-action",
    ".related-posts", ".recommended",
    ".comments", ".comment-section",
]


def enrich_articles(articles: list[dict]) -> list[dict]:
    """
    Fetch full content for articles with short RSS descriptions.

    Args:
        articles: List of article dicts from fetchers

    Returns:
        Same list with enriched content fields
    """
    enriched_count = 0

    for article in articles:
        content = article.get("content", "")
        if len(content) >= MIN_CONTENT_LENGTH:
            continue

        url = article.get("url", "")
        if not url:
            continue

        try:
            full_text = extract_content(url)
            if full_text and len(full_text) > len(content):
                article["content"] = full_text
                enriched_count += 1
        except Exception as e:
            logger.debug(f"Could not extract content from {url}: {e}")

    if enriched_count:
        logger.info(f"Enriched {enriched_count} articles with full page content")

    return articles


def extract_content(url: str) -> str:
    """
    Fetch a URL and extract the main article text.

    Args:
        url: Article URL

    Returns:
        Extracted text content, or empty string on failure
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    response = requests.get(url, headers=headers, timeout=FETCH_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml")

    # Remove unwanted elements
    for tag in STRIP_TAGS:
        for el in soup.select(tag):
            el.decompose()

    # Substack: strip editor preamble above the first <hr> in .body
    _strip_substack_preamble(soup)

    # Try each selector until we find substantial content
    for selector in ARTICLE_SELECTORS:
        elements = soup.select(selector)
        for el in elements:
            text = _clean_text(el.get_text(separator=" "))
            if len(text) >= MIN_CONTENT_LENGTH:
                return text[:MAX_CONTENT_LENGTH]

    # Fallback: try the body
    body = soup.find("body")
    if body:
        text = _clean_text(body.get_text(separator=" "))
        if len(text) >= MIN_CONTENT_LENGTH:
            return text[:MAX_CONTENT_LENGTH]

    return ""


def _strip_substack_preamble(soup: BeautifulSoup) -> None:
    """Remove editor/newsletter preamble above the first <hr> in Substack posts.

    Many Substack guest-posts have an editor's note followed by an <hr>
    separator before the actual article.  This removes everything above
    that <hr> inside the .body element so the extracted text starts with
    the real content.
    """
    body = (
        soup.select_one(".body.markup")
        or soup.select_one("article .body")
    )
    if body is None:
        return

    hr = body.find("hr")
    if hr is None:
        return

    # Walk backwards from the <hr> and remove all preceding siblings
    # (the <hr>'s parent wrapper is removed too if it's just a wrapper div)
    hr_parent = hr.parent
    target = hr_parent if hr_parent is not body else hr

    for sibling in list(target.previous_siblings):
        sibling.extract()
    target.extract()


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove noise from extracted text."""
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Strip newsletter/podcast boilerplate phrases
    boilerplate_patterns = [
        # Sponsor/promo blocks
        r"Brought to you by:?\s*[^.]{5,80}\s*(?:—[^.]{5,120}\.?)?",
        r"(?:Listen|Watch|Read)\s+(?:on|or watch on)\s+YouTube\s*,?\s*Spotify\s*,?\s*(?:and\s+)?Apple Podcasts?",
        r"Listen\s+(?:on|or)\s+(?:YouTube|Spotify|Apple)[^.]*",
        # "What you'll learn" lists
        r"What you['']ll learn:?\s*",
        # Share/subscribe CTAs
        r"(?:Share|Subscribe|Sign up|Get started)[^.]*(?:newsletter|podcast|free trial)[^.]*\.?",
        r"If you enjoyed this.*?(?:share|subscribe)[^.]*\.?",
        r"(?:Click|Tap) here to (?:share|subscribe|listen)[^.]*",
        # Cross-promo
        r"Presented by[^.]{5,80}\.?",
        r"Sponsored by[^.]{5,80}\.?",
        r"This (?:episode|post) is (?:brought|presented|sponsored) by[^.]*\.?",
        # Table of contents / bullet list headers
        r"(?:We discuss|In this (?:episode|post|issue)|What we cover):?\s*",
        r"(?:Topics covered|Key takeaways|Highlights):?\s*",
        # Sponsor taglines that leak through
        r"WorkOS\s*[^\.]{0,80}",
        r"Orkes\s*[^\.]{0,80}",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Remove very short lines that are likely navigation/UI elements
    lines = text.split(". ")
    cleaned = ". ".join(line for line in lines if len(line.strip()) > 10)
    return re.sub(r"\s+", " ", cleaned).strip()
