# Backlog

## BUG-001: HTML output contains stdout noise at top of file

**Type:** Bug  
**Priority:** High  
**Status:** Done  

When generating the HTML digest (e.g. `ai-digest --html > file.html`), extraneous stdout output (logging or print statements) appears at the top of the HTML file before the actual HTML content. This pollutes the generated file and can break rendering. All non-HTML output should go to stderr, or be suppressed when `--html` is active.

---

## FEAT-001: Sort articles by age (newest first)

**Type:** Enhancement  
**Priority:** Medium  
**Status:** Done  

Articles in the generated digest should be sorted by publication date in descending order, with the most recent articles appearing first. Currently the ordering does not consistently prioritize recency.

---

## FEAT-002: Web UI for digest management

**Type:** Feature  
**Priority:** Medium  
**Status:** Open  

A local web application that provides:

1. **Digest generation** — A button to regenerate the latest AI news digest on demand.
2. **Blog summary expansion** — If an article is a blog post, display a button to generate a detailed summary of that blog. Once generated, the summary appears inline under the article in an expandable accordion.
3. **Source management** — A UI to review, add, remove, enable, and disable URL data sources (equivalent to the `ai-digest sources` CLI commands).

The web application should be hosted on github (like this example is hosted:   
    https://ubiquitous-carnival-4qpr9nm.pages.github.io/ )
