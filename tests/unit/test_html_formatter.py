"""Tests for html_formatter — content formatting, URL linkification, and bullet conversion."""

import sys
import os
from datetime import date, datetime, timezone

# Allow imports from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from cli.html_formatter import (
    _bullets_to_list,
    _linkify_urls,
    _strip_html_tags,
    format_digest_html,
)
from models.digest import Digest
from models.digest_entry import DigestEntry
from models.news_article import NewsArticle


# ── _strip_html_tags ──


def test_strip_simple_tags():
    assert _strip_html_tags("<p>Hello</p>").strip() == "Hello"


def test_strip_nested_tags():
    result = _strip_html_tags("<div><strong>Bold</strong> text</div>")
    assert "Bold" in result
    assert "text" in result
    assert "<" not in result


def test_strip_preserves_newlines_on_block_tags():
    result = _strip_html_tags("<p>First</p><p>Second</p>")
    assert "First" in result
    assert "Second" in result
    # Should have a newline between paragraphs, not run together
    assert "FirstSecond" not in result


def test_strip_decodes_html_entities():
    result = _strip_html_tags("AT&amp;T &lt;rocks&gt;")
    assert "AT&T" in result
    assert "<rocks>" in result


def test_strip_handles_br_tags():
    result = _strip_html_tags("Line one<br>Line two<br/>Line three")
    assert "Line one" in result
    assert "Line two" in result
    assert "<br" not in result


def test_strip_plain_text_passthrough():
    text = "No HTML here, just plain text."
    assert _strip_html_tags(text) == text


# ── _linkify_urls ──


def test_linkify_converts_url():
    result = _linkify_urls("Visit https://example.com for more")
    assert '<a href="https://example.com"' in result
    assert 'target="_blank"' in result


def test_linkify_preserves_non_url_text():
    text = "No URLs in this text at all"
    assert _linkify_urls(text) == text


def test_linkify_handles_multiple_urls():
    text = "See https://a.com and https://b.com"
    result = _linkify_urls(text)
    assert result.count("<a href=") == 2


# ── _bullets_to_list ──


def test_bullets_converts_to_list():
    text = "Key points: • First • Second • Third"
    result = _bullets_to_list(text)
    assert "<ul>" in result
    assert "<li>First</li>" in result
    assert "<li>Second</li>" in result
    assert "<li>Third</li>" in result


def test_bullets_no_bullets_passthrough():
    text = "No bullet points here."
    assert _bullets_to_list(text) == text


# ── format_digest_html with HTML content (the actual bug) ──

_NOW = datetime(2026, 3, 7, tzinfo=timezone.utc)

# Enough content to pass the 50-char minimum validation
_HTML_CONTENT = (
    '<p><strong><a href="https://example.com">Example Link Title</a></strong></p>'
    "<p>Details here about the article content that is long enough to pass validation.</p>"
)


def _make_digest():
    return Digest(
        digest_id="2026-03-07",
        date=date(2026, 3, 7),
        entries=[],
        sources_fetched=["src1"],
        sources_failed=[],
        total_articles_fetched=1,
        total_articles_curated=0,
        duplicates_removed=0,
        created_at=_NOW,
    )


def _make_entry_article(content=_HTML_CONTENT):
    article = NewsArticle(
        title="Test Article Title Here",
        url="https://example.com/article",
        source_id="test-source",
        published_at=_NOW,
        fetched_at=_NOW,
        content=content,
    )
    entry = DigestEntry(
        article_id=article.article_id,
        summary="Short summary of the article for the digest entry listing.",
        summary_method="frequency",
        compression_ratio=0.3,
        processed_at=_NOW,
    )
    return entry, article


def test_expanded_content_no_raw_html_tags():
    """Verify the bug fix: expanded content must not show literal HTML tags like <p>, <strong>."""
    digest = _make_digest()
    entry, article = _make_entry_article()
    result = format_digest_html(digest, [(entry, article)])
    # The expanded body should not contain escaped HTML tags rendered as text
    assert "&lt;p&gt;" not in result
    assert "&lt;strong&gt;" not in result
    assert "&lt;a " not in result


def test_expanded_content_preserves_text():
    """Expanded content should keep the readable text."""
    digest = _make_digest()
    entry, article = _make_entry_article()
    result = format_digest_html(digest, [(entry, article)])
    assert "Example Link Title" in result
    assert "Details here about the article content" in result


def test_expanded_content_with_blockquote():
    """Content with blockquote tags should strip them cleanly."""
    digest = _make_digest()
    bq_content = (
        "<p>Intro text for the article.</p>"
        "<blockquote><p>AI models are increasingly commodified and this is a long enough sentence.</p></blockquote>"
        "<p>Conclusion paragraph with enough text to pass validation checks.</p>"
    )
    entry, article = _make_entry_article(content=bq_content)
    result = format_digest_html(digest, [(entry, article)])
    assert "&lt;blockquote&gt;" not in result
    assert "AI models are increasingly commodified" in result
    assert "Conclusion paragraph" in result
