"""Digest formatter for styled HTML output."""

import html
import re
from datetime import datetime

from models.digest import Digest
from models.digest_entry import DigestEntry
from models.news_article import NewsArticle
from services.summarizer import clean_for_summary


def format_digest_html(
    digest: Digest,
    entries: list[tuple[DigestEntry, NewsArticle]],
) -> str:
    """
    Format digest as styled HTML page.

    Args:
        digest: Digest metadata
        entries: List of (DigestEntry, NewsArticle) tuples

    Returns:
        Complete HTML document string
    """
    total_sources = len(digest.sources_fetched) + len(digest.sources_failed)
    date_display = digest.date

    articles_html = ""
    if not entries:
        articles_html = (
            '<div class="empty">No new AI news articles found.</div>'
        )
    else:
        for i, (entry, article) in enumerate(entries, 1):
            title_esc = html.escape(article.title)
            url_esc = html.escape(article.url)
            source_esc = html.escape(article.source_id)
            pub_str = _format_datetime(article.published_at) if article.published_at else ""
            summary_esc = html.escape(entry.summary)
            summary_esc = _linkify_urls(summary_esc)
            summary_esc = _bullets_to_list(summary_esc)

            # Convert summary to paragraphs on sentence boundaries
            summary_html = summary_esc.replace(". ", ".</span> <span>")
            summary_html = f"<span>{summary_html}</span>"

            # Expandable full content accordion
            expand_html = ""
            cleaned_content = clean_for_summary(article.content) if article.content else ""
            if not cleaned_content and article.content:
                cleaned_content = _strip_html_tags(article.content)

            if cleaned_content and len(cleaned_content) > len(entry.summary) + 50:
                content_esc = html.escape(cleaned_content)
                content_esc = _linkify_urls(content_esc)
                content_esc = _bullets_to_list(content_esc)
                # Split into paragraphs for readability
                paragraphs = [p.strip() for p in content_esc.split("\n") if p.strip()]
                content_body = "".join(f"<p>{p}</p>" for p in paragraphs[:20])
                expand_html = (
                    '\n          <details class="expand-content">'
                    "<summary>Expand full summary</summary>"
                    f'<div class="expanded-body">{content_body}</div>'
                    "</details>"
                )

            articles_html += f"""
      <article>
        <div class="article-number">{i}</div>
        <div class="article-content">
          <h2><a href="{url_esc}" target="_blank">{title_esc}</a></h2>
          <div class="meta">
            <span class="source">{source_esc}</span>
            <span class="date">{pub_str}</span>
          </div>
          <p class="summary">{summary_html}</p>{expand_html}
        </div>
      </article>"""

    cache_note = ""
    if digest.cache_status == "cached":
        cache_note = ' <span class="cache-badge">CACHED</span>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Daily Digest - {date_display}</title>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e1e4ed;
    --text-dim: #8b8fa3;
    --accent: #6c8cff;
    --accent-glow: #4a6bff;
    --number: #3d4260;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont,
                 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.65;
    min-height: 100vh;
  }}

  .container {{
    max-width: 760px;
    margin: 0 auto;
    padding: 40px 24px 60px;
  }}

  /* ── Header ── */
  header {{
    text-align: center;
    margin-bottom: 48px;
    padding-bottom: 32px;
    border-bottom: 1px solid var(--border);
  }}

  header .logo {{
    font-size: 13px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 8px;
  }}

  header h1 {{
    font-size: 28px;
    font-weight: 300;
    letter-spacing: -0.5px;
    margin-bottom: 12px;
  }}

  header .subtitle {{
    font-size: 14px;
    color: var(--text-dim);
  }}

  .cache-badge {{
    display: inline-block;
    font-size: 10px;
    letter-spacing: 1px;
    padding: 2px 8px;
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--text-dim);
    vertical-align: middle;
    margin-left: 8px;
  }}

  /* ── Articles ── */
  article {{
    display: flex;
    gap: 20px;
    padding: 28px 0;
    border-bottom: 1px solid var(--border);
  }}

  article:last-child {{
    border-bottom: none;
  }}

  .article-number {{
    flex-shrink: 0;
    width: 32px;
    font-size: 15px;
    font-weight: 600;
    color: var(--number);
    padding-top: 2px;
    text-align: right;
  }}

  .article-content {{
    flex: 1;
    min-width: 0;
  }}

  .article-content h2 {{
    font-size: 18px;
    font-weight: 500;
    line-height: 1.4;
    margin-bottom: 8px;
  }}

  .article-content h2 a {{
    color: var(--text);
    text-decoration: none;
    transition: color 0.15s;
  }}

  .article-content h2 a:hover {{
    color: var(--accent);
  }}

  .meta {{
    display: flex;
    gap: 16px;
    font-size: 13px;
    color: var(--text-dim);
    margin-bottom: 12px;
  }}

  .source {{
    color: var(--accent);
    font-weight: 500;
  }}

  .summary {{
    font-size: 15px;
    color: var(--text-dim);
    line-height: 1.7;
  }}

  .summary a, .expanded-body a {{
    color: var(--accent);
    text-decoration: none;
    word-break: break-all;
  }}

  .summary a:hover, .expanded-body a:hover {{
    text-decoration: underline;
  }}

  .summary ul, .expanded-body ul {{
    margin: 8px 0;
    padding-left: 20px;
  }}

  .summary li, .expanded-body li {{
    margin-bottom: 4px;
  }}

  .empty {{
    text-align: center;
    color: var(--text-dim);
    padding: 60px 0;
    font-size: 16px;
  }}

  /* ── Expand accordion ── */
  .expand-content {{
    margin-top: 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
  }}

  .expand-content summary {{
    cursor: pointer;
    padding: 8px 14px;
    font-size: 13px;
    color: var(--accent);
    background: var(--surface);
    user-select: none;
    list-style: none;
  }}

  .expand-content summary::-webkit-details-marker {{
    display: none;
  }}

  .expand-content summary::before {{
    content: '\u25b6 ';
    font-size: 10px;
    margin-right: 6px;
    display: inline-block;
    transition: transform 0.15s;
  }}

  .expand-content[open] summary::before {{
    transform: rotate(90deg);
  }}

  .expanded-body {{
    padding: 14px 16px;
    font-size: 14px;
    line-height: 1.7;
    color: var(--text-dim);
    background: var(--bg);
  }}

  .expanded-body p {{
    margin-bottom: 10px;
  }}

  .expanded-body p:last-child {{
    margin-bottom: 0;
  }}

  /* ── Footer ── */
  footer {{
    margin-top: 40px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    text-align: center;
    font-size: 13px;
    color: var(--text-dim);
  }}

  footer .stats {{
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-bottom: 8px;
  }}

  footer .stats span {{
    white-space: nowrap;
  }}
