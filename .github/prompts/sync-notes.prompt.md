# Process Notes

Review new or updated notes in the workspace, add date stamps, and flag any action items.

## Trigger

Run this when the user says "process notes" or "sync notes", mentions they added a note, or points to a specific file they just created or edited.

## Step 1: Identify Changed Notes

- If the user specifies a file or folder, use that.
- Otherwise, check `git status` for new/modified `.md` files and process those.
- If nothing is obvious, ask which file or folder to process.

## Step 2: Review the Note

Read the note content. Look for:
- **Actions taken** - emails sent, meetings scheduled, calls made, follow-ups completed
- **Status changes** - completed, blocked, closed, moved to next stage
- **New information** - contacts, dates, scheduling details
- **Next steps** - what the user plans to do next, deadlines, follow-up dates

If the note is too vague to determine what happened, **stop and ask** before making changes.

## Step 3: Add Date to the Note

Every note should have a date stamp. Check for one and add it if missing:
- Add `*Added on YYYY-MM-DD*` on the line immediately after the `#` heading
- If the note has no heading, add one based on the content, then add the date line
- If the note already has a date (`*Added on*` or `*Generated on*`), leave it as-is
- Use today's date unless the note content clearly indicates it was written on a different date

## Step 4: Update MIRA Tasks

If the note contains **next steps, action items, follow-ups, or decisions the user needs to make**, add them as new tasks in `mira-tasks.md` under the appropriate heading (`## Backlog` or `## In Progress`). Use MIRA conventions: concise verb-first titles, `P1/P2/P3` prefix if urgency was mentioned, inline tags (`@due:`, `@estimate:`) as appropriate.

If any existing tasks in `mira-tasks.md` were completed by what the note describes, mark them `[x]` and move to `## Done`.

## Step 5: Update Trackers (if applicable)

If the workspace has a tracker file (e.g., a markdown table tracking status of items), update the relevant row based on what the note contains. If no tracker exists, skip this step.

## Step 6: Update Dashboard (if applicable)

If the workspace has a dashboard file (e.g., an HTML dashboard), regenerate it to reflect the current state of the tracker. The dashboard should be driven by the tracker as the single source of truth. If no dashboard exists, skip this step.

## Step 7: Confirm Changes

After updating, briefly summarize:
- What date was added to the note
- What changed in any tracker (show before/after for updated rows)
- What changed in any dashboard
