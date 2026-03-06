# Feature Specification: Fix HTML Output Stdout Noise

**Feature Branch**: `002-featurename-fix-html`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: BUG-001 from backlog.md — HTML output contains stdout noise at top of file

## Problem Statement

When running `ai-digest --html > file.html`, log messages (e.g. `INFO: AI Daily Digest - Requesting digest for 2026-03-06`, `INFO: Fetching fresh articles...`) are written to stdout along with the HTML content. This causes the generated HTML file to have non-HTML text at the top, breaking rendering in browsers.

**Root cause**: `src/config/logging.py` configures the console logging handler to write to `sys.stdout` (line 32). All `logger.info()` calls in `__main__.py` and downstream services output to stdout. When `--html` mode pipes stdout to a file, these log lines contaminate the HTML.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clean HTML file output (Priority: P1)

As a user, when I run `ai-digest --html > file.html`, I want the resulting file to contain only valid HTML with no log messages or other non-HTML text, so the file renders correctly in a browser.

**Why this priority**: This is the core bug — the HTML output feature is broken without this fix.

**Independent Test**: Run `ai-digest --html`, capture stdout, and verify the output starts with `<!DOCTYPE html>` or `<html` with no preceding text.

**Acceptance Scenarios**:

1. **Given** the tool is run with `--html`, **When** output is captured from stdout, **Then** the first non-whitespace content is valid HTML (starts with `<!DOCTYPE` or `<html`)
2. **Given** the tool is run with `--html`, **When** output is redirected to a file, **Then** the file contains zero lines of log output (no `INFO:`, `WARNING:`, `ERROR:`, `DEBUG:` prefixed lines)
3. **Given** the tool is run with `--html`, **When** the output file is opened in a browser, **Then** it renders correctly with no visible log text

---

### User Story 2 - Log messages still visible in terminal for plain text mode (Priority: P1)

As a user, when I run `ai-digest` (without `--html`), I still want to see informational log messages in the terminal so I know the tool is working.

**Why this priority**: Equally important — fixing HTML mode must not break the plain-text user experience.

**Independent Test**: Run `ai-digest` without `--html` and verify log messages still appear on console.

**Acceptance Scenarios**:

1. **Given** the tool is run without `--html`, **When** digest is generated, **Then** log messages are visible in the terminal
2. **Given** the tool is run without `--html`, **When** output is redirected to a file, **Then** log messages still appear in the terminal (via stderr)

---

### Edge Cases

- What happens when `--html` is used together with the `sources` or `podcast` subcommands? (Log routing should be consistent regardless of subcommand.)
- What happens if a third-party library writes directly to stdout? (Out of scope for this fix, but worth noting.)
- What if the user pipes plain-text mode to a file? (Log lines in stdout are tolerable for plain text, but routing logs to stderr is a better practice universally.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Console log handler MUST write to `sys.stderr` instead of `sys.stdout`
- **FR-002**: When `--html` is active, stdout MUST contain only the HTML document — no log messages, no status text
- **FR-003**: Log messages MUST still be written to the log file (`~/.ai-digest/ai-digest.log`) regardless of output mode
- **FR-004**: Plain-text mode (`ai-digest` without `--html`) MUST continue to show the digest on stdout
- **FR-005**: All existing `print(..., file=sys.stderr)` error outputs MUST remain on stderr (no regression)

### Non-Functional Requirements

- **NFR-001**: Fix MUST NOT add new dependencies
- **NFR-002**: Fix MUST be backward-compatible — no CLI interface changes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `ai-digest --html` produces output where the first non-whitespace characters are `<!DOCTYPE` or `<html` — 100% of the time
- **SC-002**: Zero lines matching `/^(INFO|DEBUG|WARNING|ERROR):/` appear in stdout when `--html` is active
- **SC-003**: Existing plain-text mode continues to produce identical digest output (no regression)
