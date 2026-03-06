"""Digest formatter for human-readable CLI output."""

from datetime import datetime

from models.digest import Digest
from models.digest_entry import DigestEntry
from models.news_article import NewsArticle


def format_digest(
    digest: Digest,
    entries: list[tuple[DigestEntry, NewsArticle]],
) -> str:
    """
    Format digest and entries as human-readable text.
    
    Args:
        digest: Digest metadata
        entries: List of (DigestEntry, NewsArticle) tuples
        
    Returns:
        Formatted digest string
    """
    lines = []
    
    # Header
    cache_indicator = f" [{digest.cache_status.upper()}]" if digest.cache_status != "fresh" else ""
    lines.append(f"AI Daily Digest - {digest.date}{cache_indicator}")
    
    if digest.cache_status == "cached":
        lines.append(
            f"Loaded from cache: {_format_datetime(digest.created_at)} | "
            f"Articles: {len(entries)} | "
            f"Sources: {len(digest.sources_fetched)}/{len(digest.sources_fetched) + len(digest.sources_failed)}"
        )
    else:
        lines.append(
            f"Generated: {_format_datetime(digest.created_at)} | "
            f"Articles: {len(entries)} | "
            f"Sources: {len(digest.sources_fetched)}/{len(digest.sources_fetched) + len(digest.sources_failed)}"
        )
    
    lines.append("")
    
    # Articles
    if not entries:
        lines.append("━" * 80)
        lines.append("")
        lines.append("No new AI news articles found within the last 48 hours.")
        lines.append("")
        if digest.sources_failed:
            lines.append(f"Sources failed: {', '.join(digest.sources_failed)}")
        lines.append("")
        lines.append("━" * 80)
    else:
        for i, (entry, article) in enumerate(entries, 1):
            lines.append("━" * 80)
            lines.append("")
            lines.append(f"{i}. {article.title}")
            
            # Source info
            source_info = f"Source: {article.source_id}"
            if article.published_at:
                source_info += f" | Published: {_format_datetime(article.published_at)}"
            lines.append(source_info)
            lines.append(f"URL: {article.url}")
            lines.append("")
            
            # Summary (wrapped)
            lines.extend(_wrap_text(entry.summary, width=78))
            lines.append("")
    
    # Footer
    lines.append("━" * 80)
    lines.append("")
    lines.append("End of Digest")
    
    footer_parts = [f"Curated: {digest.total_articles_curated} of {digest.total_articles_fetched} articles"]
    if digest.duplicates_removed > 0:
        footer_parts.append(f"Duplicates Removed: {digest.duplicates_removed}")
    if digest.sources_failed:
        footer_parts.append(f"Sources Failed: {len(digest.sources_failed)} ({', '.join(digest.sources_failed)})")
    
    lines.append(" | ".join(footer_parts))
    
    return "\n".join(lines)


def format_error(message: str, sources_failed: list[tuple[str, str]] | None = None) -> str:
    """
    Format error message.
    
    Args:
        message: Error message
        sources_failed: Optional list of (source_name, error_message) tuples
        
    Returns:
        Formatted error string
    """
    lines = [f"Error: {message}", ""]
    
    if sources_failed:
        lines.append("All configured news sources failed to fetch:")
        for source_name, error_msg in sources_failed:
            lines.append(f"- {source_name}: {error_msg}")
        lines.append("")
    
    return "\n".join(lines)


def _format_datetime(dt: datetime) -> str:
    """Format datetime as 'YYYY-MM-DD HH:MM:SS UTC'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _wrap_text(text: str, width: int = 78) -> list[str]:
    """
    Wrap text to specified width.
    
    Args:
        text: Text to wrap
        width: Maximum line width
        
    Returns:
        List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        
        if current_length + word_length + len(current_line) > width:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length
        else:
            current_line.append(word)
            current_length += word_length
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines


def format_sources_list(sources: list[dict]) -> str:
    """Format source list for CLI output per cli-interface.md.

    Args:
        sources: List of source dicts from source_manager.list_sources()

    Returns:
        Formatted table string with status indicators
    """
    total = len(sources)
    enabled_count = sum(1 for s in sources if s["enabled"])
    lines = [f"News Sources ({total} total, {enabled_count} enabled)", ""]

    builtin = [s for s in sources if s["is_builtin"]]
    custom = [s for s in sources if not s["is_builtin"]]

    if builtin:
        lines.append("  Built-in Sources:")
        for s in builtin:
            indicator = "✓" if s["enabled"] else "✗"
            lines.append(
                f"    {indicator} {s['source_id']:<20s}"
                f" {s['name']:<30s} {s['fetch_method']:<5s} {s['url']}"
            )

    if custom:
        lines.append("")
        lines.append("  Custom Sources:")
        for s in custom:
            indicator = "✓" if s["enabled"] else "✗"
            lines.append(
                f"    {indicator} {s['source_id']:<20s}"
                f" {s['name']:<30s} {s['fetch_method']:<5s} {s['url']}"
            )

    lines.append("")
    lines.append("Legend: ✓ enabled  ✗ disabled")
    return "\n".join(lines)


def format_podcast_summary(result) -> str:
    """Format podcast summarization result for CLI output.

    Args:
        result: PodcastResult with .episode and .summary_obj attributes.

    Returns:
        Formatted podcast summary string.
    """
    ep = result.episode
    s = result.summary_obj
    lines = []

    lines.append("━" * 80)
    lines.append("")
    lines.append("Podcast Summary")
    lines.append("")
    lines.append(f"  Title:    {ep.title}")
    if ep.source_name:
        lines.append(f"  Source:   {ep.source_name}")
    lines.append(f"  URL:      {ep.url}")
    if ep.duration_seconds is not None:
        mins, secs = divmod(ep.duration_seconds, 60)
        lines.append(f"  Duration: {mins}m {secs}s")
    lines.append("")
    lines.append(f"  Transcript Words: {s.transcript_word_count}")
    lines.append(f"  Model:            {s.model_size}")
    lines.append(f"  Compression:      {s.compression_ratio:.1%}")
    lines.append(f"  Transcription:    {s.transcription_time_seconds:.1f}s")
    lines.append("")
    lines.append("━" * 80)
    lines.append("")
    lines.extend(_wrap_text(s.summary, width=78))
    lines.append("")
    lines.append("━" * 80)

    return "\n".join(lines)
