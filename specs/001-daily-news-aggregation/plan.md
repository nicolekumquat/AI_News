# Implementation Plan: Source Management & Podcast Summarization

**Branch**: `001-daily-news-aggregation` | **Date**: 2026-03-04 | **Spec**: [spec.md](specs/001-daily-news-aggregation/spec.md)
**Input**: User request to add (1) source management CLI commands and (2) podcast summarization capability

**Note**: This plan extends the existing Daily News Aggregation feature with two new capabilities.

## Summary

Two enhancements to the existing AI Daily Digest:

1. **Source Management**: CLI subcommands to list, add, remove, enable, and disable news sources (URLs, blogs, experts) without manually editing config files. This gives users interactive control over their curated source list.

2. **Podcast Summarization**: A new CLI subcommand that accepts a podcast URL (audio or episode page), downloads/extracts the audio, transcribes it, and generates a concise summary. This extends the digest to cover audio content.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: requests, feedparser, beautifulsoup4, lxml (existing); yt-dlp (new, audio extraction); faster-whisper (new, local speech-to-text transcription)  
**Storage**: Local filesystem JSON files (`~/.ai-digest/cache/`)  
**Testing**: pytest  
**Target Platform**: Local execution (Windows, macOS, Linux)  
**Project Type**: CLI tool  
**Performance Goals**: Source management: instant (<1s). Podcast: transcription within ~2x audio length on CPU  
**Constraints**: Local-only execution per constitution. Podcast transcription must run offline without cloud APIs. Audio file size practical limit ~500MB.  
**Scale/Scope**: Single-user CLI tool, managing ~20-50 sources, processing 1 podcast at a time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Content-First** | ✅ PASS | Source management directly improves content curation. Podcast summarization extends content coverage to audio. Both serve the goal of delivering concise AI news. |
| **II. Test-First (TDD)** | ✅ PASS | Plan requires TDD for all new code. Tests specified for each feature. |
| **III. Simplicity** | ⚠️ REVIEW | Podcast transcription requires new dependencies (audio extraction + speech-to-text). Must justify each dependency and prefer minimal solutions. |
| **Tech Stack** | ✅ PASS | Python 3.11+, pytest, ruff, local-only. |
| **Content Standards** | ✅ PASS | Source management enforces attribution. Podcast summaries will follow same transformation rules (no raw text). |

**Simplicity justification for podcast feature**: Audio transcription cannot be achieved with stdlib alone. A local speech-to-text model is the simplest approach that satisfies the local-only constraint while avoiding cloud API dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/001-daily-news-aggregation/
├── plan.md              # This file (updated for new features)
├── research.md          # Phase 0 output (updated)
├── data-model.md        # Phase 1 output (updated)
├── quickstart.md        # Phase 1 output (updated)
├── contracts/           # Phase 1 output (updated)
│   ├── cli-interface.md
│   └── config-schema.md
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── news_source.py       # Existing (no changes)
│   ├── news_article.py      # Existing (no changes)
│   ├── digest_entry.py      # Existing (no changes)
│   ├── digest.py            # Existing (no changes)
│   └── podcast.py           # NEW: PodcastEpisode & PodcastSummary models
├── services/
│   ├── fetcher.py           # Existing (no changes)
│   ├── cache.py             # Existing (minor: persist source changes)
│   ├── content_extractor.py # Existing (no changes)
│   ├── digest_generator.py  # Existing (no changes)
│   ├── scorer.py            # Existing (no changes)
│   ├── summarizer.py        # Existing (reused for podcast text summarization)
│   ├── source_manager.py    # NEW: CRUD operations for sources
│   └── podcast_service.py   # NEW: download, transcribe, summarize podcasts
│   └── fetchers/            # Existing (no changes)
├── cli/
│   ├── __main__.py          # Existing (add subcommand routing)
│   ├── commands.py          # Existing (add source & podcast subcommands)
│   ├── formatter.py         # Existing (no changes)
│   └── html_formatter.py    # Existing (no changes)
└── config/
    ├── loader.py            # Existing (minor: save config support)
    ├── sources.py           # Existing (no changes to defaults)
    └── logging.py           # Existing (no changes)

tests/
├── unit/
│   ├── test_source_manager.py    # NEW
│   ├── test_podcast_service.py   # NEW
│   └── ...                       # Existing tests unchanged
├── integration/
│   ├── test_source_management.py # NEW
│   ├── test_podcast_summary.py   # NEW
│   └── ...                       # Existing tests unchanged
└── contract/
    ├── test_cli_sources.py       # NEW
    ├── test_cli_podcast.py       # NEW
    └── ...
```

**Structure Decision**: Follows existing single-project structure. New files added alongside existing modules. No structural changes required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New dependency: `yt-dlp` for audio extraction | Podcast audio download from diverse hosting platforms (Spotify pages, YouTube, direct MP3 links) | Manual `requests` download only handles direct MP3 URLs; most podcast pages require extraction logic that yt-dlp already handles |
| New dependency: `faster-whisper` for transcription | Local speech-to-text required by local-only constraint | No stdlib solution for speech-to-text. Cloud APIs violate constitution. `faster-whisper` is 4x faster than `openai-whisper`, CPU-only, and the simplest local model. |

## Constitution Check — Post-Design Re-evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Content-First** | ✅ PASS | Source management gives users direct control over content curation. Podcast summarization extends digest coverage to audio content. Both features serve the core goal. |
| **II. Test-First (TDD)** | ✅ PASS | All new modules have corresponding test files specified. Contract tests defined for CLI behavior. Unit tests planned for source_manager and podcast_service. |
| **III. Simplicity** | ✅ PASS (with justified exceptions) | Source management reuses existing config system — zero new dependencies. Podcast feature adds 2 new deps (`yt-dlp`, `faster-whisper`) as **optional extras** so base install is unchanged. Each dep justified in Complexity Tracking. Config writes use stdlib `json` instead of adding `tomli_w`. |
| **Tech Stack** | ✅ PASS | Python 3.11+, pytest, ruff, local-only. Podcast transcription runs offline via `faster-whisper` (CPU). |
| **Content Standards** | ✅ PASS | Source management preserves required source attribution. Podcast summaries go through same transformation pipeline as article summaries — no raw transcript text. 15-article cap and insight-driven curation mandated. |
| **Governance** | ✅ PASS | No constitutional amendments needed. New features are extensions within existing principles. |

**Gate result**: ✅ ALL GATES PASS. Ready for task breakdown (/speckit.tasks).
