---
name: meeting-notes
description: >
  Finds meeting transcripts and adds summaries to dated sections in linked
  vault notes, even when no handwritten notes exist. Use when the user asks
  to "summarize my meeting", "update my one-on-one notes", "process today's
  meeting transcript", "format meeting notes", "add meeting summary",
  "update 1:1 notes", or "summarize transcript".
---

# Meeting Notes

Add sourced meeting summaries to dated sections in linked vault notes.
Handwritten notes are optional. Preserve all existing content.

## Inputs

- Date or range. Default to today in the user's local time.
- Selected meetings or transcripts, when supplied.
- Vault root. Default to the current Obsidian vault.

Use the meeting's local date, not the date when the skill runs.

## Find sources and targets

1. Read calendar links in the handwritten weekly snippet for the date range.
   Find local transcripts in `one-one/<person>/` and
   `meetings/meeting transcripts/`. Match the meeting date and participants.
2. If the user supplies a transcript from a meeting provider, read that source
   too. Report unavailable transcript content instead of guessing it.
3. Match each meeting to its existing linked note. One-on-one transcripts use
   the [people map](references/file-structure.md), not a guessed directory name.
   Recurring or group meetings can target notes in `meetings/` or `projects/`.
4. Resolve uncertain targets using
   [calendar note routing](../calendar-notes/references/calendar-note-routing.md).
   Do not create a new note file without user approval.
5. Process every meeting in the requested scope that has a source and a
   resolved target. A request for today's meetings covers all matching meetings;
   a named meeting covers only that meeting. Ask only when scope or routing
   remains unclear.

Read each full transcript before writing its summary. Calendar entries alone
do not prove discussion content. Report missing or incomplete sources per
meeting. Do not invent a summary to fill an empty date section.

## Summary format

Use these five sections, always with `##` headings:

| Section | Rule |
| --- | --- |
| `## TL;DR` | Exactly 3 sentences with specific takeaways. |
| `## Key Discussion Points` | Bold topic names, details, decisions, and reasons. |
| `## Action Items` | `- [ ] Task (Owner)` for agreed actions. |
| `## Follow-up Items` | Open questions and topics to revisit. |
| `## References` | Transcript link and any resources mentioned. |

Use GitHub-flavored Markdown and concise technical English.
Do not use em dashes or en dashes. Attribute decisions to the correct person.
Do not infer an owner or agreement that the source does not support.

## Insert into each linked note

1. Read the target note and its current Git diff.
2. Ensure the matching meeting-date section exists. Follow the shared
   [date section rules](../calendar-notes/references/date-sections.md).
   Reuse a calendar-created section. Create it when no notes were taken.
3. Append the summary after all existing content in that date section and
   before the next date heading. Topic and summary headings do not end a date
   section, even when the date itself uses `##`.
4. Add the source to `## References` and a stable source marker immediately
   before the summary: `<!-- meeting-summary: SOURCE_ID -->`.
   Replace `SOURCE_ID` with the provider meeting ID or vault-relative transcript
   path. Reuse that identity on later runs.
5. Check each target and date for that source before appending. If its summary
   already exists, skip it. An older summary with the same transcript reference
   also counts. Never overwrite handwritten notes or an earlier summary.

Different meetings on one date may each have a sourced summary.
If one source maps to several requested targets, check each target on its own.
Do not leave the only summary in the transcript, snippet, or work log.

## Persistence and result

Invoke `persist-work-notes` once with the exact changed note files and a short
summary. Include existing user edits in those files. Do not stage unrelated
notes or unchanged transcripts. Skip persistence on a no-op.

Return changed note paths and dates, skipped duplicate sources, missing-source
or routing errors, commit SHA, and push result. Report partial success when
some meetings could not be summarized.

See [evaluations](references/evaluations.md) and
[examples](examples/process-todays-meetings.md).
