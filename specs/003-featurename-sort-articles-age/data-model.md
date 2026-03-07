# Data Model: Sort Articles by Age (Newest First)

**Feature**: Sort Articles by Age (Newest First)
**Branch**: `003-featurename-sort-articles-age`
**Date**: 2026-03-06

This feature does not introduce new entities. It modifies the output ordering of the existing `rank_and_select()` function.

---

## Affected Entities

### NewsArticle (existing, unchanged)

The `published_at` field is used as the primary sort key.

| Field | Type | Required | Role in this feature |
|-------|------|----------|---------------------|
| `published_at` | `datetime` (UTC) | Yes | Primary sort key (descending) |

**Validation Rules**: No changes. `published_at` is required and must be ≤ `fetched_at`.

---

## Behavioral Change

### `rank_and_select()` output ordering

**Before**: Articles returned sorted by relevance score descending.

**After**: Articles returned sorted by `published_at` descending (newest first), with relevance score as tiebreaker for identical timestamps.

**Sort key**: `(published_at, score)` with `reverse=True`

**Fallback**: If `published_at` is somehow None (not possible per model validation), epoch `1970-01-01T00:00:00Z` is used, sorting the article to the end.

**Invariants preserved**:
- MAX_DIGEST_ARTICLES (15) cap still applies
- MIN_SCORE (25.0) quality threshold still applies
- Academic source cap (10%) still applies
- Scoring algorithm is unchanged
