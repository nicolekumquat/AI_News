"""CLI main entry point."""

import io
import logging
import sys

from cli.commands import format_date, parse_args
from cli.formatter import format_digest, format_error
from cli.html_formatter import format_digest_html
from config.loader import ensure_config_exists, load_config
from config.logging import setup_logging
from config.sources import get_default_sources
from models.digest import Digest
from models.digest_entry import DigestEntry
from models.news_article import NewsArticle
from services.cache import CacheService
from services.digest_generator import generate_digest
from services.fetcher import fetch_all_sources

logger = None


def main():
    """Main CLI entry point."""
    global logger

    # Ensure stdout handles Unicode on Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parse arguments
    args = parse_args()

    # Dispatch to subcommand handlers
    if args.command == "sources":
        _handle_sources(args)
    elif args.command == "podcast":
        _handle_podcast(args)
    else:
        _handle_digest(args)


def _handle_sources(args):
    """Dispatch source management subcommands."""
    from cli.formatter import format_sources_list
    from services.source_manager import (
        add_source,
        disable_source,
        enable_source,
        list_sources,
        remove_source,
    )

    if args.sources_action == "list":
        sources = list_sources()
        print(format_sources_list(sources))
    elif args.sources_action == "add":
        result = add_source(name=args.name, url=args.url, method=args.method)
        if result.get("error"):
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"Added source: {result['source_id']} ({result['name']})")
        print(f"URL: {result['url']}")
        print(f"Method: {result['method']}")
        print("Status: enabled")
        print()
        print("Source saved to configuration.")
    elif args.sources_action == "remove":
        result = remove_source(args.source_id)
        if result.get("error"):
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"Removed source: {result['source_id']} ({result['name']})")
        print("Source removed from configuration.")
    elif args.sources_action == "enable":
        result = enable_source(args.source_id)
        if result.get("error"):
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        if result.get("already"):
            print(f"Source '{args.source_id}' is already enabled.")
        else:
            print(f"Enabled source: {result['source_id']} ({result['name']})")
    elif args.sources_action == "disable":
        result = disable_source(args.source_id)
        if result.get("error"):
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        if result.get("already"):
            print(f"Source '{args.source_id}' is already disabled.")
        else:
            print(f"Disabled source: {result['source_id']} ({result['name']})")
    else:
        print("Usage: ai-digest sources {list|add|remove|enable|disable}", file=sys.stderr)
        sys.exit(1)


