"""Default news sources configuration."""

from models.news_source import NewsSource


def get_default_sources() -> list[NewsSource]:
    """
    Get default AI news sources.

    Returns:
        List of configured NewsSource objects
    """
    return [
        # --- Aggregators / community platforms ---
        NewsSource(
            source_id="hackernews",
            name="HackerNews",
            fetch_method="api",
            url="https://hn.algolia.com/api/v1/search_by_date",
            enabled=True,
        ),
        NewsSource(
            source_id="reddit-chatgpt",
            name="Reddit r/ChatGPT",
            fetch_method="api",
            url="https://www.reddit.com/r/ChatGPT/top.json",
            enabled=True,
        ),
        NewsSource(
            source_id="reddit-localllama",
            name="Reddit r/LocalLLaMA",
            fetch_method="api",
            url="https://www.reddit.com/r/LocalLLaMA/top.json",
            enabled=True,
        ),
        NewsSource(
            source_id="reddit-artificial",
            name="Reddit r/artificial",
            fetch_method="api",
            url="https://www.reddit.com/r/artificial/top.json",
            enabled=True,
        ),
        NewsSource(
            source_id="arxiv",
            name="ArXiv AI/ML",
            fetch_method="api",
            url="http://export.arxiv.org/api/query",
            enabled=True,
        ),

        # --- AI company blogs ---
        NewsSource(
            source_id="openai",
            name="OpenAI News",
            fetch_method="rss",
            url="https://openai.com/news/rss.xml",
            enabled=True,
        ),
        NewsSource(
            source_id="deepmind",
            name="Google DeepMind",
            fetch_method="rss",
            url="https://deepmind.google/blog/rss.xml",
            enabled=True,
        ),
        NewsSource(
            source_id="anthropic",
            name="Anthropic Engineering",
            fetch_method="rss",
            url="https://www.anthropic.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="meta-ai",
            name="Meta AI Research",
            fetch_method="rss",
            url="https://ai.meta.com/blog/rss/",
            enabled=True,
        ),

        # --- Thought leaders & practitioners (Substacks / blogs) ---
        NewsSource(
            source_id="sam-schillace",
            name="Sam Schillace (Sunday Letters)",
            fetch_method="rss",
            url="https://sundaylettersfromsam.substack.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="ethan-mollick",
            name="Ethan Mollick (One Useful Thing)",
            fetch_method="rss",
            url="https://oneusefulthing.substack.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="andrew-ng",
            name="Andrew Ng (The Batch)",
            fetch_method="rss",
            url="https://www.deeplearning.ai/the-batch/feed/",
            enabled=True,
        ),
        NewsSource(
            source_id="simon-willison",
            name="Simon Willison's Weblog",
            fetch_method="rss",
            url="https://simonwillison.net/atom/everything/",
            enabled=True,
        ),
        NewsSource(
            source_id="latent-space",
            name="Latent Space (AI Engineering)",
            fetch_method="rss",
            url="https://www.latent.space/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="ai-snake-oil",
            name="AI Snake Oil",
            fetch_method="rss",
            url="https://www.aisnakeoil.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="pragmatic-engineer",
            name="The Pragmatic Engineer",
            fetch_method="rss",
            url="https://newsletter.pragmaticengineer.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="lennys-newsletter",
            name="Lenny's Newsletter",
            fetch_method="rss",
            url="https://www.lennysnewsletter.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="import-ai",
            name="Import AI (Jack Clark)",
            fetch_method="rss",
            url="https://importai.substack.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="semi-analysis",
            name="SemiAnalysis",
            fetch_method="rss",
            url="https://www.semianalysis.com/feed",
            enabled=True,
        ),
        NewsSource(
            source_id="benedict-evans",
            name="Benedict Evans",
            fetch_method="rss",
            url="https://www.ben-evans.com/benedictevans?format=rss",
            enabled=True,
        ),
        NewsSource(
            source_id="chip-huyen",
            name="Chip Huyen",
            fetch_method="rss",
            url="https://huyenchip.com/feed.xml",
            enabled=True,
        ),
    ]
