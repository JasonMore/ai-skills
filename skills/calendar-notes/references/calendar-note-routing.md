# Calendar note routing

Resolve all event links before editing a snippet.

## Search order

1. Search prior calendar bullets for the same subject. Reuse the latest valid
   target.
2. Search existing notes under `one-one/`, `meetings/`, `projects/`,
   `side-projects/`, and other vault folders.
3. Prefer an exact case-insensitive file name match.
4. Use a normalized match only when one candidate is clear. Ignore leading
   `!`, case, punctuation, and words such as `cadence`, `weekly`, or `sync`.
5. For one-on-one subjects, use the people map from `meeting-notes`. Link the
   matching `one-one/@<handle>.md` file.

## Link rules

- Use the full vault-relative path without `.md`.
- Add `#YYYY-MM-DD` from the event date.
- Keep the calendar subject as visible text.
- Treat `/` in a subject as text, not a folder.
- Confirm the target file exists.
- Never create a new note file as a routing side effect. Add missing date
  sections inside resolved existing notes using [date sections](date-sections.md).
- If zero or many candidates remain, ask the user to choose. Write nothing
  until every event has one target.

## Examples

| Event subject | Link target |
| --- | --- |
| `PR future experience cadence` | `[[projects/pr-overview/! PR future experience#2026-08-04]]` |
| `Cody / Jason` | `[[one-one/@cbodfield#2026-08-05]]` |
| `Jason / Francisco` | `[[one-one/@cuquo#2026-08-03]]` |
| `Weekly Jason <> Katie` | `[[one-one/@inkblotty Katie McCormick#2026-08-03]]` |
| `Jason / Emma` | `[[one-one/@emmaviolet#2026-09-30]]` |

The Emma link requires a heading whose text is `2026-09-30` in
`one-one/@emmaviolet.md`. A file that exists without this heading is not a
complete calendar target.
