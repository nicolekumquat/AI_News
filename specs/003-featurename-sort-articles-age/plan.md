# Implementation Plan: Sort Articles by Age (Newest First)

**Branch**: `003-featurename-sort-articles-age` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-featurename-sort-articles-age/spec.md`

## Summary

After scoring and quality filtering, the selected articles are re-sorted by `published_at` descending (newest first) with relevance score as a tiebreaker for same-timestamp articles. This is a single-function change in `rank_and_select()` in `src/services/scorer.py` — no new dependencies, no CLI changes, no API changes.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: None new — uses stdlib `datetime` only
**Storage**: N/A (no storage changes)
**Testing**: pytest
**Target Platform**: Local execution (Windows, macOS, Linux)
**Project Type**: CLI tool
**Performance Goals**: Negligible overhead — one `list.sort()` on ≤15 items
**Constraints**: Must not break existing quality filtering (MIN_SCORE threshold, academic cap)
**Scale/Scope**: Single sort operation on max 15 pre-filtered articles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Content-First** | ✅ PASS | Sorting by freshness directly improves content delivery — users see the most current AI news first. Aligns with constitution's "content freshness: items older than 48h SHOULD be deprioritized" standard. |
| **II. Test-First (TDD)** | ✅ PASS | Tests written in `tests/unit/test_sort_by_age.py` covering: newest-first ordering, score tiebreaker, epoch fallback, quality filter preservation. 4/4 passing. |
| **III. Simplicity** | ✅ PASS | Single sort call added after existing filter loop. No new dependencies, no new abstractions, no new modules. Uses stdlib `datetime` only. |
| **Tech Stack** | ✅ PASS | Python 3.11+, pytest, local-only. No new packages. |
| **Content Standards** | ✅ PASS | 15-article cap preserved. Quality threshold preserved. Freshness prioritized per constitution mandate. |

### Post-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Content-First** | ✅ PASS | No change from pre-design assessment. |
| **II. Test-First (TDD)** | ✅ PASS | 4 tests written and passing. |
| **III. Simplicity** | ✅ PASS | Implementation is 5 lines of code in one function. Zero new abstractions. |

## Project Structure

### Documentation (this feature)

```text
specs/003-featurename-sort-articles-age/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (affected files)

```text
src/
└── services/
    └── scorer.py          # Modified: rank_and_select() post-filter sort

tests/
└── unit/
    └── test_sort_by_age.py  # New: 4 test cases for date sorting
```

**Structure Decision**: Single project layout. No new modules or directories needed — this is a behavior change within one existing function.
