"""Regression tests for noisy link-list text leaking into digest summaries."""

import os
import sys

# Allow imports from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from services.digest_generator import _fallback_summary
from services.summarizer import summarize


def test_fallback_summary_strips_html_and_link_list_tail():
    content = """
    <div><p>Product Introduction to Yash. The burden of 150 daily Slack notifications.</p>
    <p>When to use AI for tasks vs building deterministic code.</p>
    <p>Links mentioned:</p>
    <ul>
      <li>Perplexity Computer: https://www.perplexity.ai/computer/new</li>
      <li>OpenClaw: https://openclaw.ai/</li>
      <li>Discord: https://discord.com/</li>
    </ul></div>
    """

    summary = _fallback_summary(content)

    assert "Product Introduction to Yash" in summary
    assert "Slack notifications" in summary
    assert "Links mentioned" not in summary
    assert "https://" not in summary
    assert "<" not in summary


def test_summarize_removes_url_heavy_resources_section():
    text = (
        "The team built a deterministic Slack triage workflow that reduced noise by half. "
        "They used connectors to automate follow-up actions across Notion and Asana. "
        "Resources: https://a.com https://b.com https://c.com https://d.com"
    )

    summary = summarize(text, max_sentences=3)

    assert "deterministic Slack triage workflow" in summary
    assert "connectors to automate" in summary
    assert "Resources" not in summary
    assert "https://" not in summary


def test_summarize_truncates_at_earliest_valid_noise_marker():
    text = (
        "Product Introduction to Yash. The burden of 150 daily Slack notifications. "
        "Lightning round and final thoughts: Perplexity Computer https://www.perplexity.ai/computer/new "
        "OpenClaw https://openclaw.ai/ Discord https://discord.com/ "
        "Where to find Claire Vo: https://clairevo.com/"
    )

    summary = summarize(text, max_sentences=3)

    assert "Product Introduction to Yash" in summary
    assert "Slack notifications" in summary
    assert "Lightning round" not in summary
    assert "Where to find" not in summary
    assert "https://" not in summary
