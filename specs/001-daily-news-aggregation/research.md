# Research Document: Daily News Aggregation

**Feature**: Daily News Aggregation  
**Branch**: `001-daily-news-aggregation`  
**Date**: 2025-01-23 | **Updated**: 2026-03-04

This document resolves all "NEEDS CLARIFICATION" items from the Technical Context section and documents key technology decisions.

> **2026-03-04 Update**: Added research for Source Management (§7) and Podcast Summarization (§8) features.

---

## 1. Primary Dependencies

### Decision: Core Libraries

| Category | Library | Type | Justification |
|----------|---------|------|---------------|
| **HTTP Client** | `requests` + `urllib3.Retry` | External (~2MB) | Built-in retry with exponential backoff matches FR-009 exactly (3 retries: 1s, 2s, 4s). Simple, battle-tested, synchronous (perfect for CLI tool). |
| **Text Similarity** | `difflib.SequenceMatcher` | **Stdlib** | Provides 0.0-1.0 similarity ratio directly usable for 75% threshold. Zero deps, fast enough for ≤100 articles/day O(n²) comparisons. |
| **RSS/Feed Parsing** | `feedparser` | External (~100KB) | Industry standard for RSS/Atom parsing. Handles all feed variants (RSS 0.9x, 1.0, 2.0, Atom, RDF). Robust against malformed feeds (critical for diverse blog sources). |
| **HTML Parsing** | `beautifulsoup4` + `lxml` | External (~5MB) | CSS selector support for targeted content extraction from blogs. Curated source list makes per-source selectors maintainable. |
| **Config Loading** | `json` + `tomllib` | **Stdlib** | TOML support built into Python 3.11+ via `tomllib`. Recommend TOML instead of YAML to avoid external dependency. JSON supported via stdlib `json`. |

**Total external dependencies**: 3 packages (`requests`, `feedparser`, `beautifulsoup4`+`lxml`)

### `requirements.txt`
```
requests>=2.31,<3
feedparser>=6.0,<7
beautifulsoup4>=4.12,<5
lxml>=5.0,<6
pytest>=7.4,<8
ruff>=0.1,<1
```

### Rationale

**Simplicity Principle Compliance**:
- Stdlib preferred where viable: `difflib`, `json`, `tomllib` used instead of external alternatives
- Each external dependency justified by constitution requirements:
  - `requests`: Retry logic mandated by FR-009
  - `feedparser`: Content fetching required by FR-001, robust feed parsing critical for diverse sources
  - `beautifulsoup4`: Content extraction from non-RSS sources mandated by source list

**Alternatives Considered and Rejected**:
- ❌ **scikit-learn for similarity**: Would add 200MB+ (numpy/scipy/sklearn). YAGNI for 100 articles/day.
- ❌ **PyYAML for config**: External dep. TOML is stdlib in Python 3.11+ and equally human-readable.
- ❌ **httpx**: No built-in retry support. Would need `resilient-httpx` (additional dep).
- ❌ **trafilatura for article extraction**: 15+ transitive deps. Overkill for curated, fixed source list.

---

## 2. News Source Fetching Strategies

### Decision: Source-Specific Fetch Methods

All sources can be fetched **without authentication** using ~11 requests per daily run.

| Source | Method | Endpoint/URL | Rate Limit | Auth |
|--------|--------|--------------|------------|------|
| **HackerNews** | Algolia Search API (JSON) | `https://hn.algolia.com/api/v1/search_by_date` | None (1s delay recommended) | None |
| **Reddit r/MachineLearning** | Native `.json` endpoint | `https://www.reddit.com/r/MachineLearning/top.json?t=day` | 10 req/min (2s delay) | None (custom User-Agent required) |
| **ArXiv** | REST API (Atom XML) | `http://export.arxiv.org/api/query` | 3s between requests (enforced) | None |
| **Thought Leader Blogs** | RSS feeds via `feedparser` | See catalog below | Varies (1s delay) | None |

### HackerNews — Algolia Search API

