---
name: calendar-notes
description: >
  Captures calendar events in handwritten weekly snippets and links each event
  to an existing vault note. Use when the user asks to update calendar notes,
  add meetings to snippets, refresh a daily calendar, capture today's
  meetings, or run calendar capture from update-daily-snippet.
---

# Calendar Notes

Add calendar events to handwritten weekly snippets. Preserve all user text.
Never write work activity.

## Inputs

- Date or date range. Default to today in the user's local time.
- Vault root. Default to `/Users/jasonmore/code/work_notes`.

Weekly files use `snippets/YYYY MM mon DD - mon DD.md`.

## Process

1. Find each target weekly file.
2. Read each target and its Git diff before editing.
3. Invoke `workiq` and fetch calendar events for the full date range.
4. Skip canceled events, all-day blocks, blank busy holds, declined events,
   and events whose normalized subject is exactly `Focus time` or `Lunch`.
5. Resolve every event before any edit. Follow
   [calendar note routing](references/calendar-note-routing.md).
6. Merge missing events into each matching day.
7. Invoke `persist-work-notes` once with the exact changed handwritten files
   and a short action summary.

If routing fails, write nothing. Return the event and candidate paths.

## Merge rules

- Keep existing day heading case and all user content.
- Use or add one `## 🤖 Calendar` section under the matching day.
- Add one bullet per event:

```markdown
- 10:30 AM: Weekly Jason <> Katie (30 min) [[one-one/@inkblotty Katie McCormick#2026-08-17]]
```

- Keep existing calendar bullets in place.
- Add only missing bullets. Do not sort or rewrite existing bullets.
- Deduplicate by provider event ID when stored. Otherwise use normalized event
  date, start time, and subject.
- Treat case and repeated spaces as equal during fallback dedupe.
- If one identity maps to conflicting text or links, report the conflict. Do
  not replace either version.
- If a day heading is missing, append it without moving other sections.

## Persistence

Pass only files changed by this run. Include prior edits already present in
those files. Skip persistence on a no-op.

See [evaluations](references/evaluations.md).
