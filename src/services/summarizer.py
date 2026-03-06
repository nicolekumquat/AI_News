"""Extractive summarizer - captures key insights from articles."""

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


def summarize(text: str, max_sentences: int = 3) -> str:
    """
    Extract the most insight-rich sentences from article text.

    Uses frequency-based scoring with position weighting to find
    sentences that capture the core insight or takeaway.

    Args:
        text: Full article text
        max_sentences: Maximum sentences in summary

    Returns:
        Summary as a complete, coherent paragraph
    """
    # Strip any HTML tags from RSS content
    text = _strip_html(text)

    sentences = _split_sentences(text)

    if not sentences:
        return ""

    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    # Score each sentence
    word_freq = _word_frequencies(text)
    scored = []

    for i, sentence in enumerate(sentences):
        score = _score_sentence(sentence, word_freq, i, len(sentences))
        scored.append((i, sentence, score))

    # Select top sentences, preserving original order
    scored.sort(key=lambda x: x[2], reverse=True)
    selected = scored[:max_sentences]
    selected.sort(key=lambda x: x[0])  # restore reading order

    summary = " ".join(s[1] for s in selected)
    return summary


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    import html as html_mod
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode entities like &amp; &lt; &nbsp;
    text = html_mod.unescape(text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, handling common abbreviations."""
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Split on sentence-ending punctuation followed by space + capital
    # or end of string
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

    sentences = []
    for part in parts:
        part = part.strip()
        if len(part) > 20:  # skip very short fragments
            sentences.append(part)

    return sentences


def _word_frequencies(text: str) -> Counter:
    """Calculate word frequencies, excluding stop words."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "and", "but", "or", "nor", "not",
        "so", "yet", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "only", "own", "same", "than", "too",
        "very", "just", "because", "if", "when", "while", "this",
        "that", "these", "those", "it", "its", "he", "she", "they",
        "we", "you", "i", "me", "my", "your", "his", "her", "their",
        "our", "what", "which", "who", "whom", "how", "where", "there",
        "here", "all", "any", "about", "up", "also",
    }

    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in stop_words]
    return Counter(filtered)


def _score_sentence(
    sentence: str,
    word_freq: Counter,
    position: int,
    total_sentences: int,
) -> float:
    """
    Score a sentence for summary inclusion.

    Factors:
    - Word frequency score (important terms)
    - Position bias (first/last sentences often contain key points)
    - Insight signal words
    """
    words = re.findall(r"\b[a-z]{3,}\b", sentence.lower())
    if not words:
        return 0.0

    # Frequency score: average frequency of meaningful words
    freq_score = sum(word_freq.get(w, 0) for w in words) / len(words)

    # Position bias: first 20% and last 10% of article get a boost
    relative_pos = position / max(total_sentences - 1, 1)
    if relative_pos < 0.2:
        position_bonus = 2.0
    elif relative_pos > 0.9:
        position_bonus = 1.5
    else:
        position_bonus = 1.0

    # Insight signal bonus
    insight_signals = {
        "suggest", "reveal", "demonstrate", "show", "found",
        "discover", "conclude", "argue", "propose", "challenge",
        "implication", "significant", "key", "critical", "novel",
        "important", "breakthrough", "surprising", "unlike",
        "however", "despite", "whereas", "contrast",
    }
    signal_hits = sum(1 for w in words if w in insight_signals)
    insight_bonus = 1.0 + (signal_hits * 0.3)

    # Sentence length preference: not too short, not too long
    length_factor = 1.0
    if len(words) < 8:
        length_factor = 0.6
    elif len(words) > 40:
        length_factor = 0.8

    # Penalize promotional/boilerplate sentences
    promo_signals = {
        "subscribe", "newsletter", "podcast", "spotify", "youtube",
        "apple", "listen", "watch", "sponsor", "sponsored",
        "presented", "brought", "workos", "click", "signup",
        "discount", "trial", "coupon", "promo",
    }
    promo_hits = sum(1 for w in words if w in promo_signals)
    if promo_hits >= 2:
        return 0.0  # skip entirely
    promo_factor = 1.0 - (promo_hits * 0.5)

    return freq_score * position_bonus * insight_bonus * length_factor * promo_factor
