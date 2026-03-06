# Configuration Schema Contract

**Feature**: Daily News Aggregation  
**Branch**: `001-daily-news-aggregation`  
**Date**: 2025-01-23 | **Updated**: 2026-03-04

This document defines the configuration file schema for the AI Daily Digest CLI tool.

> **2026-03-04 Update**: Added `[podcast]` section for Whisper model defaults. Added config write behavior for source management. Added programmatic config save contract.

---

## File Location

**Default Path**: `~/.ai-digest/config.toml`

**Fallback Path**: `~/.ai-digest/config.json`

**Detection Order**:
1. Check for `config.toml`
2. If not found, check for `config.json`
3. If neither found, use built-in defaults

---

## Schema (TOML Format)

### Complete Example

```toml
[cache]
directory = "~/.ai-digest/cache"
retention_days = 30

[fetcher]
timeout_seconds = 30
max_retries = 3
retry_delays = [1, 2, 4]
user_agent = "ai-daily-digest/1.0 (local CLI tool)"

[summarizer]
compression_ratio = 0.5
min_sentence_length = 5
stopwords_enabled = true

[deduplicator]
similarity_threshold = 0.75
compare_title = true
compare_content = true

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

[[sources.custom]]
source_id = "custom-blog"
name = "Custom AI Blog"
fetch_method = "rss"
url = "https://example.com/feed.xml"
enabled = true

[[sources.custom]]
source_id = "another-source"
name = "Another Source"
fetch_method = "api"
url = "https://api.example.com/articles"
enabled = false
```

---

## Schema (JSON Format)

### Complete Example

```json
{
  "cache": {
    "directory": "~/.ai-digest/cache",
    "retention_days": 30
  },
  "fetcher": {
    "timeout_seconds": 30,
    "max_retries": 3,
    "retry_delays": [1, 2, 4],
    "user_agent": "ai-daily-digest/1.0 (local CLI tool)"
  },
  "summarizer": {
    "compression_ratio": 0.5,
    "min_sentence_length": 5,
    "stopwords_enabled": true
  },
  "deduplicator": {
    "similarity_threshold": 0.75,
    "compare_title": true,
    "compare_content": true
  },
  "sources": {
    "enabled": [
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
    ],
    "custom": [
      {
        "source_id": "custom-blog",
        "name": "Custom AI Blog",
        "fetch_method": "rss",
        "url": "https://example.com/feed.xml",
        "enabled": true
      },
      {
        "source_id": "another-source",
        "name": "Another Source",
        "fetch_method": "api",
        "url": "https://api.example.com/articles",
        "enabled": false
      }
    ]
  }
}
```

---

## Field Specifications

### `[cache]` Section

| Field | Type | Default | Valid Range | Description |
|-------|------|---------|-------------|-------------|
| `directory` | `str` | `~/.ai-digest/cache` | Valid file path | Cache storage location |
| `retention_days` | `int` | `30` | `1-365` | Days to retain cached data |

**Validation**:
- `directory` must be an existing directory or creatable path
- `retention_days` must be positive integer ≤ 365

**Example**:
```toml
[cache]
directory = "/custom/path/cache"
retention_days = 60
```

---

### `[fetcher]` Section

| Field | Type | Default | Valid Range | Description |
|-------|------|---------|-------------|-------------|
| `timeout_seconds` | `int` | `30` | `5-300` | HTTP request timeout |
| `max_retries` | `int` | `3` | `1-10` | Retry attempts per source |
| `retry_delays` | `list[int]` | `[1, 2, 4]` | Positive integers | Backoff delays (seconds) |
| `user_agent` | `str` | `ai-daily-digest/1.0` | Non-empty string | HTTP User-Agent header |

**Validation**:
- `timeout_seconds` must be in range [5, 300]
- `max_retries` must be in range [1, 10]
- `retry_delays` must be a list of positive integers
- `len(retry_delays)` must equal `max_retries`
- `user_agent` must not be empty

**Example**:
```toml
[fetcher]
timeout_seconds = 60
max_retries = 5
retry_delays = [1, 2, 4, 8, 16]
user_agent = "MyCustomDigest/2.0"
```

---

### `[summarizer]` Section

| Field | Type | Default | Valid Range | Description |
|-------|------|---------|-------------|-------------|
| `compression_ratio` | `float` | `0.5` | `0.1-0.9` | Target summary length (0.0-1.0) |
| `min_sentence_length` | `int` | `5` | `1-50` | Min words per sentence to keep |
| `stopwords_enabled` | `bool` | `true` | `true`/`false` | Use stopword filtering |

