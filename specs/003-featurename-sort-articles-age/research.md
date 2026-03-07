# Research: Sort Articles by Age (Newest First)

**Feature**: 003-featurename-sort-articles-age
**Date**: 2026-03-06

## Research Tasks

### 1. Where to insert the date sort in `rank_and_select()`

- **Decision**: Add a `list.sort()` call after the quality filter loop, before the logger.info call
- **Rationale**: The existing loop scores, filters by MIN_SCORE, and caps academic sources. Sorting must happen after all filtering is complete so that low-quality articles don't sneak in just because they're new. Sorting before the loop would be overwritten by the score-based selection.
- **Alternatives considered**:
  - Sort during the filter loop (rejected: the loop selects by score threshold, sorting mid-loop would break the break-on-low-score optimization)
  - Sort in `digest_generator.py` (rejected: `rank_and_select()` is the single point of article ordering — pushing sort elsewhere violates separation of concerns)

### 2. Handling articles with no `published_at`

- **Decision**: Use epoch (1970-01-01 UTC) as fallback sort key for articles with None `published_at`
- **Rationale**: The `NewsArticle` model requires `published_at: datetime` (not Optional), so None should not occur in practice. The defensive fallback handles any edge case without crashing. Articles with epoch date sort to the end since the sort is descending.
- **Alternatives considered**:
  - Raise an error on None (rejected: defensive programming is safer for a sort key)
  - Use `datetime.max` to sort to the beginning (rejected: unknown-date articles should not appear before known-fresh articles)

### 3. Score as tiebreaker for same-timestamp articles

- **Decision**: Use a composite sort key `(published_at, score)` with `reverse=True`
- **Rationale**: Python's tuple comparison naturally handles this — same `published_at` values compare by the second element (score), and `reverse=True` gives descending order for both fields.
- **Alternatives considered**:
  - Two separate sorts (rejected: one stable sort with composite key is idiomatic Python and more efficient)
  - Ignore tiebreaker (rejected: spec FR-002 requires it and it costs nothing extra)

### 4. Impact on plain text vs HTML output

- **Decision**: No changes needed to formatters
- **Rationale**: Both `formatter.py` (plain text) and `html_formatter.py` (HTML) iterate over the article list in order. Since `rank_and_select()` returns the sorted list, both outputs automatically reflect the new ordering.
- **Alternatives considered**: None — this was straightforward.
