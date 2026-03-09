"""Tests for generate_manifest — builds digests.json from AI-News HTML files."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from generate_manifest import build_manifest, extract_title_from_html


# ── extract_title_from_html ──


class TestExtractTitle:
    """Extract the <title> text from an HTML digest file."""

    def test_extracts_title_from_standard_digest(self, tmp_path):
        html = tmp_path / "AI-News-20260306.html"
        html.write_text(
            "<html><head><title>AI Daily Digest — March 6, 2026</title></head>"
            "<body>content</body></html>",
            encoding="utf-8",
        )
        assert extract_title_from_html(str(html)) == "AI Daily Digest — March 6, 2026"

    def test_returns_none_when_no_title(self, tmp_path):
        html = tmp_path / "AI-News-20260306.html"
        html.write_text(
            "<html><head></head><body>content</body></html>",
            encoding="utf-8",
        )
        assert extract_title_from_html(str(html)) is None

    def test_strips_whitespace(self, tmp_path):
        html = tmp_path / "AI-News-20260306.html"
        html.write_text(
            "<html><head><title>  Spaced Title  </title></head></html>",
            encoding="utf-8",
        )
        assert extract_title_from_html(str(html)) == "Spaced Title"


# ── build_manifest ──


class TestBuildManifest:
    """Build a manifest list from AI-News HTML files in a directory."""

    def _create_digest(self, directory, datestamp, title=None):
        """Helper to create a minimal HTML digest file."""
        filename = f"AI-News-{datestamp}.html"
        title_text = title or f"AI Daily Digest — {datestamp}"
        path = os.path.join(directory, filename)
        with open(path, "w") as f:
            f.write(
                f"<html><head><title>{title_text}</title></head>"
                f"<body>content</body></html>"
            )
        return path

    def test_returns_empty_list_for_empty_directory(self, tmp_path):
        result = build_manifest(str(tmp_path))
        assert result == []

    def test_discovers_single_digest(self, tmp_path):
        self._create_digest(str(tmp_path), "20260306")
        result = build_manifest(str(tmp_path))
        assert len(result) == 1
        assert result[0]["date"] == "20260306"
        assert result[0]["file"] == "AI-News-20260306.html"

    def test_sorts_newest_first(self, tmp_path):
        self._create_digest(str(tmp_path), "20260226")
        self._create_digest(str(tmp_path), "20260306")
        self._create_digest(str(tmp_path), "20260302")
        result = build_manifest(str(tmp_path))
        dates = [entry["date"] for entry in result]
        assert dates == ["20260306", "20260302", "20260226"]

    def test_includes_title_from_html(self, tmp_path):
        self._create_digest(str(tmp_path), "20260306", title="My Custom Title")
        result = build_manifest(str(tmp_path))
        assert result[0]["title"] == "My Custom Title"

    def test_ignores_non_matching_files(self, tmp_path):
        self._create_digest(str(tmp_path), "20260306")
        # Create files that should not be included
        (tmp_path / "README.md").write_text("readme")
        (tmp_path / "AI-News-20260226.txt").write_text("text version")
        (tmp_path / "AI-News-20260226_OLD.txt").write_text("old file")
        result = build_manifest(str(tmp_path))
        assert len(result) == 1

    def test_manifest_entries_have_required_keys(self, tmp_path):
        self._create_digest(str(tmp_path), "20260306")
        result = build_manifest(str(tmp_path))
        entry = result[0]
        assert "date" in entry
        assert "file" in entry
        assert "title" in entry

    def test_manifest_is_valid_json_serializable(self, tmp_path):
        self._create_digest(str(tmp_path), "20260306")
        self._create_digest(str(tmp_path), "20260302")
        result = build_manifest(str(tmp_path))
        # Should round-trip through JSON without error
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        assert deserialized == result


# ── index.html structure ──


class TestIndexHtmlStructure:
    """Verify index.html has the dynamic loading elements instead of hardcoded cards."""

    @pytest.fixture()
    def index_html(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "index.html")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_hero_cta_has_dynamic_id(self, index_html):
        """The hero CTA link should have id='latestDigestLink' for JS to update."""
        assert 'id="latestDigestLink"' in index_html

    def test_editions_grid_has_dynamic_id(self, index_html):
        """The editions container should have id='editionsGrid' for JS to populate."""
        assert 'id="editionsGrid"' in index_html

    def test_no_hardcoded_digest_cards(self, index_html):
        """There should be no hardcoded AI-News-*.html card links in the editions section."""
        # The only acceptable reference is the fallback href on the CTA
        # Count how many times a specific digest link appears as an href in doc-card anchors
        import re
        hardcoded_cards = re.findall(
            r'<a\s+class="doc-card"[^>]*href="src/AI-News-\d+\.html"', index_html
        )
        assert len(hardcoded_cards) == 0, (
            f"Found {len(hardcoded_cards)} hardcoded digest card(s) — "
            "editions should be loaded dynamically from digests.json"
        )

    def test_fetches_digests_json(self, index_html):
        """The page JS should fetch digests.json."""
        assert "digests.json" in index_html
