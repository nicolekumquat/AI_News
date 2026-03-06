# CLI Interface Contract

**Feature**: Daily News Aggregation  
**Branch**: `001-daily-news-aggregation`  
**Date**: 2025-01-23 | **Updated**: 2026-03-04

This document defines the command-line interface contract for the AI Daily Digest CLI tool.

> **2026-03-04 Update**: Added `sources` subcommand (§Source Management Commands) and `podcast` subcommand (§Podcast Summarization Command).

---

## Command Specification

### Primary Command

```bash
ai-digest [OPTIONS]
```

**Description**: Fetch, process, and display a daily digest of AI news articles.

---

## Options

### `--date <YYYY-MM-DD>`

**Description**: Specify the date for the digest to retrieve or generate.

**Format**: ISO 8601 date format (`YYYY-MM-DD`)

**Default**: Today's date

**Examples**:
```bash
ai-digest                          # Today's digest
ai-digest --date 2025-01-23       # Specific date
ai-digest --date 2025-01-20       # Historical digest (from cache if available)
```

**Validation**:
- Must be a valid date in `YYYY-MM-DD` format
- Dates in the future return an error
- Dates older than 30 days return a cache miss warning (if not cached)

**Error Cases**:
```bash
# Invalid format
ai-digest --date 01-23-2025
# Error: Invalid date format. Expected YYYY-MM-DD, got 01-23-2025

# Future date
ai-digest --date 2026-12-31
# Error: Cannot generate digest for future date: 2026-12-31

# Invalid date
ai-digest --date 2025-02-30
# Error: Invalid date: 2025-02-30 (February has only 28/29 days)
```

---

## Configuration File

**Location**: `~/.ai-digest/config.toml` (default) or `~/.ai-digest/config.json`

**Format**: TOML or JSON

**Detection**: Tool checks for `config.toml` first, falls back to `config.json`, uses defaults if neither exists.

**Example Configuration (`config.toml`)**:

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
min_sentence_length = 5

[sources]
enabled = ["hackernews", "reddit-ml", "arxiv", "openai", "deepmind", "anthropic", "meta-ai"]