**Query for AI-related posts (last 48h, ≥5 points)**:
```
https://hn.algolia.com/api/v1/search_by_date?query=AI+OR+"artificial+intelligence"+OR+"machine+learning"+OR+LLM+OR+GPT+OR+Claude&tags=story&numericFilters=created_at_i>{UNIX_48H_AGO},points>5&hitsPerPage=50
```

**Implementation pattern**:
```python
import requests
import time

def fetch_hn_ai_posts(hours_ago=48, min_points=5, max_results=50):
    cutoff = int(time.time()) - (hours_ago * 3600)
    url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {
        "query": 'AI OR "artificial intelligence" OR "machine learning" OR LLM OR GPT',
        "tags": "story",
        "numericFilters": f"created_at_i>{cutoff},points>{min_points}",
        "hitsPerPage": max_results,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["hits"]
```

### Reddit r/MachineLearning — Native JSON Endpoint

**Critical**: Must set custom `User-Agent` or get HTTP 429.

**Implementation pattern**:
```python
def fetch_reddit_ml(sort="top", time_filter="day", limit=50):
    url = f"https://www.reddit.com/r/MachineLearning/{sort}.json"
    headers = {
        "User-Agent": "ai-daily-digest:v1.0 (local CLI tool; once-daily fetch)"
    }
    params = {"t": time_filter, "limit": limit}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    posts = resp.json()["data"]["children"]
    return [
        {
            "title": p["data"]["title"],
            "url": p["data"]["url"],
            "published": p["data"]["created_utc"],
            "selftext": p["data"].get("selftext", ""),
        }
        for p in posts
    ]
```

### ArXiv — REST API with Client-Side Date Filtering

**Query for AI/ML papers** (cs.AI, cs.LG, cs.CL categories):
```
http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=100
```

**Note**: API does not support date filtering. Fetch sorted by date descending, filter client-side by `<published>` tag.

**Implementation pattern**:
```python
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}

def fetch_arxiv_ai_papers(hours_ago=48, max_results=100):
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    
    root = ET.fromstring(resp.text)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    papers = []
    
    for entry in root.findall("atom:entry", ARXIV_NS):
        published = entry.find("atom:published", ARXIV_NS).text
        pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        if pub_dt < cutoff:
            break  # sorted descending, stop when too old
        papers.append({
            "title": entry.find("atom:title", ARXIV_NS).text.strip(),
            "summary": entry.find("atom:summary", ARXIV_NS).text.strip(),
            "published": published,
            "url": entry.find("atom:id", ARXIV_NS).text,
        })
    return papers
```

### Thought Leader & Company Blogs — RSS Feeds

**Source Catalog**:

| Source | Feed URL |
|--------|----------|
| Sam Schillace (MS Deputy CTO) | `https://sundaylettersfromsam.substack.com/feed` |
| Ethan Mollick (One Useful Thing) | `https://oneusefulthing.substack.com/feed` |
| Andrew Ng (The Batch) | `https://www.deeplearning.ai/the-batch/feed/` |
| OpenAI News | `https://openai.com/news/rss.xml` |
| Google DeepMind | `https://deepmind.google/blog/rss.xml` |
| Anthropic Engineering | `https://raw.githubusercontent.com/conoro/anthropic-engineering-rss-feed/main/anthropic_engineering_rss.xml` (community-maintained) |
| Meta AI Research | `https://research.facebook.com/feed` |

**Implementation pattern**:
```python
import feedparser
from datetime import datetime, timedelta, timezone
from time import mktime

def fetch_rss_feed(feed_url, source_name, hours_ago=48):
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    articles = []
    
    for entry in feed.entries:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_dt = datetime.fromtimestamp(
                mktime(entry.published_parsed), tz=timezone.utc
            )
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub_dt = datetime.fromtimestamp(
                mktime(entry.updated_parsed), tz=timezone.utc
            )
        else:
            continue
        
        if pub_dt < cutoff:
            continue
        
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": pub_dt.isoformat(),
            "summary": entry.get("summary", ""),
            "source": source_name,
        })
    return articles
```

### Unified Error Handling (FR-009 Compliance)

