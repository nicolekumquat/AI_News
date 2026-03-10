"""Digest generator service - curates and summarizes top articles."""

import logging
from datetime import datetime, timezone
from difflib import SequenceMatcher

from models.digest import Digest
from models.digest_entry import DigestEntry
from models.news_article import NewsArticle
from services.scorer import MAX_DIGEST_ARTICLES, rank_and_select
from services.summarizer import summarize

logger = logging.getLogger(__name__)

# Articles with content similarity above this threshold are duplicates
SIMILARITY_THRESHOLD = 0.40

# Per-source caps to prevent any single source from dominating the digest.
# Key = source_id prefix (matched with str.startswith), value = max articles.
SOURCE_CAPS = {
    "reddit-": 2,
}


def _content_fingerprint(article: NewsArticle) -> str:
    """Normalize article content for similarity comparison."""
    import re
    text = (article.title + " " + article.content).lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def _extract_key_terms(article: NewsArticle) -> set[str]:
    """Extract meaningful terms for topic-based dedup."""
    import re
    text = (article.title + " " + article.content[:500]).lower()
    text = re.sub(r"https?://\S+", "", text)
    words = re.findall(r"\b[a-z]{3,}\b", text)

    stop = {
        "the", "and", "for", "are", "was", "were", "been", "have",
        "has", "had", "will", "would", "could", "should", "can",
        "this", "that", "with", "from", "into", "about", "more",
        "than", "also", "just", "how", "what", "when", "where",
        "who", "which", "their", "your", "they", "you", "not",
        "but", "all", "its", "our", "his", "her", "she",
        "been", "being", "each", "other", "some", "most",
        "very", "only", "here", "there", "then", "now",
    }
    return {w for w in words if w not in stop}


def _is_duplicate(article: NewsArticle, selected: list[NewsArticle]) -> bool:
    """Check if article covers the same topic as an already-selected article."""
    new_terms = _extract_key_terms(article)
    if not new_terms:
        return False

    for existing in selected:
        existing_terms = _extract_key_terms(existing)
        if not existing_terms:
            continue

        # Jaccard similarity on key terms
        overlap = new_terms & existing_terms
        union = new_terms | existing_terms
        jaccard = len(overlap) / len(union) if union else 0

        if jaccard >= SIMILARITY_THRESHOLD:
            logger.debug(
                f"Duplicate detected (jaccard={jaccard:.2f}): "
                f"'{article.title[:40]}' ~ '{existing.title[:40]}'"
            )
            return True
    return False


def generate_digest(
    date_str: str,
    articles: list[NewsArticle],
    sources_fetched: list[str],
    sources_failed: list[str],
) -> tuple[Digest, list[DigestEntry]]:
    """
    Generate a curated digest from articles.

    Ranks articles by insight potential, selects the top 15,
    and generates extractive summaries that capture key takeaways.

    Args:
        date_str: Date string (YYYY-MM-DD)
        articles: List of NewsArticle objects
        sources_fetched: List of successful source IDs
        sources_failed: List of failed source IDs

    Returns:
        Tuple of (Digest, list of DigestEntry objects)
    """
    logger.info(
        f"Generating digest for {date_str} from {len(articles)} articles"
    )

    # Rank and select top articles by insight score
    ranked = rank_and_select(articles, max_articles=MAX_DIGEST_ARTICLES * 2)

    # Deduplicate: skip articles too similar to already-selected ones
    deduped = []
    selected_articles = []
    duplicates_removed = 0
    source_counts: dict[str, int] = {}  # track per-source selections
    for article, score in ranked:
        if len(deduped) >= MAX_DIGEST_ARTICLES:
            break
        if _is_duplicate(article, selected_articles):
            duplicates_removed += 1
            continue
        # Enforce per-source caps
        capped = False
        for prefix, cap in SOURCE_CAPS.items():
            if article.source_id.startswith(prefix):
                if source_counts.get(prefix, 0) >= cap:
                    logger.debug(
                        f"Source cap ({cap}) reached for {prefix}: "
                        f"skipping '{article.title[:40]}'"
                    )
                    capped = True
                break
        if capped:
            continue
        deduped.append((article, score))
        selected_articles.append(article)
        for prefix in SOURCE_CAPS:
            if article.source_id.startswith(prefix):
                source_counts[prefix] = source_counts.get(prefix, 0) + 1

    entries = []
    for article, score in deduped:
        # Generate extractive summary capturing key insights
        summary = summarize(article.content, max_sentences=3)

        # Fallback: use first 2-3 complete sentences if summarizer
        # returns empty
        if not summary:
            summary = _fallback_summary(article.content)

        summary_method = "frequency" if summary else "fallback"

        compression = len(summary) / max(len(article.content), 1)
        # Clamp compression ratio to valid range
        compression = min(max(compression, 0.06), 0.55)

        entry = DigestEntry(
            article_id=article.article_id,
            summary=summary,
            summary_method=summary_method,
            compression_ratio=compression,
            processed_at=datetime.now(timezone.utc),
            is_duplicate=False,
            duplicate_of=None,
        )
        entries.append(entry)

    # Create digest metadata
    digest = Digest(
        digest_id=date_str,
        date=datetime.strptime(date_str, "%Y-%m-%d").date(),
        entries=[entry.entry_id for entry in entries],
        total_articles_fetched=len(articles),
        total_articles_curated=len(entries),
        duplicates_removed=duplicates_removed,
        sources_fetched=sources_fetched,
        sources_failed=sources_failed,
        created_at=datetime.now(timezone.utc),
        cache_status="fresh",
    )

    logger.info(
        f"Digest generated: {len(entries)} curated entries "
        f"from {len(articles)} total articles"
    )
    return digest, entries


def _fallback_summary(content: str) -> str:
    """Extract first 2-3 complete sentences as fallback summary."""
    import re

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", content.strip())
    result = []
    for s in sentences[:3]:
        s = s.strip()
        if len(s) > 20:
            result.append(s)
        if len(result) >= 2:
            break
    return " ".join(result) if result else content[:300]
