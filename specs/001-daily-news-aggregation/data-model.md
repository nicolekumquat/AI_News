# Data Model: Daily News Aggregation

**Feature**: Daily News Aggregation  
**Branch**: `001-daily-news-aggregation`  
**Date**: 2025-01-23 | **Updated**: 2026-03-04

This document defines all data entities, their attributes, relationships, validation rules, and state transitions for the feature.

> **2026-03-04 Update**: Added PodcastEpisode (§5) and PodcastSummary (§6) entities for podcast summarization feature. Source management uses existing NewsSource entity with no schema changes.

---

## Entities

### 1. NewsSource

Represents a configured source for fetching AI news.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | Yes | Unique identifier (e.g., "hackernews", "reddit-ml") |
| `name` | `str` | Yes | Display name (e.g., "HackerNews", "Reddit r/MachineLearning") |
| `fetch_method` | `enum` | Yes | One of: `"api"`, `"rss"`, `"html"` |
| `url` | `str` | Yes | Base URL or API endpoint |
| `enabled` | `bool` | Yes | Whether source is active for fetching |
| `last_fetch_at` | `datetime` (ISO 8601) | No | Timestamp of last successful fetch |
| `fetch_count` | `int` | Yes | Total successful fetches (for monitoring) |
| `error_count` | `int` | Yes | Total failed fetches (for monitoring) |

**Validation Rules**:
- `source_id` must be unique across all sources
- `source_id` must match regex `^[a-z0-9-]+$` (lowercase alphanumeric + hyphens)
- `url` must be a valid HTTP/HTTPS URL
- `fetch_method` must be one of: `"api"`, `"rss"`, `"html"`
- `fetch_count` and `error_count` must be ≥ 0

**Example**:
```json
{
  "source_id": "hackernews",
  "name": "HackerNews",
  "fetch_method": "api",
  "url": "https://hn.algolia.com/api/v1/search_by_date",
  "enabled": true,
  "last_fetch_at": "2025-01-23T10:30:00Z",
  "fetch_count": 42,
  "error_count": 2
}
```

---

### 2. NewsArticle

Represents a fetched article with original content.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `article_id` | `str` (UUID) | Yes | Unique identifier |
| `title` | `str` | Yes | Article title |
| `url` | `str` | Yes | Link to original article |
| `source_id` | `str` | Yes | Foreign key to NewsSource |
| `published_at` | `datetime` (ISO 8601) | Yes | Publication timestamp |
| `fetched_at` | `datetime` (ISO 8601) | Yes | When article was fetched |
| `content` | `str` | Yes | Full article text or excerpt |
| `author` | `str` | No | Article author (if available) |
| `metadata` | `dict` | No | Source-specific metadata (e.g., HN points, Reddit score) |

**Validation Rules**:
- `article_id` must be unique (UUID v4)
- `title` must not be empty (min length: 5 chars)
- `url` must be a valid HTTP/HTTPS URL
- `source_id` must reference an existing NewsSource
- `published_at` must be ≤ `fetched_at` (cannot be published in the future relative to fetch time)
- `content` must not be empty (min length: 50 chars for acceptance)
- Articles with missing `title` or `source_id` are **rejected** (FR-002 edge case handling)
- Articles with missing `published_at` default to `fetched_at` with warning logged

**Rejection Criteria** (edge case handling):
- Missing `title`: Reject
- Missing `source_id`: Reject
- Missing `url`: Reject
- `content` < 50 chars: Accept but flag for no summarization
- Missing `published_at`: Accept but default to `fetched_at` with warning

**Example**:
```json
{
  "article_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "GPT-5 Released with Multimodal Capabilities",
  "url": "https://openai.com/news/gpt-5-release",
  "source_id": "openai",
  "published_at": "2025-01-23T08:00:00Z",
  "fetched_at": "2025-01-23T10:00:00Z",
  "content": "OpenAI today announced GPT-5, the latest iteration...",
  "author": "Sam Altman",
  "metadata": {
    "category": "product-launch",
    "tags": ["GPT", "multimodal", "LLM"]
  }
}
```

---

### 3. DigestEntry

