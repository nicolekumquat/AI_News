"""Generate digests.json manifest from AI-News-*.html files in the src directory."""

import glob
import json
import os
import re
import sys


def extract_title_from_html(filepath):
    """Extract the <title> text from an HTML file. Returns None if not found."""
    with open(filepath, encoding="utf-8", errors="replace") as f:
        # Read only the first 4 KB — title is always in <head>
        head = f.read(4096)
    match = re.search(r"<title>(.*?)</title>", head, re.IGNORECASE | re.DOTALL)
    if match:
        title = match.group(1).strip()
        return title if title else None
    return None


def build_manifest(src_dir):
    """Scan *src_dir* for AI-News-YYYYMMDD.html files and return a manifest list.

    Each entry is a dict with keys: date, file, title.
    The list is sorted newest-first by date.
    """
    pattern = os.path.join(src_dir, "AI-News-*.html")
    entries = []
    for filepath in glob.glob(pattern):
        basename = os.path.basename(filepath)
        m = re.match(r"AI-News-(\d{8})\.html$", basename)
        if not m:
            continue
        datestamp = m.group(1)
        title = extract_title_from_html(filepath)
        entries.append({
            "date": datestamp,
            "file": basename,
            "title": title,
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def main():
    """CLI entry point: write digests.json into the src directory."""
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        src_dir = sys.argv[1]
    manifest = build_manifest(src_dir)
    out_path = os.path.join(src_dir, "digests.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {len(manifest)} entries to {out_path}")


if __name__ == "__main__":
    main()
