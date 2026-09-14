---
name: update-daily-snippet
description: >
  Runs calendar capture, daily todo refresh, then work logging. Use when the
  user asks to "update my snippets", "add to my weekly summary", "update daily
  snippet", "what did I work on", "summarize my sessions", "add today's work
  to snippets", or wants one daily workflow for calendar notes, todos, and
  verified work activity.
---

# Update Daily Snippet

Run calendar capture, refresh daily todos, then run work logging.

## Inputs

- Date or date range. Default to today in the user's local time.
- User focus, if supplied. Pass it to `work-log` as hints.

## Process

1. Invoke `calendar-notes` for the date range.
2. Wait for its result. Record changed files, commit SHA, no-op, or error.
3. If calendar routing or persistence failed, stop and return its error.
4. Refresh the daily todo section in the current handwritten weekly snippet.
5. Invoke `work-log` for the same date range and focus.
6. Wait for its result.
7. Return calendar, todo, and work-log results in order.

Run `work-log` after calendar success or no-op. Calendar must finish first.
Report partial success when work-log fails after calendar changed content.

## Daily todo refresh

Use this phase for open follow-ups only. Do not summarize ships here.

Read:

1. Current handwritten file: `snippets/<current-week>.md`
2. Prior handwritten file: `snippets/<prior-week>.md`
3. Meeting notes linked from calendar bullets in the date range

For linked one-on-one or recurring meeting notes, read only the matching
`#YYYY-MM-DD` section when it exists. Skip the note if the date section is
missing. Do not pull old todos from other sections.

Collect:

- Open checkbox todos from the current day or date range.
- Open action items and follow-up items from linked meeting note sections.
- Still-open, non-trivial todos from the prior handwritten file's `# todo`
  section when the current file does not mark them complete.

For each copied todo:

- Copy the source text exactly. Keep its case, spelling, punctuation, links,
  owner text, indentation, and checkbox syntax.
- Keep todos in their source order.
- Keep source group labels that contain copied todos.
- Do not rewrite, shorten, expand, fix, or add owner text.
- Do not regroup todos by topic or create new group labels.

Skip:

- Completed checkboxes.
- Trivial placeholders, blank tasks, and stale historical items.
- Items that current notes show as done, replaced, or no longer useful.

Deduplicate by normalized task text, target URL, and owner. When duplicates
exist, copy the newest source item exactly.

Write one section under each matching day:

```markdown
## 🤖 Todos
- [ ] Task (Owner)
```

Keep existing todo bullets. Add only missing bullets. Do not sort or rewrite
user text. Preserve the copied order and group labels. If a day heading is
missing, append it without moving other content.

## Persistence

`calendar-notes` and `work-log` each invoke `persist-work-notes` with their
exact changed files. The todo phase invokes `persist-work-notes` once with the
current handwritten weekly snippet when it changed.

Skip todo persistence on a no-op.

## Boundaries

- Keep calendar events in handwritten weekly snippets.
- Keep open follow-ups in handwritten weekly snippets.
- Keep generated activity in `snippets/work-log/`.
- Never copy work-log prose into a handwritten day section.
- Never hide a calendar, todo, or work-log error.

See [evaluations](references/evaluations.md).
