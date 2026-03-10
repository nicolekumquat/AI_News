"""Article scorer - ranks articles by user interest profile."""

import logging
from datetime import datetime, timezone

from models.news_article import NewsArticle

logger = logging.getLogger(__name__)

# ── Interest tiers derived from user preference calibration ──
# Rating 2: highly interested
# Rating 1: somewhat interested
# Rating 0: not interested (penalized)

# TIER 2 — Highly interested topics (max boost)
TIER2_KEYWORDS = {
    # Major model releases & competitive landscape
    "gpt", "gpt-4", "gpt-5", "claude", "gemini", "llama", "openai",
    "anthropic", "google", "microsoft", "meta", "nvidia", "apple",
    "release", "announced", "competition", "landscape",
    "versus", "compared", "dominance",
    # AI coding assistants & building software with AI
    "copilot", "cursor", "codex", "coding", "developer", "code",
    "software", "engineering", "programming",
    "workflow", "productivity", "faster", "accelerate",
    # Prompt engineering
    "prompt", "prompting", "chain-of-thought", "few-shot",
    "zero-shot", "system-prompt", "scaffold",
    # Agentic AI
    "agent", "agentic", "autonomous", "mcp", "tool-use",
    "function-calling", "autogpt", "crewai", "langchain",
    "langgraph", "orchestration", "multi-agent", "swarm",
    # Enterprise AI adoption
    "enterprise", "adoption", "organization", "team", "company",
    "roi", "transformation", "strategy", "implementation",
    "business", "industry", "deploy", "production", "scale",
    # Startup disruption
    "startup", "disrupt", "disruption", "founder",
    "product", "customer", "solve", "innovate",
    # Synthesized learnings & thought leadership
    "discovered", "realized", "conclusion", "takeaway",
    "takeaways", "worked", "failed", "succeeded",
    "results", "outcome", "here's", "heres",
    "changed", "rethink", "rethinking",
    "counterintuitive", "unexpected",
    # Predictions & future of AI/work
    "prediction", "future", "vision", "paradigm", "shift",
    "forecast", "inevitable", "emerging", "next",
    "implication", "implications", "consequence",
    "mollick", "schillace", "ng", "altman", "amodei", "lecun",
    "karpathy",
}

# TIER 1 — Somewhat interested topics (moderate boost)
TIER1_KEYWORDS = {
    # Regulation & governance
    "regulation", "policy", "governance", "compliance", "law",
    "congress", "senate", "eu", "legislation",
    # Safety & alignment
    "safety", "alignment", "guardrails", "responsible",
    "trustworthy", "reliable",
    # Non-technical AI use
    "writing", "design", "marketing", "legal", "creative",
    "content", "education", "healthcare", "finance",
    # Hardware & infrastructure
    "gpu", "inference", "cost", "latency", "hardware",
    "infrastructure", "chip", "compute", "efficiency",
    # Ethics & societal impact
    "ethics", "bias", "fairness", "impact", "society",
    "jobs", "displacement", "inequality",
    # RAG & embeddings
    "rag", "retrieval", "embedding", "vector", "knowledge",
    "search", "index", "context-window",
}

# TIER 0 — Not interested (penalize these)
TIER0_PENALTY_KEYWORDS = {
    # Benchmarks & evaluation
    "benchmark", "benchmarks", "mmlu", "leaderboard", "score",
    "f1-score", "accuracy", "precision", "recall", "bleu",
    "perplexity", "evaluation", "evaluated", "sota",
    "state-of-the-art", "outperforms", "outperformed",
    # Academic architecture papers
    "architecture", "transformer", "attention-head", "ablation",
    "ablations", "baseline", "baselines", "variant", "variants",
    "module", "layer", "encoder", "decoder", "feedforward",
    # Training optimization
    "pretraining", "pre-training", "fine-tuning", "finetuning",
    "hyperparameter", "batch-size", "learning-rate", "epoch",
    "convergence", "gradient", "loss", "optimizer", "warmup",
    "regularization", "dropout",
    # Open-source fine-tuning community
    "lora", "qlora", "adapter", "quantization", "4-bit",
    "8-bit", "gguf", "ggml", "ollama", "huggingface",
    # Academic paper signals
    "arxiv", "peer-reviewed", "hypothesis", "experiment",
    "supplementary", "appendix", "table-1", "figure-1",
    "we-propose", "we-introduce", "we-present", "we-show",
    "dataset", "corpus", "annotation",
}

# Shallow / routine content (always penalize)
SHALLOW_KEYWORDS = {
    "funding", "valuation", "raises", "series-a", "series-b",
    "hiring", "layoff", "stock", "revenue", "ipo",
    "sponsored", "advertisement", "deal", "discount", "promo",
    "changelog", "release-notes", "patch", "bugfix",
    # Event promotions
    "hackathon", "sign-up", "register", "free-event",
    # Conference gossip
    "spotlight", "poster", "oral", "accepted-at", "openreview",
    # HR / hiring announcements
    "appointed", "chief", "officer", "cpo", "cto", "coo",
}