**3 retries with exponential backoff (1s, 2s, 4s)**:
```python
import time
import logging

def fetch_with_retry(fetch_fn, source_name, max_retries=3):
    """Retry with exponential backoff per FR-009."""
    delays = [1, 2, 4]
    for attempt in range(max_retries):
        try:
            return fetch_fn()
        except Exception as e:
            logging.warning(f"{source_name} attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delays[attempt])
    logging.error(f"{source_name}: all {max_retries} retries exhausted")
    return []
```

---

## 3. Text Similarity & Deduplication

### Decision: difflib.SequenceMatcher with Combined Title + Content

**Algorithm**: Compute similarity ratio on concatenated `title + content` using stdlib `difflib.SequenceMatcher`. Apply 75% threshold per FR-004.

**Implementation pattern**:
```python
from difflib import SequenceMatcher

def are_duplicates(article_a, article_b, threshold=0.75):
    """Return True if articles are duplicates (≥75% similar)."""
    text_a = article_a.title + " " + article_a.content
    text_b = article_b.title + " " + article_b.content
    similarity = SequenceMatcher(None, text_a, text_b).ratio()
    return similarity >= threshold
```

**Deduplication strategy**:
1. Sort articles by publication date (newest first)
2. For each article, compare against all previously accepted articles
3. If similarity ≥ 75%, skip as duplicate
4. If similarity < 75%, accept and add to accepted list

**Complexity**: O(n²) for n articles. At 100 articles/day: ~4,950 comparisons. `difflib` handles this in <100ms.

**Rationale**:
- Stdlib-only (no external deps)
- Direct 0.0-1.0 ratio maps to 75% threshold
- Fast enough for daily volumes
- Handles near-duplicates (reworded text) better than keyword overlap

**Alternatives Rejected**:
- ❌ **scikit-learn TF-IDF + cosine similarity**: More semantically robust but adds 200MB+ deps. Violates simplicity.
- ❌ **Custom cosine similarity with Counter**: Viable stdlib alternative but worse at near-duplicate detection than SequenceMatcher.

---

## 4. Extractive Summarization

### Decision: Frequency-Based Sentence Scoring with Position Weighting

**Algorithm**: 
1. Count word frequencies (excluding stopwords)
2. Score each sentence by summing word frequencies, normalized by sentence length
3. Apply positional boost: 1.5× for first sentence, 1.2× for last sentence
4. Select top 50% of sentences by score, preserving original order

**Implementation pattern**:
```python
import re
from collections import Counter

def frequency_summarize(text, ratio=0.5):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 2:
        return text
    
    # Tokenize, remove stopwords
    STOPWORDS = {'the','a','an','is','are','was','were','in','on','at','to','for',
                 'of','and','or','but','with','by','from','that','this','it','as',
                 'be','has','have','had','not','no','do','does','did','will','would',
                 'could','should','can','may','might','its','his','her','their','our'}
    words = re.findall(r'\b[a-z]+\b', text.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    freq = Counter(words)
    
    # Score sentences
    scored = []
    for i, sent in enumerate(sentences):
        sent_words = re.findall(r'\b[a-z]+\b', sent.lower())
        score = sum(freq.get(w, 0) for w in sent_words)
        score = score / max(len(sent_words), 1)  # normalize
        
        # Positional boost
        if i == 0:
            score *= 1.5
        elif i == len(sentences) - 1:
            score *= 1.2
        
        scored.append((score, i, sent))
    
    # Select top N sentences
    n = max(1, int(len(sentences) * ratio))
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:n]
    top.sort(key=lambda x: x[1])  # preserve order
    return ' '.join(s[2] for s in top)
```

**Fallback for edge cases**:
```python
def fallback_lead_summary(text, ratio=0.5):
    """Fallback: first N sentences (for short texts or failures)."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    n = max(1, int(len(sentences) * ratio))
    return ' '.join(sentences[:n])

def smart_summarize(text, ratio=0.5):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 3:
        return fallback_lead_summary(text, ratio)
    try:
        return frequency_summarize(text, ratio)
    except Exception:
        return fallback_lead_summary(text, ratio)
```

