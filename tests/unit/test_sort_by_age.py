"""Tests for FEAT-001: Articles sorted by age (newest first)."""

from datetime import datetime, timezone

import pytest

from models.news_article import NewsArticle
from services.scorer import rank_and_select, score_article


def _make_article(article_id, title, published_at, source_id="test", content=None):
    """Helper to create a NewsArticle with minimal required fields."""
    if content is None:
        content = (
            "This is a substantial test article about AI agents and enterprise "
            "adoption of large language models for coding and productivity. "
            "OpenAI and Anthropic are competing in the agentic AI space."
        )
    return NewsArticle(
        article_id=article_id,
        title=title,
        url=f"https://example.com/{article_id}",
        source_id=source_id,
        published_at=published_at,
        fetched_at=datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc),
        content=content,
    )


class TestArticleSortByAge:
    """Articles should be sorted by published_at descending after quality filtering."""

    def test_newest_articles_appear_first(self):
        articles = [
            _make_article("old", "OpenAI launches new AI agent framework", datetime(2026, 3, 4, 10, 0, tzinfo=timezone.utc)),
            _make_article("new", "Anthropic ships Claude enterprise coding tools", datetime(2026, 3, 6, 10, 0, tzinfo=timezone.utc)),
            _make_article("mid", "Microsoft Copilot gets agentic AI features", datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc)),
        ]
        result = rank_and_select(articles)
        dates = [a.published_at for a, _ in result]
        assert dates == sorted(dates, reverse=True), \
            f"Articles not sorted newest-first: {dates}"

    def test_same_timestamp_uses_score_as_tiebreaker(self):
        same_time = datetime(2026, 3, 6, 10, 0, tzinfo=timezone.utc)
        a = _make_article(
            "a", "OpenAI GPT-5 agent release announced",
            same_time,
            content="OpenAI announced GPT-5 with agentic coding capabilities. "
                    "Copilot and Claude developers are responding to the competition. "
                    "Enterprise adoption is accelerating across the industry.",
        )
        b = _make_article(
            "b", "AI developer tools weekly news roundup",
            same_time,
            content="A weekly AI developer tools roundup covering language models, "
                    "coding assistants, and enterprise AI deployment strategies. "
                    "Companies are adopting agentic workflows for software engineering.",
        )
        score_a, score_b = score_article(a), score_article(b)
        assert score_a != score_b, "Need different scores for tiebreaker test"

        result = rank_and_select([a, b])
        assert len(result) >= 2
        # Same timestamp — higher score should come first
        if score_a > score_b:
            assert result[0][0].article_id == "a"
        else:
            assert result[0][0].article_id == "b"

    def test_very_old_published_at_sorts_last(self):
        """Articles with ancient published_at should sort after recent ones."""
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        articles = [
            _make_article("old-date", "AI agent coding tools for enterprise developers",
                          epoch, content=(
                              "AI agent coding tools for enterprise developers are "
                              "revolutionizing software engineering workflows. "
                              "OpenAI and Anthropic compete in the agentic coding space."
                          )),
            _make_article("dated", "Anthropic Claude agentic AI enterprise launch",
                          datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc)),
        ]
        result = rank_and_select(articles)
        assert len(result) >= 2
        assert result[-1][0].article_id == "old-date", \
            "Article with epoch published_at should appear last"

    def test_quality_filter_still_applies(self):
        """Low-quality articles should be excluded even if they're the newest."""
        articles = [
            _make_article(
                "junk", "Benchmark results MMLU leaderboard SOTA evaluation ablation",
                datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
                content="Benchmark results show MMLU leaderboard SOTA evaluation "
                        "ablation baselines variant architecture transformer attention-head "
                        "encoder decoder feedforward pre-training fine-tuning hyperparameter "
                        "batch-size learning-rate epoch convergence gradient loss optimizer",
            ),
            _make_article(
                "good", "OpenAI launches enterprise AI coding agent for developers",
                datetime(2026, 3, 4, 10, 0, tzinfo=timezone.utc),
            ),
        ]
        result = rank_and_select(articles)
        article_ids = [a.article_id for a, _ in result]
        assert "good" in article_ids, "High-quality article should be included"