[[sources.custom]]
source_id = "custom-blog"
name = "Custom AI Blog"
fetch_method = "rss"
url = "https://example.com/feed.xml"
enabled = true
```

**Example Configuration (`config.json`)**:

```json
{
  "cache": {
    "directory": "~/.ai-digest/cache",
    "retention_days": 30
  },
  "fetcher": {
    "timeout_seconds": 30,
    "max_retries": 3,
    "retry_delays": [1, 2, 4]
  },
  "summarizer": {
    "compression_ratio": 0.5,
    "min_sentence_length": 5
  },
  "sources": {
    "enabled": [
      "hackernews",
      "reddit-ml",
      "arxiv",
      "openai",
      "deepmind",
      "anthropic",
      "meta-ai"
    ],
    "custom": [
      {
        "source_id": "custom-blog",
        "name": "Custom AI Blog",
        "fetch_method": "rss",
        "url": "https://example.com/feed.xml",
        "enabled": true
      }
    ]
  }
}
```

**Configuration Options**:

| Section | Field | Type | Default | Description |
|---------|-------|------|---------|-------------|
| `cache.directory` | `str` | `~/.ai-digest/cache` | Cache storage location |
| `cache.retention_days` | `int` | `30` | Days to keep cached data |
| `fetcher.timeout_seconds` | `int` | `30` | HTTP request timeout |
| `fetcher.max_retries` | `int` | `3` | Retry attempts per source |
| `fetcher.retry_delays` | `list[int]` | `[1, 2, 4]` | Backoff delays (seconds) |
| `summarizer.compression_ratio` | `float` | `0.5` | Target summary length (0.0-1.0) |
| `summarizer.min_sentence_length` | `int` | `5` | Min words per sentence to keep |
| `sources.enabled` | `list[str]` | All built-in sources | Active source IDs |
| `sources.custom` | `list[object]` | `[]` | User-defined sources |

---

## Output Format

### Successful Digest Display

**Format**: Human-readable text output to stdout

**Structure**:
```
AI Daily Digest - [Date]
Generated: [Timestamp] | Articles: [Count] | Sources: [Count]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[#] [Title]
Source: [Source Name] | Published: [Date/Time]
URL: [Article URL]

[Summary text spanning multiple lines if needed. The summary is a condensed
version of the original article focusing on key points.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Repeat for each article]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

End of Digest
Articles: [N] | Duplicates Removed: [M] | Sources Failed: [K]
```

**Example**:
```
AI Daily Digest - 2025-01-23
Generated: 2025-01-23 10:10:00 UTC | Articles: 64 | Sources: 6/7

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GPT-5 Released with Multimodal Capabilities
Source: OpenAI | Published: 2025-01-23 08:00:00 UTC
URL: https://openai.com/news/gpt-5-release

OpenAI announced GPT-5 with support for text, image, and audio input. Initial
benchmarks show 40% improvement over GPT-4 on reasoning tasks. The model will
be available via API starting February 1st.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. New Transformer Architecture Achieves State-of-the-Art on GLUE
Source: ArXiv | Published: 2025-01-23 06:30:00 UTC
URL: https://arxiv.org/abs/2501.12345

Researchers propose a novel attention mechanism reducing computational complexity
from O(n²) to O(n log n). The architecture achieves new SOTA on GLUE benchmark
while training 3x faster than standard transformers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... more articles ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

End of Digest
Articles: 64 | Duplicates Removed: 23 | Sources Failed: 1 (anthropic)
```

---

### Cached Digest Notice

When a cached digest is returned:
```
AI Daily Digest - 2025-01-23 [CACHED]
Loaded from cache: 2025-01-23 10:10:00 UTC | Articles: 64 | Sources: 6/7

[... digest content ...]
```

---

### Empty Digest

When no articles are available:
```
AI Daily Digest - 2025-01-23
Generated: 2025-01-23 10:10:00 UTC | Articles: 0 | Sources: 6/7

No new AI news articles found within the last 48 hours.

Last successful fetch: 2025-01-22 10:00:00 UTC

Sources failed: anthropic
```

---

### Error Messages

**All sources failed**:
```
Error: Unable to generate digest for 2025-01-23

All configured news sources failed to fetch:
- hackernews: Connection timeout after 3 retries
- reddit-ml: Rate limit exceeded (HTTP 429)
- arxiv: Service unavailable (HTTP 503)
- openai: Connection timeout after 3 retries
- deepmind: Connection timeout after 3 retries
- anthropic: Connection timeout after 3 retries
- meta-ai: Connection timeout after 3 retries

Last successful digest: 2025-01-22 (run 'ai-digest --date 2025-01-22' to view)
```

**Invalid date**:
```
Error: Invalid date format. Expected YYYY-MM-DD, got 01-23-2025
Usage: ai-digest [--date YYYY-MM-DD]
```

**Future date**:
```
Error: Cannot generate digest for future date: 2026-12-31
```

**Configuration error**:
```
Error: Invalid configuration file: ~/.ai-digest/config.toml

Line 12: Invalid value for 'fetcher.max_retries': must be between 1 and 10, got 0
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success (digest displayed) |
| `1` | General error (invalid arguments, config error) |
| `2` | All sources failed (unable to generate digest) |
| `3` | Cache miss for historical date and sources unavailable |

---

## Usage Examples

### Basic Usage

```bash
# Display today's digest
ai-digest

# Display digest for specific date
ai-digest --date 2025-01-20
```

### Common Workflows

```bash
# Check yesterday's digest
ai-digest --date $(date -d "yesterday" +%Y-%m-%d)

# View digest from 3 days ago
ai-digest --date 2025-01-20

# Force refresh by deleting cache first (manual workaround)
rm ~/.ai-digest/cache/digests/2025-01-23.json
ai-digest --date 2025-01-23
```

---

## Contract Tests

All contract behaviors must be verified with integration tests:

1. **Test: Default date (today)**
   - Run `ai-digest` without arguments
   - Verify digest for today's date is displayed

2. **Test: Specific date**
   - Run `ai-digest --date 2025-01-23`
   - Verify digest for 2025-01-23 is displayed

3. **Test: Cached digest**
   - Generate digest, then run command again
   - Verify `[CACHED]` indicator in output

4. **Test: Empty digest**
   - Mock all sources to return no articles
   - Verify "No new AI news articles" message

5. **Test: All sources failed**
   - Mock all sources to fail
   - Verify error message lists all failed sources
   - Verify exit code 2

6. **Test: Invalid date format**
   - Run `ai-digest --date 01-23-2025`
   - Verify error message with correct format guidance
   - Verify exit code 1

7. **Test: Future date**
   - Run `ai-digest --date 2026-12-31`
   - Verify future date error message
   - Verify exit code 1

8. **Test: Configuration loading**
   - Create custom `config.toml` with modified settings
   - Verify settings are applied (e.g., different cache directory)

---

## Source Management Commands (NEW)

### `ai-digest sources list`

**Description**: Display all configured news sources with their type and enabled/disabled status.

**Output Format**:
```
News Sources (22 total, 20 enabled)

  Built-in Sources:
    ✓ hackernews          HackerNews                          api   https://hn.algolia.com/api/v1/search_by_date
    ✓ reddit-chatgpt      Reddit r/ChatGPT                    api   https://www.reddit.com/r/ChatGPT/top.json
    ✓ reddit-localllama   Reddit r/LocalLLaMA                 api   https://www.reddit.com/r/LocalLLaMA/top.json
    ✗ reddit-artificial    Reddit r/artificial                 api   https://www.reddit.com/r/artificial/top.json
    ✓ arxiv               ArXiv AI/ML                         api   http://export.arxiv.org/api/query
    ✓ openai              OpenAI News                         rss   https://openai.com/news/rss.xml
    ...

  Custom Sources:
    ✓ my-ai-blog          My AI Blog                          rss   https://myblog.com/feed.xml

Legend: ✓ enabled  ✗ disabled
```

**Exit Code**: `0`

---

### `ai-digest sources add --name <NAME> --url <URL> [--method rss|api|html]`

**Description**: Add a new custom news source.

**Arguments**:
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--name` | Yes | — | Display name for the source |
| `--url` | Yes | — | Feed/API URL |
| `--method` | No | `rss` | Fetch method: `rss`, `api`, or `html` |

**Source ID Generation**: Auto-generated from name (lowercase, spaces → hyphens, strip non-alphanumeric). Example: "My AI Blog" → `my-ai-blog`.

**Output**:
```
Added source: my-ai-blog (My AI Blog)
URL: https://myblog.com/feed.xml
Method: rss
Status: enabled

Source saved to configuration.
```

**Error Cases**:
```
# Duplicate source ID
Error: Source ID 'hackernews' already exists.
Use a different name or remove the existing source first.

# Invalid URL
Error: Invalid URL: not-a-url
URL must start with http:// or https://

# Invalid method
Error: Invalid fetch method: xml
Valid methods: rss, api, html
```

**Exit Codes**: `0` (success), `1` (validation error)

---

### `ai-digest sources remove <source_id>`

**Description**: Remove a custom source. Built-in sources cannot be removed (use `disable` instead).

**Output**:
```
Removed source: my-ai-blog (My AI Blog)
Source removed from configuration.
```

**Error Cases**:
```
# Built-in source
Error: Cannot remove built-in source 'hackernews'.
Use 'ai-digest sources disable hackernews' to disable it instead.

# Non-existent source
Error: Source 'nonexistent' not found.
Run 'ai-digest sources list' to see available sources.
```

**Exit Codes**: `0` (success), `1` (error)

---

### `ai-digest sources enable <source_id>`

**Description**: Enable a previously disabled source.

**Output**:
```
Enabled source: reddit-artificial (Reddit r/artificial)
```

**Error Cases**:
```
# Already enabled
Source 'hackernews' is already enabled.

# Non-existent
Error: Source 'nonexistent' not found.
```

**Exit Codes**: `0` (success, including already-enabled), `1` (not found)

---

### `ai-digest sources disable <source_id>`

**Description**: Disable a source so it is skipped during digest generation.

**Output**:
```
Disabled source: reddit-artificial (Reddit r/artificial)
```

**Error Cases**:
```
# Already disabled
Source 'reddit-artificial' is already disabled.

# Last enabled source
Error: Cannot disable 'hackernews' — at least one source must remain enabled.

# Non-existent
Error: Source 'nonexistent' not found.
```

**Exit Codes**: `0` (success, including already-disabled), `1` (error)

---

## Podcast Summarization Command (NEW)

### `ai-digest podcast <URL> [--model tiny|base|small|medium]`

**Description**: Download a podcast episode from the given URL, transcribe the audio locally using Whisper, and generate a concise summary.

**Arguments**:
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `URL` | Yes | — | Podcast episode URL (page, audio link, or YouTube) |
| `--model` | No | `base` | Whisper model size for transcription |

**Prerequisites**: `yt-dlp` must be installed and available on PATH. `faster-whisper` must be installed (`pip install ai-daily-digest[podcast]`).

**Output Format**:
```
Podcast Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Title: GPT-5 Deep Dive
Source: Latent Space Podcast
URL: https://www.latent.space/p/gpt5-analysis
Duration: 57:00 | Transcript: 8,500 words | Model: base

Summary:
The Latent Space podcast analyzes GPT-5's new capabilities including native
multimodal reasoning, extended context windows up to 1M tokens, and improved
tool use. Key takeaway: GPT-5 represents a shift from scaling parameters to
scaling inference compute. The hosts discuss implications for AI engineering
workflows and predict that agent frameworks will need significant rearchitecting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Compression: 94.7% | Processing time: 3m 12s
```

**Progress Output** (stderr, during processing):
```
Downloading audio... done (57:00, 48.2 MB)
Transcribing with whisper-base... done (187s)
Generating summary... done
```

**Error Cases**:
```
# Missing yt-dlp
Error: 'yt-dlp' is not installed or not found on PATH.
Install it with: pip install yt-dlp
Or install podcast extras: pip install ai-daily-digest[podcast]

# Missing faster-whisper
Error: 'faster-whisper' is not installed.
Install podcast extras: pip install ai-daily-digest[podcast]

# Invalid URL / download failure
Error: Failed to download audio from URL: https://example.com/404
yt-dlp error: Unable to extract video data

# Audio too short (< 30 seconds)
Error: Audio is too short (12s). Minimum duration for summarization is 30 seconds.

# Invalid model size
Error: Invalid model size 'huge'. Valid options: tiny, base, small, medium
```

**Exit Codes**: `0` (success), `1` (argument/config error), `4` (download failure), `5` (transcription failure)

---

## Updated Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error (invalid arguments, config error, source management error) |
| `2` | All sources failed (unable to generate digest) |
| `3` | Cache miss for historical date and sources unavailable |
| `4` | Podcast download failure |
| `5` | Podcast transcription failure |

---

## Contract Tests (Source Management)

9. **Test: sources list**
   - Add custom source, disable one built-in
   - Run `ai-digest sources list`
   - Verify output shows all sources with correct status indicators

10. **Test: sources add**
    - Run `ai-digest sources add --name "Test Blog" --url https://test.com/feed.xml`
    - Verify source added with auto-generated ID `test-blog`
    - Verify source appears in `sources list` output
    - Verify config file updated

11. **Test: sources add duplicate**
    - Add source, then try adding with same name
    - Verify duplicate error message
    - Verify exit code 1

12. **Test: sources remove custom**
    - Add custom source, then remove it
    - Verify success message
    - Verify source no longer in `sources list`

13. **Test: sources remove built-in (rejected)**
    - Run `ai-digest sources remove hackernews`
    - Verify error message suggesting `disable` instead
    - Verify exit code 1

14. **Test: sources enable/disable**
    - Disable a source, verify disabled in list
    - Enable it again, verify enabled in list

15. **Test: sources disable last source (rejected)**
    - Disable all sources except one
    - Try to disable the last one
    - Verify error about minimum sources

## Contract Tests (Podcast)

16. **Test: podcast basic**
    - Mock yt-dlp and faster-whisper
    - Run `ai-digest podcast https://example.com/episode`
    - Verify summary output format

17. **Test: podcast with model flag**
    - Run `ai-digest podcast https://example.com/episode --model small`
    - Verify `small` model passed to transcription

18. **Test: podcast missing dependency**
    - Mock yt-dlp as unavailable
    - Run `ai-digest podcast https://example.com/episode`
    - Verify dependency error message

19. **Test: podcast download failure**
    - Mock yt-dlp to fail
    - Verify error message and exit code 4

---

## Document Status

✅ CLI command and options defined per FR-008, FR-008a, FR-008b.
✅ Configuration file schema documented (JSON/TOML support).
✅ Output format specified with examples.
✅ Error handling and exit codes defined.
✅ Contract tests outlined for validation.
✅ Source management subcommands defined (list, add, remove, enable, disable).
✅ Podcast summarization subcommand defined with progress output.
✅ Updated exit codes for new features.
✅ Ready for implementation.