**Validation (FR-011 compliance)**:
```python
def validate_summary(original, summary):
    compression = len(summary) / max(len(original), 1)
    is_copy = summary.strip() == original.strip()
    is_too_long = compression > 0.55
    
    return {
        'compression_ratio': round(compression, 3),
        'is_copy': is_copy,
        'is_valid': not is_copy and not is_too_long and compression > 0.05,
    }
```

**Rationale**:
- **Stdlib-only**: Uses only `re` and `collections.Counter`
- **50% target**: Direct `ratio` parameter control
- **News-optimized**: Position weighting leverages inverted pyramid structure
- **Deterministic**: Same input → same output (easy to test)
- **Graceful degradation**: Fallback to first-N sentences

**Alternatives Rejected**:
- ❌ **TextRank (graph-based)**: Requires `networkx` dependency. O(n²) complexity adds no benefit for news content.
- ❌ **ML-based summarization**: Violates simplicity principle and constitution constraint (no external AI services).

---

## 5. Technology Choices Summary

| Requirement | Technology | Type | Reason |
|-------------|-----------|------|--------|
| **HTTP with retry** | `requests` + `urllib3.Retry` | External | Built-in exponential backoff matches FR-009 |
| **Text similarity** | `difflib.SequenceMatcher` | Stdlib | Direct ratio for 75% threshold, zero deps |
| **RSS parsing** | `feedparser` | External | Industry standard, handles all feed variants |
| **HTML parsing** | `beautifulsoup4` + `lxml` | External | CSS selectors for targeted extraction |
| **Config loading** | `json` + `tomllib` | Stdlib | TOML built into Python 3.11+ |
| **Summarization** | Frequency-based scoring | Stdlib | Simple, effective, no ML required |
| **Deduplication** | SequenceMatcher on title+content | Stdlib | Fast enough for daily volumes |

**All choices comply with constitution Simplicity principle**: Stdlib preferred where viable, external deps minimized and justified.

---

## 6. Performance Considerations

| Metric | Target | Expected |
|--------|--------|----------|
| Digest retrieval (cached) | <1s | ~100-200ms (file read + parse) |
| Digest retrieval (fresh fetch) | <5s | ~20-30s (11 API calls with delays) |
| Article processing | <10 min for 100 articles | ~2-3 min (dedup O(n²), summarization O(n)) |
| Cache storage | 30 days × 100 articles | ~3MB (JSON files) |

**Performance not a concern at this scale**. All O(n²) operations (deduplication comparisons) remain fast at 100 articles/day.

---

## 7. Source Management

### 7.1 Research: CLI Source Management Patterns

**Question**: How should source management commands be structured in the CLI?

**Decision**: Use `ai-digest sources <action>` subcommand pattern.

**Rationale**: argparse supports subparsers natively. A `sources` subcommand group keeps source management distinct from digest generation while sharing the same entry point. This follows standard CLI conventions (e.g., `git remote add/remove`, `docker image ls/rm`).

**Subcommands**:

| Command | Description |
|---------|-------------|
| `ai-digest sources list` | Show all configured sources with status |
| `ai-digest sources add --name "Name" --url URL [--method rss\|api\|html]` | Add a custom source |
| `ai-digest sources remove <source_id>` | Remove a custom source (built-ins cannot be removed) |
| `ai-digest sources enable <source_id>` | Enable a source |
| `ai-digest sources disable <source_id>` | Disable a source |

**Implementation Pattern**:
```python
import argparse

def build_parser():
    parser = argparse.ArgumentParser(prog="ai-digest")
    subparsers = parser.add_subparsers(dest="command")
    
    # Default (no subcommand) = generate digest
    # Sources subcommand group
    sources_parser = subparsers.add_parser("sources", help="Manage news sources")
    sources_sub = sources_parser.add_subparsers(dest="action")
    
    # ai-digest sources list
    sources_sub.add_parser("list", help="List all sources")
    
    # ai-digest sources add
    add_parser = sources_sub.add_parser("add", help="Add a custom source")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--url", required=True)
    add_parser.add_argument("--method", choices=["rss", "api", "html"], default="rss")
    
    # ai-digest sources remove <source_id>
    rm_parser = sources_sub.add_parser("remove", help="Remove a custom source")
    rm_parser.add_argument("source_id")
    
    # ai-digest sources enable/disable <source_id>
    en_parser = sources_sub.add_parser("enable", help="Enable a source")
    en_parser.add_argument("source_id")
    dis_parser = sources_sub.add_parser("disable", help="Disable a source")
    dis_parser.add_argument("source_id")
    
    return parser
```

