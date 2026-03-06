# Feature Specification: Sort Articles by Age (Newest First)

**Feature Branch**: `003-featurename-sort-articles-age`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: FEAT-001 from backlog.md — Articles should be sorted by age, with the newest articles first

## Problem Statement

Currently, articles in the digest are sorted by relevance score (highest score first) via `rank_and_select()` in `src/services/scorer.py`. There is no consideration of publication date in the ordering. Users want the most recent articles to appear first so the digest feels current and timely.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Newest articles appear first in digest (Priority: P1)

As a user reading my daily AI digest, I want the articles ordered by publication date (newest first) so I see the most current news at the top.

**Why this priority**: This is the entire feature — the digest should feel timely, with breaking news at the top.

**Independent Test**: Generate a digest from articles with different `published_at` timestamps and verify the output order matches newest-to-oldest.

**Acceptance Scenarios**:

1. **Given** a digest with articles published at different times, **When** the digest is generated, **Then** articles are ordered by `published_at` descending (newest first)
2. **Given** two articles with the same `published_at` timestamp, **When** the digest is generated, **Then** their relative order is determined by relevance score (higher score first) as a tiebreaker
3. **Given** an article with no `published_at` value (None), **When** the digest is generated, **Then** that article appears after all articles with valid timestamps

---

### User Story 2 - Consistent ordering in both plain text and HTML output (Priority: P1)

As a user, I want the same article order regardless of whether I use `--html` or plain text output.

**Why this priority**: Both output formats should present the same ordering — this is a consistency requirement.

**Independent Test**: Generate a digest in both formats and verify article order is identical.

**Acceptance Scenarios**:

1. **Given** a digest with multiple articles, **When** output as plain text, **Then** articles are ordered newest first
2. **Given** the same digest, **When** output as HTML, **Then** articles appear in the same order as plain text

---

### Edge Cases

- Articles with identical `published_at` timestamps should fall back to relevance score ordering.
- Articles with `None` for `published_at` should sort to the end, not the beginning.
- The relevance score filtering (minimum score threshold, academic cap) should still apply *before* the date sort — low-quality articles should not appear just because they're new.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: After scoring and filtering, the final article list MUST be sorted by `published_at` descending (newest first)
- **FR-002**: Articles with identical `published_at` values MUST use relevance score as a secondary sort (higher score first)
- **FR-003**: Articles with `None` `published_at` MUST appear after all dated articles
- **FR-004**: The minimum quality threshold and academic cap from `rank_and_select()` MUST still apply — sorting is a post-filter step
- **FR-005**: Both plain text and HTML output MUST reflect the same article order

### Non-Functional Requirements

- **NFR-001**: No new dependencies required
- **NFR-002**: No CLI interface changes — this is a behavior change in digest generation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any digest with N articles, article[i].published_at >= article[i+1].published_at for all i (or article[i+1] has None published_at)
- **SC-002**: Relevance score filtering continues to exclude low-quality articles (no regression in quality)
- **SC-003**: Existing tests pass without modification (aside from sort-order-specific assertions)