# Low-level technical implementation (penalize)
# User doesn't want ML infrastructure/plumbing details
LOWLEVEL_TECH_KEYWORDS = {
    # ML frameworks & internals
    "pytorch", "tensorflow", "jax", "keras", "triton",
    "cuda", "kernel", "kernels", "gpu-programming",
    "matmul", "tensor", "tensorrt", "onnx",
    # Implementation plumbing
    "scheduler", "schedulers", "optimizer", "optimizers",
    "dataloader", "pipeline", "batch", "batching",
    "checkpoint", "checkpointing", "serialization",
    # Low-level systems
    "metal", "vulkan", "opengl", "cpu", "simd",
    "memory", "buffer", "allocation", "synchronization",
    "fp8", "fp16", "bf16", "int8", "quantization",
    "sparse", "sparsity", "pruning",
    # Library/package updates
    "implementation", "codebase", "repository", "repo",
    "package", "library", "dependency", "dependencies",
    "mnist", "cifar", "imagenet",
    # Robotics / niche hardware
    "robotics", "robot", "pose", "slam",
}

# Help-seeking / career advice / questions without insights (penalize)
HELPSEEKING_KEYWORDS = {
    # "How do I learn X" / seeking advice
    "how-do-i", "how-do-you", "how-can-i", "should-i",
    "any-tips", "any-advice", "any-suggestions",
    "recommend", "recommendations", "suggestion", "suggestions",
    "looking-for", "searching-for", "need-help",
    "beginner", "newbie", "getting-started", "start-learning",
    "where-can-i", "where-do-i", "where-should-i",
    "which-is-better", "what-should-i",
    # Career / role change
    "transitioning", "transition", "career", "portfolio",
    "resume", "interview", "job", "hiring-manager",
    "entry-level", "junior", "internship", "bootcamp",
    "self-taught", "degree", "phd", "masters", "undergrad",
    # Asking others (not sharing insights)
    "thoughts", "opinions", "feedback", "curious",
    "wondering", "confused", "stuck", "struggling",
    "help", "please", "eli5", "explain",
    "forgetting", "forget", "remember",
}

# Preferred sources: practitioners and thought leaders
PREFERRED_SOURCES = {
    "ethan-mollick", "andrew-ng", "sam-schillace",
    "simon-willison", "latent-space", "ai-snake-oil",
    "pragmatic-engineer", "lennys-newsletter", "import-ai",
    "semi-analysis", "benedict-evans", "chip-huyen",
    "reddit-chatgpt", "reddit-localllama", "reddit-artificial",
    "hackernews", "openai", "anthropic", "deepmind",
}

MAX_DIGEST_ARTICLES = 15