### 7.2 Research: Source Persistence Strategy

**Question**: How should user source modifications be persisted?

**Decision**: Store user source overrides in `~/.ai-digest/config.toml` using the existing `[[sources.custom]]` array and `[sources]` section. Source enable/disable state tracked via the `enabled` list in config.

**Rationale**:
- The config schema already supports `[[sources.custom]]` for user-added sources
- The `[sources] enabled = [...]` list already controls which sources are active
- Modifying config file directly is the simplest approach, with built-in backup
- Avoids adding a separate persistence layer (YAGNI)

**Source Manager Operations**:

| Operation | Config Effect |
|-----------|--------------|
| `add` | Append to `[[sources.custom]]` array, add to `enabled` list |
| `remove` | Remove from `[[sources.custom]]` array, remove from `enabled` list. Built-in sources cannot be removed. |
| `enable` | Add `source_id` to `[sources] enabled` list |
| `disable` | Remove `source_id` from `[sources] enabled` list |
| `list` | Read built-in sources + custom sources, show enabled status |

**Source ID Generation for `add`**:
- Auto-generate from name: lowercase, replace spaces/special chars with hyphens, strip non-alphanumeric
- Example: "My AI Blog" → `my-ai-blog`
- Validate uniqueness against all sources (built-in + custom)

**Config Save Strategy**:
- Read existing config, modify in-memory, write back
- Since `tomllib` (stdlib) is read-only, use `tomli_w` for TOML writing or fall back to JSON format
- **Decision**: Use JSON for user config writes. TOML reading is supported via `tomllib`, but writing requires an external package (`tomli_w`). Since config already supports JSON fallback, writing changes to `config.json` is the simplest approach.

**Alternatives Considered**:
- ❌ **tomli_w for TOML writing**: External dependency for a rarely-used operation. Violates simplicity.
- ❌ **Separate sources.json file**: Additional file to manage. Config already handles this.
- ❌ **SQLite for source storage**: Massive overkill for <50 records. YAGNI.

### 7.3 Research: Built-in vs Custom Source Protection

**Decision**: Built-in sources (from `src/config/sources.py`) can be enabled/disabled but **not removed**. Only custom (user-added) sources can be removed.

**Rationale**: Built-in sources represent the curated default experience. Users should be able to mute them without losing the ability to re-enable later. Removing built-in sources would require a reset mechanism — unnecessary complexity.

---

## 8. Podcast Summarization

### 8.1 Research: Podcast Audio Extraction (NEEDS CLARIFICATION → RESOLVED)

**Question**: How to download podcast audio from a URL?

**Decision**: Use `yt-dlp` for audio extraction from podcast URLs.

**Rationale**:
- `yt-dlp` supports 1000+ sites including YouTube, Spotify episode pages, SoundCloud, Apple Podcasts web player, and direct audio URLs
- Handles format selection, extraction, and conversion to common audio formats
- Single dependency replaces what would otherwise be many site-specific scrapers
- Already widely used in Python audio/video tooling
- Supports extracting audio-only streams (saves bandwidth and disk space)

**Implementation Pattern**:
```python
import subprocess
import tempfile
import os

def download_podcast_audio(url: str, output_dir: str = None) -> str:
    """Download podcast audio and return path to audio file."""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ai-digest-podcast-")
    
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",  # wav for whisper compatibility
        "--audio-quality", "0",   # best quality
        "--output", output_template,
        "--no-playlist",          # single episode only
        url,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Audio download failed: {result.stderr}")
    
    # Find the downloaded file
    for f in os.listdir(output_dir):
        if f.endswith(".wav"):
            return os.path.join(output_dir, f)
    
    raise FileNotFoundError("No audio file produced")
```

