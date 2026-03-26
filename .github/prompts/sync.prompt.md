# Sync Repo to GitHub

Push the current workspace to GitHub.

## Trigger

Run this when the user says "sync" (without "notes").

## Step 1: Check for Unprocessed Notes

Before pushing, do a quick scan for any `.md` files that:
- Were recently created or modified (check `git status` for unstaged/staged changes)
- Lack a date stamp (`*Added on YYYY-MM-DD*` or `*Generated on YYYY-MM-DD*`)

If unprocessed notes are found, **tell the user** and ask if they want to process them first (via the process-notes workflow) or just push as-is.

## Step 2: Update MIRA Tasks

Check `mira-tasks.md` at the workspace root. If any tasks were completed during this session but are still marked `[ ]`, update them to `[x]` and move them to the `## Done` section. If any new human action items surfaced during this session, add them to the appropriate section.

## Step 3: Push to GitHub

Check the workspace's `copilot-instructions.md` or `.github/copilot-instructions.md` for any project-specific git credential or push instructions. If custom instructions exist, follow them exactly.

Otherwise, use the standard flow:
```
git add -A && git commit -m "<message>" && git push
```

- Use a concise, descriptive commit message based on what changed
- If there's nothing to commit, say so and skip

## Step 4: Confirm

Briefly confirm what was pushed (or that there was nothing to push).