</style>
</head>
<body>
<div class="container">

  <header>
    <div class="logo">AI Daily Digest</div>
    <h1>{date_display}{cache_note}</h1>
    <div class="subtitle">{len(entries)} curated articles &middot; {len(digest.sources_fetched)} of {total_sources} sources</div>
  </header>

  <main>{articles_html}
  </main>

  <footer>
    <div class="stats">
      <span>Curated {digest.total_articles_curated} of {digest.total_articles_fetched}</span>
      <span>&middot;</span>
      <span>{len(digest.sources_fetched)}/{total_sources} sources</span>
    </div>
    <div>Generated by AI Daily Digest</div>
  </footer>

</div>
</body>
</html>"""


_TAG_RE = re.compile(r'<[^>]+>')


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags from text, preserving readable content."""
    # Replace block-level closing tags with newlines to preserve structure
    text = re.sub(r'</(?:p|div|li|br|h[1-6]|blockquote|tr)\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = _TAG_RE.sub('', text)
    # Decode common HTML entities
    text = html.unescape(text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


_URL_RE = re.compile(r'(https?://[^\s<>&"]+)')


def _linkify_urls(text: str) -> str:
    """Convert plain-text URLs in already-escaped HTML into clickable links."""
    return _URL_RE.sub(r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)


def _bullets_to_list(text: str) -> str:
    """Convert bullet patterns (• item) into an HTML unordered list."""
    parts = re.split(r'\s*•\s*', text)
    if len(parts) <= 1:
        return text
    # First part is the text before any bullets
    leading = parts[0]
    items = ''.join(f'<li>{p.strip()}</li>' for p in parts[1:] if p.strip())
    return f'{leading}<ul>{items}</ul>'


def _format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%b %d, %Y &middot; %H:%M UTC")
