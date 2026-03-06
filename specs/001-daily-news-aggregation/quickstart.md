# Quick Start Guide: Daily News Aggregation

**Feature**: Daily News Aggregation  
**Branch**: `001-daily-news-aggregation`  
**Date**: 2025-01-23 | **Updated**: 2026-03-04

This guide provides a quick start for developers implementing or working with the Daily News Aggregation feature.

> **2026-03-04 Update**: Added Source Management (§Managing Sources) and Podcast Summarization (§Podcast Summarization) sections.

---

## Overview

The Daily News Aggregation feature fetches AI news from multiple sources, deduplicates content, generates summaries, and presents a daily digest via a CLI command.

**Key Components**:
- **Fetcher**: Retrieves articles from HackerNews, Reddit, ArXiv, and AI thought leader blogs
- **Deduplicator**: Identifies and removes duplicate articles using 75% similarity threshold
- **Summarizer**: Generates extractive summaries (50% compression target)
- **Cache**: Stores processed digests locally for fast retrieval
- **CLI**: Provides `ai-digest [--date YYYY-MM-DD]` command

---

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Internet connection (for fetching news sources)

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai-daily-digest
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages**:
```
requests>=2.31,<3
feedparser>=6.0,<7
beautifulsoup4>=4.12,<5
lxml>=5.0,<6
pytest>=7.4,<8
ruff>=0.1,<1
```

### 4. Install CLI Tool (Development Mode)

```bash
pip install -e .
```

This makes the `ai-digest` command available in your virtual environment.

---

## Basic Usage

### View Today's Digest

```bash
ai-digest
```

**Output**:
```
AI Daily Digest - 2025-01-23
Generated: 2025-01-23 10:10:00 UTC | Articles: 64 | Sources: 6/7

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GPT-5 Released with Multimodal Capabilities
Source: OpenAI | Published: 2025-01-23 08:00:00 UTC
URL: https://openai.com/news/gpt-5-release

[Summary...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... more articles ...]
```

### View Digest for Specific Date

```bash
ai-digest --date 2025-01-20
```

### View Yesterday's Digest

```bash
# Linux/macOS
ai-digest --date $(date -d "yesterday" +%Y-%m-%d)

# Windows PowerShell
ai-digest --date (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
```

---

## Configuration

### Default Configuration

On first run, the tool creates a default configuration at `~/.ai-digest/config.toml`:

```toml
[cache]
directory = "~/.ai-digest/cache"
retention_days = 30

[fetcher]
timeout_seconds = 30
max_retries = 3
retry_delays = [1, 2, 4]

[summarizer]
compression_ratio = 0.5

[deduplicator]
similarity_threshold = 0.75

[sources]
enabled = [
  "hackernews",
  "reddit-ml",
  "arxiv",
  "openai",
  "deepmind",
  "anthropic",
  "meta-ai",
  "sam-schillace",
  "ethan-mollick",
  "andrew-ng"
]
```

### Customizing Sources

To disable a source, remove it from the `enabled` list:

```toml
[sources]
enabled = ["hackernews", "arxiv", "openai"]  # Only 3 sources
```

To add a custom RSS feed:

```toml
[[sources.custom]]
source_id = "my-blog"
name = "My AI Blog"
fetch_method = "rss"
url = "https://myblog.com/feed.xml"
enabled = true
```

---

## Development Workflow

### Project Structure

```
src/
├── models/              # NewsArticle, NewsSource, DigestEntry, Digest
├── services/
│   ├── fetcher.py      # Source fetching with retry logic
│   ├── deduplicator.py # Title+content similarity (75% threshold)
│   ├── summarizer.py   # Extractive text summarization
│   └── cache.py        # Local filesystem caching
├── cli/
│   ├── __main__.py     # Entry point for ai-digest command
│   └── commands.py     # CLI argument parsing
└── config/
    └── loader.py       # JSON/TOML config file loading

tests/
├── contract/           # CLI interface contract tests
├── integration/        # End-to-end digest generation tests
└── unit/              # Component-level tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_summarizer.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run contract tests only
pytest tests/contract/
```

### Linting and Formatting

