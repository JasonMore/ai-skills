# Linked note date sections

Calendar capture and meeting summaries use the same date section in each note.
Use the event or transcript date in the user's local time, not the run date.

## Find or create a section

1. Read the current note and its Git diff before editing.
2. Find a Markdown heading whose full text is the exact `YYYY-MM-DD`.
   Allow `#YYYY-MM-DD` and `# YYYY-MM-DD`, and the same forms with `##`.
   Ignore headings inside fenced code blocks.
3. Reuse the heading when it exists. Do not add a second heading for that date.
   If duplicate date headings exist, stop for that note and report the conflict.
4. If the heading is missing, add it at the top of the note, after YAML
   frontmatter when present. Match the most recent date heading's level and
   spacing. Use `# YYYY-MM-DD` when there is no existing date convention.
5. Keep every existing note, image, link, heading, and summary unchanged.
   Do not move other dates or rewrite user text.

The section ends at the next date heading, not the next topic heading.
For a `## YYYY-MM-DD` section, `## TL;DR` and other summary headings remain
inside that date. The final date section ends at the end of the file.

## Calendar capture

Create only the missing date heading and blank space for notes.
Do not add a summary, action item, or placeholder claim.
Check every calendar link in the requested date range, including old bullets.
If an event has no note link by user choice, there is no target to update.

Example calendar link:

```markdown
- 10:35 AM: Jason / Emma (25 min) [[one-one/@emmaviolet#2026-09-30]]
```

If Emma's note has no section for that date, prepend:

```markdown
# 2026-09-30

```

Clicking the calendar link must open that heading, even before a summary exists.

## Meeting summaries

Append the summary after all existing content in the matching date section
and before the next date heading. An empty section is a valid target.
Create the date section first when no handwritten notes exist.
Keep summaries in the linked note, not only in the transcript or weekly snippet.

Persist every changed note with the calling skill's exact target file list.