def score_article(article: NewsArticle) -> float:
    """
    Score an article 0-100 based on user interest profile.

    Tier 2 (high interest): major models, coding with AI, prompting,
        agents, enterprise, startups, thought leaders, dev stories
    Tier 1 (moderate): regulation, safety, non-tech AI, hardware,
        ethics, RAG
    Tier 0 (penalized): benchmarks, academic papers, training
        optimization, fine-tuning community
    """
    score = 0.0
    text = (article.title + " " + article.content).lower()
    words = text.split()
    word_count = len(words)

    # Content depth: prefer substantive articles (200-2000 words)
    if word_count < 100:
        score += 5
    elif word_count < 300:
        score += 15
    elif word_count < 1000:
        score += 25
    elif word_count < 2000:
        score += 20
    else:
        score += 15

    stripped = [w.strip(".,;:!?()[]\"'") for w in words]

    # Tier 2 keywords — highest boost (max 35 points)
    t2_hits = sum(1 for w in stripped if w in TIER2_KEYWORDS)
    t2_density = t2_hits / max(word_count, 1)
    score += min(t2_density * 700, 35)

    # Tier 1 keywords — moderate boost (max 15 points)
    t1_hits = sum(1 for w in stripped if w in TIER1_KEYWORDS)
    t1_density = t1_hits / max(word_count, 1)
    score += min(t1_density * 400, 15)

    # Tier 0 penalty — very strong (max -45 points)
    t0_hits = sum(1 for w in stripped if w in TIER0_PENALTY_KEYWORDS)
    t0_density = t0_hits / max(word_count, 1)
    score -= min(t0_density * 900, 45)

    # Shallow content penalty (max -15 points)
    shallow_hits = sum(1 for w in stripped if w in SHALLOW_KEYWORDS)
    shallow_density = shallow_hits / max(word_count, 1)
    score -= min(shallow_density * 400, 15)

    # Low-level technical implementation penalty (max -35 points)
    lowlevel_hits = sum(1 for w in stripped if w in LOWLEVEL_TECH_KEYWORDS)
    lowlevel_density = lowlevel_hits / max(word_count, 1)
    score -= min(lowlevel_density * 800, 35)

    # Help-seeking / career / question-asking penalty (phrase-based)
    helpseeking_phrases = [
        "how do i", "how do you", "how can i", "how did you",
        "should i", "any tips", "any advice", "any suggestions",
        "looking for", "searching for", "need help",
        "where can i", "where do i", "where should i",
        "which is better", "what should i",
        "recommend", "recommendations",
        "beginner", "newbie", "getting started", "start learning",
        "transitioning", "transition to", "career",
        "portfolio", "resume", "interview", "entry-level",
        "internship", "bootcamp", "self-taught",
        "thoughts?", "opinions?", "feedback?",
        "wondering", "confused", "stuck", "struggling",
        "eli5", "explain like",
        "i keep forgetting", "keep forgetting",
        "stay up to date", "find more information",
        "can someone explain", "does anyone know",
        "what are the best", "what is the best",
    ]
    help_phrase_hits = sum(1 for p in helpseeking_phrases if p in text)
    score -= min(help_phrase_hits * 8, 30)

    # Source boost (max 10 points)
    if article.source_id.lower() in PREFERRED_SOURCES:
        score += 10

    # Title quality: sharing insights, not asking questions (max 10 points)
    title_lower = article.title.lower()

    # Low-level tech title penalty (strong signal)
    lowlevel_title_phrases = [
        "pytorch", "tensorflow", "tensorrt", "triton", "cuda",
        "mnist", "cifar", "kernel", "fp8", "fp16", "bf16",
        "inference on", "from scratch", "scheduler",
        "implementation", "onnx", "metal", "gpu v",
        "spark", "scala", "dataloader", "booster",
        "v1.", "v2.", "v0.", "release",
        "hackathon", "hiring", "appointed", "spotlight",
        "iclr", "icml", "neurips", "cvpr", "aaai",
        "dissertation", "thesis",
    ]
    if any(phrase in title_lower for phrase in lowlevel_title_phrases):
        score -= 15

    # Boost: sharing synthesized learnings
    if any(phrase in title_lower for phrase in (
        "how i", "how we", "why i", "why we",
        "what i learned", "what we learned",
        "here's what", "heres what",
        "lessons from", "lesson learned",
        "i built", "we built", "i shipped", "we shipped",
        "worked and", "didn't work", "what worked",
        "future of", "state of", "prediction",
    )):
        score += 10
    # Penalize: asking for help or advice
    title_is_question = any(phrase in title_lower for phrase in (
        "how do you", "how do i", "how can i",
        "any tips", "any advice", "should i",
        "looking for", "where can i", "where do i",
        "how did you", "eli5", "help me",
        "transitioning to", "career", "stay up to date",
        "find more information", "can someone",
        "does anyone", "what are the best",
        "what's the", "whats the", "what is the",
        "what do you", "what did you", "what has",
        "have you", "do you", "did you",
    )) or title_lower.rstrip().endswith("?")
    if title_is_question:
        score -= 15

    # Extra penalty for short question posts (< 150 words) — these are
    # crowdsourcing questions, not shareable insights
    if title_is_question and word_count < 150:
        score -= 15

    # Unique word diversity bonus (max 10 points)
    unique_ratio = len(set(words)) / max(word_count, 1)
    score += unique_ratio * 10

    return max(0.0, min(100.0, score))


def rank_and_select(
    articles: list[NewsArticle],
    max_articles: int = MAX_DIGEST_ARTICLES,
) -> list[tuple[NewsArticle, float]]:
    """
    Rank articles by user interest score and return top N.

    Returns list of (article, score) tuples, highest score first.
    """
    # Minimum quality threshold — don't pad digest with junk
    MIN_SCORE = 25.0

    scored = [(article, score_article(article)) for article in articles]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Academic sources (arxiv) capped at 10% of digest
    ACADEMIC_SOURCES = {"arxiv"}
    max_academic = max(1, int(max_articles * 0.10))

    selected = []
    academic_count = 0
    for article, s in scored:
        if len(selected) >= max_articles:
            break
        if s < MIN_SCORE:
            break  # everything below here is low quality
        is_academic = article.source_id.lower() in ACADEMIC_SOURCES
        if is_academic:
            if academic_count >= max_academic:
                continue
            academic_count += 1
        selected.append((article, s))

    # Sort by published_at descending (newest first), score as tiebreaker
    _epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    selected.sort(
        key=lambda x: (x[0].published_at if x[0].published_at else _epoch, x[1]),
        reverse=True,
    )

    logger.info(
        f"Ranked {len(articles)} articles, selected top {len(selected)} "
        f"(score range: {selected[-1][1]:.1f}-{selected[0][1]:.1f})"
        if selected else f"No articles to rank"
    )

    return selected