def _handle_podcast(args):
    """Dispatch podcast summarization."""
    from cli.formatter import format_podcast_summary
    from services.podcast_service import check_podcast_dependencies, summarize_podcast

    # Check dependencies first
    dep_errors = check_podcast_dependencies()
    if dep_errors:
        for err in dep_errors:
            print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    # Load config for default model
    config = load_config()
    model = args.model or config.get("podcast", {}).get("default_model", "base")

    try:
        summary = summarize_podcast(args.url, model=model)
        print(format_podcast_summary(summary))
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Podcast processing failed")
        # Map specific errors to exit codes
        error_msg = str(e)
        if "download" in error_msg.lower():
            print(f"Error: Failed to download audio from URL: {args.url}", file=sys.stderr)
            print(f"yt-dlp error: {e}", file=sys.stderr)
            sys.exit(4)
        elif "transcri" in error_msg.lower():
            print(f"Error: Transcription failed: {e}", file=sys.stderr)
            sys.exit(5)
        else:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def _handle_digest(args):
    """Handle default digest generation (existing behaviour)."""
    date_str = format_date(args.date)

    # When generating HTML, suppress console logging so only the HTML
    # document appears on stdout (file logging is unaffected).
    if args.html:
        _silence_console_logging()

    logger.info(f"AI Daily Digest - Requesting digest for {date_str}")

    try:
        # Load configuration
        config_path = ensure_config_exists()
        config = load_config(config_path)
        
        # Initialize services
        cache = CacheService()
        sources = get_default_sources()
        
        # Check cache first
        cached_data = cache.load_digest(date_str)
        
        if cached_data and cache.is_digest_fresh(date_str):
            # Use cached digest
            logger.info(f"Using cached digest for {date_str}")
            digest = Digest.from_dict(cached_data["digest"])
            entries = [DigestEntry.from_dict(e) for e in cached_data["entries"]]
            
            # Load articles from cache
            cached_articles = cache.load_articles(date_str)
            if cached_articles:
                articles = [NewsArticle.from_dict(a) for a in cached_articles]
            else:
                articles = []
            
            # Mark as cached
            digest.cache_status = "cached"
            
            # Pair entries with articles
            article_map = {a.article_id: a for a in articles}
            entry_article_pairs = [
                (entry, article_map.get(entry.article_id))
                for entry in entries
                if entry.article_id in article_map
            ]
            
            # Enrich podcast articles with transcript summaries
            if args.html:
                _enrich_podcasts(entry_article_pairs, config)

            # Display
            fmt = format_digest_html if args.html else format_digest
            print(fmt(digest, entry_article_pairs))
            sys.exit(0)
        
        # Fetch fresh articles
        logger.info(f"Fetching fresh articles for {date_str}")
        articles, sources_fetched, sources_failed = fetch_all_sources(sources, hours_ago=48)
        
        # Check if all sources failed
        if not articles and sources_failed and not sources_fetched:
            error_msg = f"Unable to generate digest for {date_str}"
            source_errors = [(s, "All retries exhausted") for s in sources_failed]
            print(format_error(error_msg, source_errors), file=sys.stderr)
            sys.exit(2)
        
        # Generate digest
        digest, entries = generate_digest(date_str, articles, sources_fetched, sources_failed)
        
        # Cache digest and articles
        cache.save_articles(date_str, [a.to_dict() for a in articles])
        cache.save_digest(digest.to_dict(), [e.to_dict() for e in entries])
        
        # Pair entries with articles
        article_map = {a.article_id: a for a in articles}
        entry_article_pairs = [
            (entry, article_map[entry.article_id])
            for entry in entries
        ]

        # Enrich podcast articles with transcript summaries
        if args.html:
            _enrich_podcasts(entry_article_pairs, config)
        
        # Display
        fmt = format_digest_html if args.html else format_digest
        print(fmt(digest, entry_article_pairs))
        sys.exit(0)
        
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _enrich_podcasts(entry_article_pairs, config):
    """Transcribe podcast episodes and embed summaries into article content."""
    from services.podcast_service import check_podcast_dependencies, summarize_podcast

    deps = check_podcast_dependencies()
    if deps:
        logger.warning("Podcast deps missing, skipping transcription: %s", deps)
        return

    model = config.get("podcast", {}).get("default_model", "base")

    for entry, article in entry_article_pairs:
        if article is None:
            continue
        if "\U0001f399" not in article.title:
            continue
        # Skip if already has a transcript (from a prior run)
        if article.content and "Podcast Transcript Summary:" in article.content:
            continue

        logger.info("Transcribing podcast: %s", article.title)
        try:
            result = summarize_podcast(article.url, model=model)
            article.content = (
                f"Podcast Transcript Summary:\n\n{result.summary}\n\n"
                f"---\n\nFull Transcript ({result.summary_obj.transcript_word_count:,} words, "
                f"{result.episode.duration_seconds // 60}min):\n\n"
                f"{result.summary_obj.transcript}"
            )
            logger.info("Transcribed: %s (%d words)", article.title, result.summary_obj.transcript_word_count)
        except Exception as e:
            logger.warning("Failed to transcribe %s: %s", article.url, e)


def _silence_console_logging():
    """Remove console (StreamHandler) handlers from the root logger.

    Keeps file-based logging intact so diagnostics are still captured in
    the log file, but nothing leaks to stderr/stdout when we need clean
    output (e.g. ``--html``).
    """
    root = logging.getLogger()
    root.handlers = [
        h for h in root.handlers
        if not isinstance(h, logging.StreamHandler)
        or isinstance(h, logging.FileHandler)
    ]


if __name__ == "__main__":
    main()
