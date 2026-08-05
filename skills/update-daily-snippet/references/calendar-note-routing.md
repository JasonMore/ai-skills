# Calendar note routing

Resolve all calendar links before editing the snippet file.

## Search order

1. Search prior snippets for the same event subject. Reuse its latest valid note target.
2. Search existing notes under `one-one/`, `meetings/`, `projects/`, `side-projects/`, and other vault folders.
3. Prefer an exact case-insensitive file-name match.
4. Accept a normalized match only when one candidate is clear. Ignore the leading `!`, case, punctuation, and scheduling words such as `cadence`, `weekly`, or `sync`.
5. For one-on-one subjects, use the people mapping from the `meeting-notes` skill and link the matching `one-one/@<handle>.md` file.

## Required behavior

- Use the full vault-relative path without `.md`.
- Add `#<YYYY-MM-DD>` from the calendar event date.
- Keep the event subject as visible text in the calendar bullet.
- Treat `/` in an event subject as text. Never use it as a folder separator.
- Confirm the target file exists before writing.
- If no candidate or more than one candidate remains, use `ask_user`.
- Resolve every event first. Do not write any snippet content until all events have targets.
- Never create a new meeting note as a side effect of a calendar link.

## Examples

| Event subject | Link target |
| --- | --- |
| `PR future experience cadence` | `[[projects/pr-overview/! PR future experience#2026-08-04]]` |
| `Cody / Jason` | `[[one-one/@cbodfield#2026-08-05]]` |
| `Jason / Francisco` | `[[one-one/@cuquo#2026-08-03]]` |
| `Weekly Jason <> Katie` | `[[one-one/@inkblotty Katie McCormick#2026-08-03]]` |
