# Backlog

## BUG-001: HTML output contains stdout noise at top of file

**Type:** Bug  
**Priority:** High  
**Status:** Done  

When generating the HTML digest (e.g. `ai-digest --html > file.html`), extraneous stdout output (logging or print statements) appears at the top of the HTML file before the actual HTML content. This pollutes the generated file and can break rendering. All non-HTML output should go to stderr, or be suppressed when `--html` is active.

---

## FEAT-001: Sort articles by age (newest first)

**Type:** Enhancement  
**Priority:** Medium  
**Status:** Done  

Articles in the generated digest should be sorted by publication date in descending order, with the most recent articles appearing first. Currently the ordering does not consistently prioritize recency.

---

## FEAT-002: Web UI for digest management

**Type:** Feature  
**Priority:** Medium  
**Status:** Done  

A local web application that provides:

1. **Digest generation** — A button to regenerate the latest AI news digest on demand.
2. **Blog summary expansion** — If an article is a blog post, display a button to generate a detailed summary of that blog. Once generated, the summary appears inline under the article in an expandable accordion.
3. **Source management** — A UI to review, add, remove, enable, and disable URL data sources (equivalent to the `ai-digest sources` CLI commands).

The web application should be hosted on github (like this example is hosted:   
    https://ubiquitous-carnival-4qpr9nm.pages.github.io/ )

---

## FEAT-003: Email Delivery

**Type:** Feature  
**Priority:** Low  
**Status:** Blocked by Policy  

Automated daily digest delivered to inbox every morning.

**Blocked:** Corporate email policy restricts programmatic sending from personal tools. The overhead of setting up an approved sending path exceeds the value for a personal project. The GitHub Pages site serves the same content.

---

## BUG-002: March 6 digest not sorted newest-first

**Type:** Bug  
**Priority:** High  
**Status:** Done  

The 03-06 digest (`src/AI-News-20260306.html`) shows articles in non-chronological order — oldest articles appear at the top. The article dates jump: Feb 24 → Mar 3 → Mar 2 → Feb 28 → Mar 6 → ... Expected: Mar 6 articles first, descending to oldest.

**Root cause:** The digest was generated before the FEAT-001 sort fix was committed. The sort logic in `scorer.py` is correct now, but the existing HTML file was never regenerated.

**Fix:** Regenerate the 03-06 digest using the current code with the sort fix applied.

---

## BUG-003: URLs in summaries are plain text, not clickable links

**Type:** Bug  
**Priority:** Medium  
**Status:** Done  

When article summaries contain URLs (e.g., the Notion/Claude Code article from Lenny's Newsletter), the URLs render as plain text rather than clickable `<a>` links. The `html_formatter.py` escapes all HTML in summaries via `html.escape()`, which is correct for security, but then doesn't post-process to convert URL patterns back into anchor tags.

**Affected code:** `src/cli/html_formatter.py` — the `summary_esc` variable is escaped but URLs are not linkified afterward.

**Fix:** After escaping, apply a regex to detect `https?://...` patterns in the escaped summary text and wrap them in `<a href="..." target="_blank">` tags.

---

## BUG-004: Bullet points in summaries render inline instead of as a list

**Type:** Bug  
**Priority:** Medium  
**Status:** Done  

When article content contains bullet points (using `•` characters), the summarizer collapses them into a single run of inline text. For example, the Notion article summary shows `• Item1 • Item2 • Item3` all on one line instead of as a formatted bulleted list.

**Affected code:**
1. `src/services/summarizer.py` — `_strip_html()` collapses all whitespace including newlines, losing bullet structure.
2. `src/cli/html_formatter.py` — no post-processing to detect `•` patterns and convert them to `<ul><li>` elements.

**Fix:** In the HTML formatter, detect `•` (or `- `) bullet patterns in summary text and convert them to proper `<ul><li>` HTML lists.

---

## FEAT-004: Auto-transcribe podcast episodes during digest generation

**Type:** Feature  
**Priority:** Medium  
**Status:** Done  

During HTML digest generation, podcast episodes (identified by 🎙️ emoji in title) are automatically transcribed using the existing `podcast_service.py` (yt-dlp + faster-whisper). The transcript summary and full transcript are embedded in the article's expandable accordion, so the static page ships with transcripts already included.

Gracefully skips transcription if podcast dependencies are missing or if the URL is not downloadable audio (e.g., blog show notes pages). In those cases, the existing blog content is preserved in the accordion.

**Related:** `src/services/podcast_service.py`, `src/cli/__main__.py` (`_enrich_podcasts`).