**Validation**:
- `compression_ratio` must be in range [0.1, 0.9]
- `min_sentence_length` must be positive integer ≤ 50
- `stopwords_enabled` must be boolean

**Example**:
```toml
[summarizer]
compression_ratio = 0.4
min_sentence_length = 10
stopwords_enabled = true
```

---

### `[deduplicator]` Section

| Field | Type | Default | Valid Range | Description |
|-------|------|---------|-------------|-------------|
| `similarity_threshold` | `float` | `0.75` | `0.5-0.99` | Similarity threshold (0.0-1.0) |
| `compare_title` | `bool` | `true` | `true`/`false` | Include title in similarity |
| `compare_content` | `bool` | `true` | `true`/`false` | Include content in similarity |

**Validation**:
- `similarity_threshold` must be in range [0.5, 0.99]
- At least one of `compare_title` or `compare_content` must be `true`

**Example**:
```toml
[deduplicator]
similarity_threshold = 0.80
compare_title = true
compare_content = true
```

---

### `[sources]` Section

#### `enabled` Field

| Field | Type | Default | Valid Range | Description |
|-------|------|---------|-------------|-------------|
| `enabled` | `list[str]` | All built-in sources | Valid source IDs | Active source IDs |

**Built-in Source IDs**:
- `hackernews`
- `reddit-ml`
- `arxiv`
- `openai`
- `deepmind`
- `anthropic`
- `meta-ai`
- `sam-schillace`
- `ethan-mollick`
- `andrew-ng`

**Validation**:
- All IDs in `enabled` must be valid (built-in or custom source IDs)
- List cannot be empty (at least one source required)

**Example**:
```toml
[sources]
enabled = ["hackernews", "arxiv", "openai"]
```

---

#### `custom` Field (Array of Custom Sources)

| Field | Type | Required | Valid Range | Description |
|-------|------|----------|-------------|-------------|
| `source_id` | `str` | Yes | Regex: `^[a-z0-9-]+$` | Unique source identifier |
| `name` | `str` | Yes | Non-empty string | Display name |
| `fetch_method` | `enum` | Yes | `api`, `rss`, `html` | Fetch method |
| `url` | `str` | Yes | Valid HTTP/HTTPS URL | Source URL or endpoint |
| `enabled` | `bool` | No (default: `true`) | `true`/`false` | Whether source is active |

**Validation**:
- `source_id` must be unique across all sources (built-in + custom)
- `source_id` must match regex `^[a-z0-9-]+$`
- `name` must not be empty
- `fetch_method` must be one of: `api`, `rss`, `html`
- `url` must be a valid HTTP/HTTPS URL
- `enabled` defaults to `true` if not specified

**Example**:
```toml
[[sources.custom]]
source_id = "my-blog"
name = "My AI Blog"
fetch_method = "rss"
url = "https://myblog.com/feed.xml"
enabled = true

[[sources.custom]]
source_id = "another-api"
name = "Another API"
fetch_method = "api"
url = "https://api.example.com/articles"
enabled = false
```

---

## Default Configuration

When no configuration file is found, the following defaults are used:

```toml
[cache]
directory = "~/.ai-digest/cache"
retention_days = 30

[fetcher]
timeout_seconds = 30
max_retries = 3
retry_delays = [1, 2, 4]
user_agent = "ai-daily-digest/1.0 (local CLI tool)"

[summarizer]
compression_ratio = 0.5
min_sentence_length = 5
stopwords_enabled = true

[deduplicator]
similarity_threshold = 0.75
compare_title = true
compare_content = true

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

---

## Validation Rules

### Configuration Validation Process

1. **File Format Validation**:
   - Parse TOML/JSON
   - Reject if syntax errors

2. **Schema Validation**:
   - Check all required fields present
   - Validate field types match schema
   - Check value ranges for numeric fields

3. **Semantic Validation**:
   - Verify `retry_delays` length matches `max_retries`
   - Verify at least one source is enabled
   - Verify custom source IDs don't conflict with built-in IDs
   - Verify at least one of `compare_title` or `compare_content` is true

4. **Path Validation**:
   - Expand `~` in `cache.directory`
   - Create cache directory if it doesn't exist
   - Verify write permissions

---

## Error Handling

### Configuration Errors

**File Not Found** (non-fatal):
```
Warning: No configuration file found at ~/.ai-digest/config.toml or ~/.ai-digest/config.json
Using default configuration.
```

**Parse Error** (fatal):
```
Error: Invalid configuration file: ~/.ai-digest/config.toml

Syntax error at line 12, column 5:
  Expected ']', got ','

Please fix the configuration file or delete it to use defaults.
```

**Validation Error** (fatal):
```
Error: Invalid configuration file: ~/.ai-digest/config.toml

