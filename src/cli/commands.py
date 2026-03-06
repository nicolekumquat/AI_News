"""CLI argument parser and command handling with subcommand support."""

import argparse
import sys
from datetime import date, datetime


def build_parser():
    """
    Build the top-level argument parser with subcommands.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="ai-digest",
        description="Daily AI news aggregation and digest tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-digest                          # Today's digest
  ai-digest --date 2025-01-23        # Specific date
  ai-digest sources list             # List configured sources
  ai-digest sources add --name "My Blog" --url https://blog.com/feed.xml
  ai-digest podcast https://example.com/episode.mp3
        """,
    )

    # Top-level digest options (default behaviour when no subcommand given)
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Date for digest (default: today)",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        default=False,
        help="Output as styled HTML instead of plain text",
    )

    subparsers = parser.add_subparsers(dest="command")

    # ── sources subcommand ──────────────────────────────────────────────
    sources_parser = subparsers.add_parser(
        "sources",
        help="Manage news sources",
        description="List, add, remove, enable, or disable news sources.",
    )
    sources_sub = sources_parser.add_subparsers(dest="sources_action")

    # sources list
    sources_sub.add_parser("list", help="List all configured sources")

    # sources add
    add_parser = sources_sub.add_parser("add", help="Add a new custom source")
    add_parser.add_argument("--name", required=True, help="Display name for the source")
    add_parser.add_argument("--url", required=True, help="Feed/API URL")
    add_parser.add_argument(
        "--method",
        default="rss",
        choices=["rss", "api", "html"],
        help="Fetch method (default: rss)",
    )

    # sources remove
    remove_parser = sources_sub.add_parser("remove", help="Remove a custom source")
    remove_parser.add_argument("source_id", help="ID of the source to remove")

    # sources enable
    enable_parser = sources_sub.add_parser("enable", help="Enable a source")
    enable_parser.add_argument("source_id", help="ID of the source to enable")

    # sources disable
    disable_parser = sources_sub.add_parser("disable", help="Disable a source")
    disable_parser.add_argument("source_id", help="ID of the source to disable")

    # ── podcast subcommand ──────────────────────────────────────────────
    podcast_parser = subparsers.add_parser(
        "podcast",
        help="Summarize a podcast episode",
        description="Download, transcribe, and summarize a podcast episode.",
    )
    podcast_parser.add_argument("url", help="Podcast episode URL")
    podcast_parser.add_argument(
        "--model",
        default=None,
        choices=["tiny", "base", "small", "medium"],
        help="Whisper model size (default: from config or 'base')",
    )

    return parser


def parse_args(args=None):
    """
    Parse command-line arguments.

    Args:
        args: List of arguments (None = sys.argv)

    Returns:
        Parsed arguments namespace
    """
    parser = build_parser()
    parsed = parser.parse_args(args)

    # If no subcommand, this is a digest request — validate date
    if parsed.command is None:
        if parsed.date:
            try:
                parsed_date = datetime.strptime(parsed.date, "%Y-%m-%d").date()
                if parsed_date > date.today():
                    print(
                        f"Error: Cannot generate digest for future date: {parsed.date}",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                parsed.date = parsed_date
            except ValueError:
                print(
                    f"Error: Invalid date format. Expected YYYY-MM-DD, got {parsed.date}",
                    file=sys.stderr,
                )
                print("Usage: ai-digest [--date YYYY-MM-DD]", file=sys.stderr)
                sys.exit(1)
        else:
            parsed.date = date.today()

    return parsed


def format_date(date_obj: date) -> str:
    """Format date as YYYY-MM-DD."""
    return date_obj.strftime("%Y-%m-%d")
