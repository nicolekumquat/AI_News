# Copilot Instructions for AI_News

## Git Push — Dual GitHub Account Setup

This repo (`nicolekumquat/AI_News`) requires pushing as the `nicolekumquat` account.
The developer's default/work account is `nical_microsoft`, which does NOT have push access.

**To push from this repo:**
1. `gh auth switch --user nicolekumquat`
2. `git push`
3. `gh auth switch --user nical_microsoft` (restore work account)

The local git config uses `gh auth git-credential` as the credential helper,
so pushes route through whichever `gh` account is currently active.

## MIRA Task File — `mira-tasks.md`

The file `mira-tasks.md` at the workspace root is the **human operator's personal task list**.
MIRA (Mission Intelligence & Resource Ally) scans this file and syncs tasks into a cross-project dashboard.

**This is NOT the same as SpecKit's `specs/*/tasks.md`.**
- `mira-tasks.md` = things the **human** needs to do (decisions, reviews, follow-ups, manual steps)
- `specs/*/tasks.md` = **AI-executable** implementation tasks (code, tests, refactors)

### Rules for maintaining `mira-tasks.md`

1. **Add tasks** when the user commits to something, is assigned work, or a conversation surfaces a human action item.
2. **Mark done** with `[x]` when completed. Move the line to the `## Done` section.
3. **Never remove** a task without the user's explicit approval — mark done instead.
4. **Keep titles concise and action-oriented** — start with a verb (e.g., "Review PR", "Decide on…", "Update config").
5. **Priority**: Prefix with `P1`, `P2`, or `P3` when the user indicates urgency (e.g., `- [ ] P1 - Fix broken deploy`).
6. **Inline tags**: Use `@due:YYYY-MM-DD`, `@estimate:MIN`, `@start:YYYY-MM-DD`, `@bucket:work` as appropriate.
7. **Headings** (`## Backlog`, `## In Progress`, `## Done`) act as categories — place tasks under the right heading.
8. Tasks must be **top-level checkboxes** (no leading whitespace) to be scanned by MIRA.