Represents a processed article ready for inclusion in a digest.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entry_id` | `str` (UUID) | Yes | Unique identifier |
| `article_id` | `str` (UUID) | Yes | Foreign key to NewsArticle |
| `summary` | `str` | Yes | Transformed/summarized content |
| `summary_method` | `enum` | Yes | One of: `"frequency"`, `"fallback"` |
| `compression_ratio` | `float` | Yes | `len(summary) / len(content)` |
| `is_duplicate` | `bool` | Yes | Whether identified as duplicate during processing |
| `duplicate_of` | `str` (UUID) | No | Reference to original entry if this is a duplicate |
| `processed_at` | `datetime` (ISO 8601) | Yes | When summarization occurred |

**Validation Rules**:
- `entry_id` must be unique (UUID v4)
- `article_id` must reference an existing NewsArticle
- `summary` must not be empty
- `summary` must not be identical to original `content` (FR-011 validation)
- `compression_ratio` must be in range (0.05, 0.55] for valid transformations
- `summary_method` must be one of: `"frequency"`, `"fallback"`
- If `is_duplicate` is `true`, `duplicate_of` must be set
- If `is_duplicate` is `false`, `duplicate_of` must be `null`

**State Transitions**:
1. **Initial**: Article fetched → `is_duplicate = false`, `duplicate_of = null`
2. **Duplicate Detected**: During deduplication → `is_duplicate = true`, `duplicate_of = <original_entry_id>`
3. **Summarized**: Frequency-based → `summary_method = "frequency"`
4. **Fallback**: Summarization failed or text too short → `summary_method = "fallback"`

**Example**:
```json
{
  "entry_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "article_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "summary": "OpenAI announced GPT-5 with multimodal capabilities. The model supports text, image, and audio input. Initial benchmarks show 40% improvement over GPT-4.",
  "summary_method": "frequency",
  "compression_ratio": 0.45,
  "is_duplicate": false,
  "duplicate_of": null,
  "processed_at": "2025-01-23T10:05:00Z"
}
```

---

### 4. Digest

Represents a daily collection of DigestEntry items for a specific date.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `digest_id` | `str` | Yes | Unique identifier (format: `YYYY-MM-DD`) |
| `date` | `date` | Yes | Digest date (e.g., "2025-01-23") |
| `entries` | `list[str]` | Yes | List of DigestEntry `entry_id` references |
| `total_articles_fetched` | `int` | Yes | Articles fetched before deduplication |
| `total_articles_after_dedup` | `int` | Yes | Articles after deduplication |
| `duplicates_removed` | `int` | Yes | Count of duplicates removed |
| `sources_fetched` | `list[str]` | Yes | List of NewsSource `source_id` that succeeded |
| `sources_failed` | `list[str]` | Yes | List of NewsSource `source_id` that failed |
| `created_at` | `datetime` (ISO 8601) | Yes | When digest was generated |
| `cache_status` | `enum` | Yes | One of: `"fresh"`, `"cached"`, `"stale"` |

**Validation Rules**:
- `digest_id` must match format `YYYY-MM-DD` and be a valid date
- `digest_id` must be unique (one digest per date)
- `entries` must reference existing DigestEntry objects
- `total_articles_after_dedup` = `len(entries)`
- `duplicates_removed` = `total_articles_fetched - total_articles_after_dedup`
- `sources_fetched` and `sources_failed` must be disjoint sets
- `sources_fetched` + `sources_failed` = all enabled NewsSource IDs
- `cache_status` must be one of: `"fresh"`, `"cached"`, `"stale"`

**State Transitions**:
1. **Fresh**: Just generated → `cache_status = "fresh"`
2. **Cached**: Loaded from cache, < 24 hours old → `cache_status = "cached"`
3. **Stale**: Loaded from cache, ≥ 24 hours old → `cache_status = "stale"`

**Example**:
```json
{
  "digest_id": "2025-01-23",
  "date": "2025-01-23",
  "entries": [
    "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "c3d4e5f6-a7b8-9012-cdef-123456789012"
  ],
  "total_articles_fetched": 87,
  "total_articles_after_dedup": 64,
  "duplicates_removed": 23,
  "sources_fetched": [
    "hackernews",
    "reddit-ml",
    "arxiv",
    "openai",
    "deepmind"
  ],
  "sources_failed": [
    "anthropic"
  ],
  "created_at": "2025-01-23T10:10:00Z",
  "cache_status": "fresh"
}
```

---

## Relationships

```
NewsSource (1) ──< (N) NewsArticle
    ↓
    source_id ← source_id

