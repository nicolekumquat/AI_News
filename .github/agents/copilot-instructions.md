# Test_Project Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-25

## Active Technologies
- Python 3.11+ + requests, feedparser, beautifulsoup4+lxml (HTTP client, RSS parsing, HTML parsing) (001-daily-news-aggregation)
- Local filesystem (JSON/YAML cache files for articles and digests) (001-daily-news-aggregation)
- Python 3.11+ + requests, feedparser, beautifulsoup4, lxml (existing); yt-dlp (new, audio extraction); faster-whisper (new, local speech-to-text transcription) (001-daily-news-aggregation)
- Local filesystem JSON files (`~/.ai-digest/cache/`) (001-daily-news-aggregation)
- Python 3.11+ + None new — uses stdlib `datetime` only (003-featurename-sort-articles-age)
- N/A (no storage changes) (003-featurename-sort-articles-age)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 003-featurename-sort-articles-age: Added Python 3.11+ + None new — uses stdlib `datetime` only
- 003-featurename-sort-articles-age: Added Python 3.11+ + None new — uses stdlib `datetime` only
- 001-daily-news-aggregation: Added Python 3.11+ + requests, feedparser, beautifulsoup4, lxml (existing); yt-dlp (new, audio extraction); faster-whisper (new, local speech-to-text transcription)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
