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


def update_index_cta(repo_root, latest_file):
    """Update the hardcoded fallback href in index.html to point to the latest digest."""
    index_path = os.path.join(repo_root, "index.html")
    if not os.path.exists(index_path):
        return
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
    updated = re.sub(
        r'(id="latestDigestLink"\s+href=")src/AI-News-[^"]+(")',
        rf'\1src/{latest_file}\2',
        html,
    )
    if updated != html:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"Updated index.html CTA → {latest_file}")


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

    # Keep the hardcoded fallback in index.html up to date
    if manifest:
        repo_root = os.path.dirname(src_dir)
        update_index_cta(repo_root, manifest[0]["file"])


if __name__ == "__main__":
    main()
