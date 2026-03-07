# Quickstart: Sort Articles by Age (Newest First)

**Feature**: 003-featurename-sort-articles-age

## What Changed

The daily digest now sorts articles by publication date (newest first) instead of by relevance score alone. The quality filter still applies — low-quality articles are excluded regardless of recency.

## Usage

No CLI changes. Run the digest as usual:

```bash
# Plain text (default)
ai-digest

# HTML output
ai-digest --html
```

Articles will appear newest-first in both formats.

## How It Works

1. Articles are fetched from all enabled sources
2. Each article is scored by the interest profile (unchanged)
3. Articles below MIN_SCORE (25.0) are excluded (unchanged)
4. Academic sources are capped at 10% of digest (unchanged)
5. **NEW**: Remaining articles are re-sorted by `published_at` descending
6. Articles with the same timestamp use relevance score as tiebreaker

## Running Tests

```bash
python -m pytest tests/unit/test_sort_by_age.py -v
```