```bash
# Check code style
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

---

## Common Tasks

### Task 1: Add a New News Source

**Steps**:

1. **Define source configuration** in `src/config/sources.py`:
   ```python
   BUILTIN_SOURCES = {
       # ... existing sources ...
       "new-source": {
           "name": "New Source",
           "fetch_method": "rss",
           "url": "https://example.com/feed.xml"
       }
   }
   ```

2. **Update default enabled sources** in `config.toml`:
   ```toml
   [sources]
   enabled = [..., "new-source"]
   ```

3. **Write tests**:
   ```python
   def test_fetch_new_source(mocker):
       # Mock RSS feed response
       # Verify articles fetched correctly
   ```

4. **Update documentation**: Add source to README and this quickstart.

---

### Task 2: Modify Summarization Algorithm

**Steps**:

1. **Edit `src/services/summarizer.py`**:
   ```python
   def frequency_summarize(text, ratio=0.5):
       # Modify algorithm here
       pass
   ```

2. **Write failing test** (TDD approach):
   ```python
   def test_summarize_with_new_algorithm():
       text = "..."
       summary = frequency_summarize(text)
       assert len(summary) <= len(text) * 0.5
       assert "key phrase" in summary
   ```

3. **Implement changes** to make test pass.

4. **Run regression tests**:
   ```bash
   pytest tests/unit/test_summarizer.py
   ```

---

### Task 3: Debug Deduplication Issues

**Steps**:

1. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Run digest generation with verbose output**:
   ```bash
   ai-digest --date 2025-01-23 --verbose
   ```

3. **Check similarity scores** in logs:
   ```
   DEBUG: Comparing "Article A" vs "Article B": similarity=0.82 (duplicate)
   ```

4. **Adjust threshold** in config if needed:
   ```toml
   [deduplicator]
   similarity_threshold = 0.80  # Stricter threshold
   ```

---

## Architecture Patterns

### Fetcher Pattern (Retry with Exponential Backoff)

```python
def fetch_with_retry(fetch_fn, source_name, max_retries=3):
    delays = [1, 2, 4]
    for attempt in range(max_retries):
        try:
            return fetch_fn()
        except Exception as e:
            logging.warning(f"{source_name} attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delays[attempt])
    logging.error(f"{source_name}: all retries exhausted")
    return []
```

**Usage**:
```python
articles = fetch_with_retry(
    lambda: fetch_hackernews_api(),
    "hackernews"
)
```

---

### Deduplication Pattern (Pairwise Comparison)

```python
from difflib import SequenceMatcher

def deduplicate_articles(articles, threshold=0.75):
    accepted = []
    for article in sorted(articles, key=lambda a: a.published_at, reverse=True):
        is_duplicate = False
        for existing in accepted:
            text_a = article.title + " " + article.content
            text_b = existing.title + " " + existing.content
            similarity = SequenceMatcher(None, text_a, text_b).ratio()
            if similarity >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            accepted.append(article)
    return accepted
```

---

### Summarization Pattern (Frequency-Based)

```python
def frequency_summarize(text, ratio=0.5):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 2:
        return text
    
    # Word frequency
    words = re.findall(r'\b[a-z]+\b', text.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    freq = Counter(words)
    
    # Score sentences
    scored = []
    for i, sent in enumerate(sentences):
        sent_words = re.findall(r'\b[a-z]+\b', sent.lower())
        score = sum(freq.get(w, 0) for w in sent_words)
        score = score / max(len(sent_words), 1)
        
        # Position boost
        if i == 0:
            score *= 1.5
        elif i == len(sentences) - 1:
            score *= 1.2
        
        scored.append((score, i, sent))
    
    # Top N sentences
    n = max(1, int(len(sentences) * ratio))
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:n]
    top.sort(key=lambda x: x[1])
    return ' '.join(s[2] for s in top)
```

---

## Troubleshooting

### Issue: "All sources failed"

**Symptoms**: Error message saying all configured sources failed to fetch.

**Possible Causes**:
1. No internet connection
2. Rate limiting (especially Reddit without User-Agent)
3. Source API changes or downtime

**Solutions**:
1. Check internet connection: `ping google.com`
2. Verify User-Agent in config (required for Reddit)
3. Check source status pages
4. Try fetching individual source manually:
   ```python
   from src.services.fetcher import fetch_hackernews
   articles = fetch_hackernews()
   print(len(articles))
   ```

---

### Issue: "Too many duplicates"

**Symptoms**: Digest has duplicate articles despite deduplication.

**Possible Causes**:
1. Similarity threshold too low
2. Title-only matching (content not compared)
3. Different article versions with slight variations

**Solutions**:
1. Increase similarity threshold:
   ```toml
   [deduplicator]
   similarity_threshold = 0.85  # Stricter
   ```
2. Verify both title and content are compared:
   ```toml
   [deduplicator]
   compare_title = true
   compare_content = true
   ```

---

### Issue: "Summaries are too short/long"

**Symptoms**: Generated summaries don't meet 50% compression target.

**Possible Causes**:
1. Wrong compression ratio configured
2. Short articles (fallback mode)

**Solutions**:
1. Adjust compression ratio:
   ```toml
   [summarizer]
   compression_ratio = 0.4  # Target 40% instead of 50%
   ```
2. Check logs for fallback mode usage:
   ```
   INFO: Article "..." too short, using fallback summary
   ```

---

## Managing Sources

### List All Sources

```bash
ai-digest sources list
```

Shows all built-in and custom sources with their enabled/disabled status, fetch method, and URL.

### Add a Custom Source

```bash
# Add an RSS feed
ai-digest sources add --name "My Favorite AI Blog" --url https://myblog.com/feed.xml

# Add an API source
ai-digest sources add --name "Custom API" --url https://api.example.com/articles --method api

# Add an HTML-scraped source
ai-digest sources add --name "AI Newsletter" --url https://newsletter.example.com --method html
```

### Remove a Custom Source

```bash
ai-digest sources remove my-favorite-ai-blog
```

Note: Built-in sources cannot be removed, only disabled.

### Enable/Disable Sources

```bash
# Disable a source you don't want
ai-digest sources disable arxiv

# Re-enable it later
ai-digest sources enable arxiv
```

---

## Podcast Summarization

### Prerequisites (Optional)

Install podcast extras for audio transcription:

```bash
pip install ai-daily-digest[podcast]
```

This installs `yt-dlp` (audio download) and `faster-whisper` (local transcription).

### Summarize a Podcast

```bash
# Basic usage (uses 'base' whisper model)
ai-digest podcast https://www.latent.space/p/gpt5-analysis

# Use a faster but less accurate model
ai-digest podcast https://www.youtube.com/watch?v=abc123 --model tiny

# Use a more accurate model (slower)
ai-digest podcast https://example.com/episode.mp3 --model small
```

### How It Works

1. **Download**: `yt-dlp` extracts audio from the episode URL
2. **Transcribe**: `faster-whisper` converts speech to text locally (no cloud APIs)
3. **Summarize**: The existing frequency-based summarizer generates a concise summary

### Model Selection Guide

| Model | Speed | Accuracy | RAM | Best For |
|-------|-------|----------|-----|----------|
| `tiny` | ~32x real-time | Basic | ~400MB | Quick checks, short clips |
| `base` | ~16x real-time | Good | ~1GB | **Default — most podcasts** |
| `small` | ~6x real-time | Better | ~2GB | Important episodes, noisy audio |
| `medium` | ~2x real-time | Great | ~5GB | Maximum accuracy, clear speech |

### Configure Default Model

```toml
# In ~/.ai-digest/config.toml
[podcast]
default_model = "small"        # Use 'small' model by default
cleanup_audio = true           # Delete audio after processing
max_duration_seconds = 7200    # Max 2 hours (default)
```

---

## Next Steps

- **Read the full specification**: `specs/001-daily-news-aggregation/spec.md`
- **Review data models**: `specs/001-daily-news-aggregation/data-model.md`
- **Check contracts**: `specs/001-daily-news-aggregation/contracts/`
- **Implement tasks**: `specs/001-daily-news-aggregation/tasks.md` (generated by `/speckit.tasks`)

---

## Document Status

✅ Quick start guide created with installation, usage, and development workflows.
✅ Common tasks and architecture patterns documented.
✅ Troubleshooting section provided.
✅ Source management CLI usage documented.
✅ Podcast summarization usage and model guide documented.
✅ Ready for Phase 1 completion and agent context update.