Validation errors:
- fetcher.max_retries: must be between 1 and 10, got 0
- fetcher.retry_delays: length (2) must match max_retries (3)
- sources.enabled: cannot be empty, at least one source required

Please fix the configuration file or delete it to use defaults.
```

**Conflicting Source ID** (fatal):
```
Error: Invalid configuration file: ~/.ai-digest/config.toml

Duplicate source ID detected: "hackernews"
Custom source "hackernews" conflicts with built-in source.

Please rename the custom source or remove it from the configuration.
```

---

## Contract Tests

All configuration behaviors must be verified:

1. **Test: Default config when no file exists**
   - Remove config files
   - Run tool
   - Verify default values used

2. **Test: TOML config loading**
   - Create valid `config.toml`
   - Run tool
   - Verify settings applied

3. **Test: JSON config loading**
   - Create valid `config.json` (remove `.toml`)
   - Run tool
   - Verify settings applied

4. **Test: TOML precedence over JSON**
   - Create both `config.toml` and `config.json`
   - Run tool
   - Verify TOML settings used

5. **Test: Invalid TOML syntax**
   - Create malformed `config.toml`
   - Run tool
   - Verify parse error with line number

6. **Test: Validation errors**
   - Create config with `max_retries = 0`
   - Run tool
   - Verify validation error message

7. **Test: Custom source loading**
   - Add custom source to config
   - Run tool
   - Verify custom source fetched

8. **Test: Disabled sources**
   - Set `enabled = false` for a source
   - Run tool
   - Verify source not fetched

9. **Test: Conflicting source ID**
   - Add custom source with ID "hackernews"
   - Run tool
   - Verify conflict error

---

## Podcast Section (NEW)

### `[podcast]` Section

| Field | Type | Default | Valid Range | Description |
|-------|------|---------|-------------|-------------|
| `default_model` | `str` | `base` | `tiny`, `base`, `small`, `medium` | Default Whisper model size |
| `cleanup_audio` | `bool` | `true` | `true`/`false` | Delete downloaded audio after processing |
| `max_duration_seconds` | `int` | `7200` | `60-14400` | Maximum podcast duration to accept (2h default) |

**Validation**:
- `default_model` must be one of: `tiny`, `base`, `small`, `medium`
- `max_duration_seconds` must be in range [60, 14400] (1 min to 4 hours)

**Example**:
```toml
[podcast]
default_model = "small"
cleanup_audio = true
max_duration_seconds = 7200
```

---

## Configuration Write Contract (NEW)

### Config Save Behavior

When source management commands (`sources add`, `sources remove`, `sources enable`, `sources disable`) modify configuration:

1. **Read**: Load current config from `config.toml` or `config.json` (or generate defaults)
2. **Modify**: Apply the change in-memory
3. **Backup**: Copy existing config file to `config.toml.bak` or `config.json.bak`
4. **Write**: Save modified config to `~/.ai-digest/config.json`

**Why JSON for writes**: `tomllib` (stdlib) is read-only. Writing TOML would require `tomli_w` (external dep). JSON write via stdlib `json` avoids this dependency while maintaining full compatibility — the tool reads TOML first, falls back to JSON.

**Config migration on first write**: If user has a `config.toml` and a source management command modifies config, the tool:
1. Reads `config.toml`
2. Writes changes to `config.json`
3. The next read will prefer `config.toml` (unchanged) — **this is intentional**
4. User-added sources in `config.json` are merged with `config.toml` settings

**Merge strategy**: On load, if both files exist:
- Base settings from `config.toml`
- Custom sources and enabled list from `config.json` override `config.toml` values
- This allows `config.toml` to remain the user's hand-edited file while `config.json` captures programmatic changes

### Contract Tests (Config Write)

10. **Test: Config save creates JSON file**
    - Run `ai-digest sources add --name "Test" --url https://test.com/feed`
    - Verify `~/.ai-digest/config.json` created
    - Verify JSON is valid and contains the new source

11. **Test: Config backup created**
    - With existing config.json, run source management command
    - Verify `config.json.bak` created

12. **Test: Config merge (TOML + JSON)**
    - Have `config.toml` with cache settings
    - Run `ai-digest sources add` to create `config.json`
    - Verify digest uses cache settings from `config.toml` and sources from `config.json`

---

## Document Status

✅ Configuration schema defined for TOML and JSON formats.
✅ All field specifications documented with types, ranges, defaults.
✅ Validation rules and error handling specified.
✅ Default configuration documented.
✅ Contract tests outlined for validation.
✅ Podcast configuration section added.
✅ Config write and merge strategy documented for source management.
✅ Ready for implementation.
