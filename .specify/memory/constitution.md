<!--
  Sync Impact Report
  ==================================================
  Version change: 1.0.0 → 1.1.0 (MINOR: expanded content standards)
  Modified principles: N/A
  Modified sections:
    - Content & Data Standards: added 15-article cap, insight-driven
      curation mandate, complete-thought summary requirement
  Added sections: N/A
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no changes needed
    - .specify/templates/spec-template.md ✅ no changes needed
    - .specify/templates/tasks-template.md ✅ no changes needed
  Follow-up TODOs: None
  ==================================================
-->

# AI Daily Digest Constitution

## Core Principles

### I. Content-First

Every feature MUST serve the goal of delivering concise, accurate
AI news summaries to the user. Features that do not directly
support content aggregation, summarization, or delivery are
out of scope until all content-serving capabilities are complete.

- New features MUST justify how they improve content quality,
  freshness, or accessibility.
- No feature bloat: if a capability does not help the user
  consume AI news more effectively, it MUST NOT be built.
- User-facing output MUST be brief, scannable, and actionable.

### II. Test-First (NON-NEGOTIABLE)

All production code MUST be written using Test-Driven Development.

- Tests MUST be written before implementation code.
- Tests MUST fail (red) before any implementation is written.
- Implementation MUST make failing tests pass (green) with the
  simplest possible code.
- Refactoring MUST only occur after tests are green.
- No pull request or merge is permitted without corresponding
  passing tests for all new behavior.

### III. Simplicity

Start simple. Do not build what is not yet needed.

- YAGNI (You Aren't Gonna Need It) MUST be the default stance
  for all design decisions.
- Premature optimization is prohibited; optimize only when
  profiling data justifies it.
- Prefer standard library solutions over third-party packages
  when both are viable.
- Every added dependency MUST be justified in the PR description.
- Complexity MUST be explicitly justified and documented when
  unavoidable.

## Technology Stack & Constraints

- **Language**: Python 3.11+
- **Deployment**: Local execution only (no cloud deployment required)
- **Package management**: pip with a `requirements.txt` or
  `pyproject.toml` for dependency pinning
- **Testing**: pytest as the sole test runner
- **Linting/Formatting**: ruff for linting and formatting
- **Virtual environments**: All development MUST occur inside a
  Python virtual environment (`venv`)
- Third-party packages MUST be pinned to specific versions

## Content & Data Standards

- The daily digest MUST contain at most 15 articles, curated
  for depth and insight over volume.
- Articles MUST be ranked by practical relevance: prefer
  content about applying AI to real work (building software,
  workflow transformation, adoption lessons) and major
  industry trends (model releases, paradigm shifts, policy
  changes) over narrow academic feature-level research.
- Every news item MUST include source attribution (publication
  name and URL at minimum).
- Duplicate content MUST be detected and deduplicated before
  being presented to the user.
- Content freshness: items older than 48 hours SHOULD be
  deprioritized or excluded from the daily digest.
- Summaries MUST capture at least one key insight or
  takeaway as a complete thought — truncated text fragments
  are prohibited. Raw article text MUST NOT be presented
  verbatim without transformation.
- Data fetched from external sources MUST be cached locally
  to avoid redundant network calls within the same run.

## Governance

This constitution is the highest-authority document for the
AI Daily Digest project. All code, reviews, and design decisions
MUST comply with its principles.

- **Amendments** require: (1) a written proposal describing the
  change, (2) rationale for why existing principles are
  insufficient, and (3) an updated constitution version.
- **Versioning** follows semantic versioning:
  - MAJOR: Principle removal or incompatible redefinition.
  - MINOR: New principle or materially expanded guidance.
  - PATCH: Wording clarifications, typo fixes, non-semantic edits.
- **Compliance review**: Every PR MUST be checked against these
  principles before merge. Reviewers MUST cite the specific
  principle when requesting changes for constitution compliance.
- **Complexity justification**: Any deviation from the Simplicity
  principle MUST be documented in the PR with a clear rationale.

**Version**: 1.2.0 | **Ratified**: 2026-02-23 | **Last Amended**: 2026-02-26