NewsArticle (1) ──< (1) DigestEntry
    ↓
    article_id ← article_id

DigestEntry (N) >── (1) Digest
    ↓
    entry_id → entries[]

DigestEntry (N) ──> (1) DigestEntry [duplicate_of]
    ↓
    entry_id → duplicate_of
```

---

## Persistence Strategy

**Storage**: Local filesystem (JSON files)

**Directory Structure**:
```
~/.ai-digest/cache/
├── sources.json                  # NewsSource configurations
├── articles/
│   ├── 2025-01-23.json          # NewsArticle objects by fetch date
│   ├── 2025-01-24.json
│   └── ...
├── digests/
│   ├── 2025-01-23.json          # Digest + DigestEntry objects
│   ├── 2025-01-24.json
│   └── ...
└── metadata.json                 # Cache metadata (last cleanup, stats)
```

**Retention Policy**:
- Articles: Keep for 30 days, then delete
- Digests: Keep for 30 days, then delete
- Sources: Persist indefinitely (configuration)

**Cache Invalidation**:
- Articles: Invalidate after 48 hours (freshness window)
- Digests: Invalidate after 24 hours for the current date
- Sources: Never invalidate (configuration only)

---

## Validation Summary

| Entity | Key Validation | Rejection Criteria |
|--------|----------------|-------------------|
| **NewsSource** | Unique `source_id`, valid URL | N/A (configuration) |
| **NewsArticle** | Title, URL, source_id required; content ≥ 50 chars | Missing title/source_id/url |
| **DigestEntry** | Summary not identical to content; compression 0.05-0.55 | Summary == content |
| **Digest** | Unique date, entries reference valid DigestEntry objects | N/A (always valid by construction) |
| **PodcastEpisode** | Valid URL, non-empty title | Missing URL |
| **PodcastSummary** | Non-empty transcript and summary, valid compression ratio | Empty transcript or summary |

---

## 5. PodcastEpisode (NEW)

Represents a podcast episode to be transcribed and summarized.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `episode_id` | `str` (UUID) | Yes | Unique identifier |
| `url` | `str` | Yes | URL of the podcast episode (page or direct audio) |
| `title` | `str` | Yes | Episode title (extracted from metadata or user-provided) |
| `audio_path` | `str` | No | Local path to downloaded audio (temporary) |
| `duration_seconds` | `int` | No | Audio duration in seconds (if available) |
| `source_name` | `str` | No | Podcast/show name (if available from metadata) |
| `downloaded_at` | `datetime` (ISO 8601) | No | When audio was downloaded |

**Validation Rules**:
- `episode_id` must be unique (UUID v4)
- `url` must be a valid HTTP/HTTPS URL
- `title` must not be empty (min length: 3 chars)
- `duration_seconds` must be ≥ 0 if set
- `audio_path` must point to an existing file when set

**Example**:
```json
{
  "episode_id": "d4e5f6a7-b8c9-0123-defg-456789012345",
  "url": "https://www.latent.space/p/gpt5-analysis",
  "title": "GPT-5 Deep Dive - Latent Space Podcast",
  "audio_path": "/tmp/ai-digest-podcast-abc123/GPT-5 Deep Dive.wav",
  "duration_seconds": 3420,
  "source_name": "Latent Space Podcast",
  "downloaded_at": "2026-03-04T14:00:00Z"
}
```

---

## 6. PodcastSummary (NEW)

Represents the result of transcribing and summarizing a podcast episode.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summary_id` | `str` (UUID) | Yes | Unique identifier |
| `episode_id` | `str` (UUID) | Yes | Foreign key to PodcastEpisode |
| `transcript` | `str` | Yes | Full transcript text |
| `transcript_word_count` | `int` | Yes | Word count of raw transcript |
| `summary` | `str` | Yes | Condensed summary of transcript |
| `summary_word_count` | `int` | Yes | Word count of summary |
| `compression_ratio` | `float` | Yes | `len(summary) / len(transcript)` |
| `model_size` | `str` | Yes | Whisper model used (e.g., "base") |
| `transcription_time_seconds` | `float` | Yes | Time taken to transcribe |
| `processed_at` | `datetime` (ISO 8601) | Yes | When processing completed |

