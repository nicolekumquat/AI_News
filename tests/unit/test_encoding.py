"""Tests for encoding correctness — ensure Unicode content survives the pipeline.

Root cause: PowerShell decodes stdout from external processes using
[Console]::OutputEncoding (OEM CP437 on US-English Windows).  When
Python writes UTF-8 bytes and they're redirected with ">", PowerShell
decodes via CP437 — turning U+201C (") into ΓÇ£.

Fix: the CLI's --output flag writes directly to a file, bypassing shell
encoding entirely.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Allow imports from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Common mojibake patterns: UTF-8 bytes decoded as CP437/CP1252
MOJIBAKE_PATTERNS = [
    "\u0393\u00c7\u00a3",  # ΓÇ£ = " (left smart quote)
    "\u0393\u00c7\u00a5",  # ΓÇ¥ = " (right smart quote)
    "\u0393\u00c7\u00d6",  # ΓÇÖ = ' (right smart apostrophe)
    "\u0393\u00c7\u00f4",  # ΓÇô = – (en dash)
    "\u0393\u00c7\u00f6",  # ΓÇö = — (em dash)
    "\u2261\u0192",        # ≡ƒ prefix on mangled emojis
]

MOJIBAKE_RE = re.compile(
    r"[\u0393][\u00c0-\u00ff][\u00a0-\u00ff]"
    r"|\u2261\u0192"
)

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src"


class TestOutputFileEncoding:
    """Verify --output writes valid UTF-8 free of shell-encoding mojibake."""

    def test_output_file_contains_no_mojibake(self):
        """Generate HTML via --output and check for CP437 corruption."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            out_path = tmp.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "cli", "--html", "--output", out_path],
                cwd=str(SRC_DIR),
                capture_output=True,
                timeout=120,
            )
            assert result.returncode == 0, (
                f"CLI exited {result.returncode}: {result.stderr.decode('utf-8', errors='replace')}"
            )
            html = Path(out_path).read_text(encoding="utf-8")
            assert len(html) > 100, "Output file is too short"

            hits = MOJIBAKE_RE.findall(html)
            assert not hits, f"Mojibake found in --output file: {hits[:5]}"
        finally:
            os.unlink(out_path)