**Alternatives Considered**:
- ❌ **requests + BeautifulSoup to scrape audio URL**: Only works for direct MP3 links or simple pages. Podcast hosting platforms use JavaScript rendering, CDN redirects, and embed players.
- ❌ **podcastparser**: Only parses RSS feeds, doesn't download audio from episode URLs.
- ❌ **ffmpeg directly**: Handles format conversion but not URL extraction from web pages.

### 8.2 Research: Speech-to-Text Transcription (NEEDS CLARIFICATION → RESOLVED)

**Question**: Which local speech-to-text solution to use?

**Decision**: Use `faster-whisper` (CTranslate2-based Whisper implementation).

**Rationale**:
- Local-only (satisfies constitution constraint — no cloud APIs)
- `faster-whisper` is 4x faster than OpenAI's `openai-whisper` with lower memory usage
- Uses CTranslate2 for efficient CPU inference (no GPU required)
- Supports all Whisper model sizes (tiny → large-v3)
- Default to `base` model for balance of speed and accuracy (~1GB RAM, ~10x real-time on CPU)
- Can upgrade to `small` or `medium` if user needs better accuracy
- Handles English transcription well (matches project scope)

**Implementation Pattern**:
```python
from faster_whisper import WhisperModel

def transcribe_audio(audio_path: str, model_size: str = "base") -> str:
    """Transcribe audio file to text using local Whisper model."""
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(audio_path, language="en")
    
    transcript = " ".join(segment.text.strip() for segment in segments)
    return transcript
```

**Model Size Trade-offs**:

| Model | Size | RAM | Speed (CPU) | Accuracy |
|-------|------|-----|-------------|----------|
| `tiny` | 39MB | ~400MB | ~32x real-time | Basic |
| `base` | 74MB | ~1GB | ~16x real-time | Good |
| `small` | 244MB | ~2GB | ~6x real-time | Better |
| `medium` | 769MB | ~5GB | ~2x real-time | Great |

**Default**: `base` — good accuracy for English podcast content, fast enough for typical 30-60 minute episodes (transcribes in 2-4 minutes on modern CPU).

**Model Download**: `faster-whisper` downloads the model on first use and caches it in `~/.cache/huggingface/`. Size: ~74MB for `base`.

**Alternatives Considered**:
- ❌ **openai-whisper**: 4x slower, higher memory usage, requires PyTorch (~2GB). `faster-whisper` provides identical accuracy with CTranslate2.
- ❌ **whisper.cpp / python-whispercpp**: Good performance but Python bindings are less mature. `faster-whisper` has a cleaner Python API.
- ❌ **vosk**: Smaller models but lower accuracy for long-form podcast content. Better suited for real-time streaming.
- ❌ **Cloud APIs (OpenAI, Google, AWS)**: Violates constitution local-only constraint.

### 8.3 Research: Podcast Summarization Pipeline

**Decision**: Three-stage pipeline: Download → Transcribe → Summarize.

**Pipeline**:
1. **Download**: `yt-dlp` extracts audio from podcast URL → WAV file
2. **Transcribe**: `faster-whisper` converts audio to text → raw transcript
3. **Summarize**: Reuse existing `frequency_summarize()` from `src/services/summarizer.py` → concise summary

**Why reuse existing summarizer**: The existing frequency-based extractive summarizer works well on structured text. Podcast transcripts are essentially spoken text — similar enough in structure. The summarizer's sentence scoring with positional weighting applies well to podcast content where key points are often stated at the beginning and end of segments.

**Transcript preprocessing** (before summarization):
- Remove filler words (um, uh, like, you know)
- Collapse repeated whitespace
- Split into sentences (Whisper output may lack punctuation — add sentence boundaries at natural pauses > 1s)