**Validation Rules**:
- `summary_id` must be unique (UUID v4)
- `episode_id` must reference an existing PodcastEpisode
- `transcript` must not be empty (min length: 100 chars — indicates real audio content)
- `summary` must not be empty
- `summary` must not be identical to `transcript`
- `compression_ratio` must be in range (0.01, 0.5] for valid transformations (podcasts are long-form, expect more aggressive compression)
- `model_size` must be one of: `"tiny"`, `"base"`, `"small"`, `"medium"`
- `transcription_time_seconds` must be > 0

**State Transitions**:
1. **Downloading**: PodcastEpisode created, audio_path not yet set
2. **Downloaded**: audio_path set, ready for transcription
3. **Transcribing**: Audio being processed by Whisper model
4. **Transcribed**: transcript populated, ready for summarization
5. **Summarized**: summary populated, processing complete

**Example**:
```json
{
  "summary_id": "e5f6a7b8-c9d0-1234-efgh-567890123456",
  "episode_id": "d4e5f6a7-b8c9-0123-defg-456789012345",
  "transcript": "Welcome to the Latent Space podcast. Today we're diving deep into GPT-5...",
  "transcript_word_count": 8500,
  "summary": "The Latent Space podcast analyzes GPT-5's new capabilities including native multimodal reasoning, extended context windows up to 1M tokens, and improved tool use. Key takeaway: GPT-5 represents a shift from scaling parameters to scaling inference compute. The hosts discuss implications for AI engineering workflows and prediction that agent frameworks will need significant rearchitecting.",
  "summary_word_count": 450,
  "compression_ratio": 0.053,
  "model_size": "base",
  "transcription_time_seconds": 187.5,
  "processed_at": "2026-03-04T14:05:00Z"
}
```

---

## Updated Relationships

```
NewsSource (1) ──< (N) NewsArticle
    ↓
    source_id ← source_id

NewsArticle (1) ──< (1) DigestEntry
    ↓
    article_id ← article_id

DigestEntry (N) >── (1) Digest
    ↓
    entry_id → entries[]

DigestEntry (N) ──> (1) DigestEntry [duplicate_of]
    ↓
    entry_id → duplicate_of

PodcastEpisode (1) ──< (1) PodcastSummary
    ↓
    episode_id ← episode_id
```

---

## Updated Persistence Strategy

**Directory Structure**:
```
~/.ai-digest/cache/
├── sources.json                  # NewsSource configurations
├── articles/
│   ├── 2025-01-23.json          # NewsArticle objects by fetch date
│   └── ...
├── digests/
│   ├── 2025-01-23.json          # Digest + DigestEntry objects
│   └── ...
├── podcasts/
│   ├── <episode_id>.json        # PodcastEpisode + PodcastSummary
│   └── ...
└── metadata.json                 # Cache metadata (last cleanup, stats)
```

**Retention Policy** (updated):
- Articles: Keep for 30 days, then delete
- Digests: Keep for 30 days, then delete
- Sources: Persist indefinitely (configuration)
- Podcasts: Keep for 30 days, then delete

---

## Document Status

✅ All entities from spec extracted and defined.
✅ Validation rules documented per requirements (FR-002, FR-003, FR-011).
✅ State transitions for duplicate detection and summarization defined.
✅ Persistence strategy aligned with caching requirements (FR-006).
✅ PodcastEpisode and PodcastSummary entities defined for podcast feature.
✅ Source management uses existing NewsSource entity — no schema changes needed.
✅ Ready to proceed to contracts definition.