**Implementation Pattern**:
```python
import re
import os
import tempfile

def summarize_podcast(url: str, model_size: str = "base") -> dict:
    """Full pipeline: download, transcribe, summarize a podcast."""
    tmp_dir = tempfile.mkdtemp(prefix="ai-digest-podcast-")
    
    try:
        # Stage 1: Download
        audio_path = download_podcast_audio(url, output_dir=tmp_dir)
        
        # Stage 2: Transcribe
        raw_transcript = transcribe_audio(audio_path, model_size=model_size)
        
        # Stage 3: Clean + Summarize
        cleaned = clean_transcript(raw_transcript)
        summary = frequency_summarize(cleaned, ratio=0.3)  # more aggressive for long transcripts
        
        return {
            "url": url,
            "transcript_length": len(raw_transcript),
            "summary": summary,
            "compression_ratio": len(summary) / max(len(cleaned), 1),
        }
    finally:
        # Clean up temp audio files
        for f in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f))
        os.rmdir(tmp_dir)


def clean_transcript(text: str) -> str:
    """Clean raw transcript of filler words and formatting issues."""
    # Remove common filler words
    fillers = r'\b(um|uh|like|you know|I mean|sort of|kind of|basically|actually|literally)\b'
    text = re.sub(fillers, '', text, flags=re.IGNORECASE)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

### 8.4 Research: New Dependencies for Podcast Feature

| Package | Version | Size | Purpose | Justification |
|---------|---------|------|---------|---------------|
| `yt-dlp` | `>=2024.1,<2026` | ~15MB | Audio extraction from URLs | Only tool that handles diverse podcast hosting platforms |
| `faster-whisper` | `>=1.0,<2` | ~50MB + model | Local speech-to-text | Fastest local Whisper implementation, no GPU required |

**Total new deps**: 2 packages (+ transitive: `ctranslate2`, `tokenizers`, `huggingface_hub`)

**Constitution compliance**: Each dependency justified — no stdlib alternative exists for audio extraction or speech-to-text. Both are required for the podcast feature and cannot be simplified further.

**Optional dependency approach**: The podcast feature's dependencies (`yt-dlp`, `faster-whisper`) should be **optional extras** to keep the base install lightweight. Users who don't need podcast summarization shouldn't need to install ~70MB+ of additional packages.

```
# requirements.txt — base (unchanged)
requests>=2.31,<3
feedparser>=6.0,<7
beautifulsoup4>=4.12,<5
lxml>=5.0,<6

# requirements-podcast.txt — optional
yt-dlp>=2024.1,<2026
faster-whisper>=1.0,<2
```

Or in `pyproject.toml`:
```toml
[project.optional-dependencies]
podcast = ["yt-dlp>=2024.1,<2026", "faster-whisper>=1.0,<2"]
```

### 8.5 Research: CLI Command Design for Podcast

**Decision**: `ai-digest podcast <url> [--model tiny|base|small|medium]`

**Rationale**: Follows same subcommand pattern as source management. Model selection flag allows users to trade speed for accuracy.

**Output format**: Same formatted output as digest entries — title (extracted from metadata or URL), source attribution, and summary text. Optionally save to cache for later reference.

---

## 9. Updated Technology Choices Summary

| Requirement | Technology | Type | Reason |
|-------------|-----------|------|--------|
| **HTTP with retry** | `requests` + `urllib3.Retry` | External | Built-in exponential backoff matches FR-009 |
| **Text similarity** | `difflib.SequenceMatcher` | Stdlib | Direct ratio for 75% threshold, zero deps |
| **RSS parsing** | `feedparser` | External | Industry standard, handles all feed variants |
| **HTML parsing** | `beautifulsoup4` + `lxml` | External | CSS selectors for targeted extraction |
| **Config loading** | `json` + `tomllib` | Stdlib | TOML built into Python 3.11+ |
| **Config writing** | `json` | Stdlib | JSON write for source management changes |
| **Summarization** | Frequency-based scoring | Stdlib | Simple, effective, no ML required |
| **Deduplication** | SequenceMatcher on title+content | Stdlib | Fast enough for daily volumes |
| **Audio extraction** | `yt-dlp` | External (optional) | Handles 1000+ podcast hosting sites |
| **Speech-to-text** | `faster-whisper` | External (optional) | 4x faster than openai-whisper, CPU-only, local |

---

## Document Status

✅ All "NEEDS CLARIFICATION" items resolved.
✅ All technology choices justified against constitution principles.
✅ Implementation patterns documented for all core components.
✅ Source management research complete (§7).
✅ Podcast summarization research complete (§8).
✅ Ready to proceed to Phase 1 (Design & Contracts).
