# Evaluations

## No handwritten notes

**Given:** Emma's September 30 transcript exists. Her note has older dates
but no September 30 section.

**Expect:** Create the date section using the note's heading style. Add all
five summary sections, a source marker, and the transcript reference there.
Preserve all older notes. Persist only the changed note.

## Calendar-created empty section

**Given:** Calendar capture added `# 2026-09-30` to Emma's note.
No handwritten notes follow it.

**Expect:** Reuse the section and append the sourced summary. Do not ask the
user to write notes first or add another date heading.

## Preserve notes and section boundaries

**Given:** The target uses `## 2026-09-30`, followed by notes, an image, and
topic headings. The next date is `## 2026-09-29`.

**Expect:** Append after all September 30 content and before September 29.
Do not treat a topic or summary heading as the next date. Keep user content
byte-for-byte.

## All requested linked notes

**Given:** Today's calendar links to Emma's note and a project meeting note.
Both meetings have transcripts.

**Expect:** Add a summary to each note's date section. Do not summarize only
the one-on-one or leave the group summary only in its transcript.
Persist both changed notes in one call.

## Repeat run

**Given:** The same transcript was summarized in its target date section.

**Expect:** Skip summary insertion for that target-date-source tuple.
Still collect its open tasks. Return no-op only when summaries and todos both
need no changes.

## Two meetings on one date

**Given:** Two distinct meeting sources target the same note on September 30.

**Expect:** Keep one date heading. Append a summary for each source. A rerun
skips each source separately.

## Backfill uses the meeting date

**Given:** The skill runs on October 1 for a September 30 transcript.

**Expect:** Add the summary under September 30, not October 1.

## Missing source

**Given:** A calendar link has an empty date section but no transcript.

**Expect:** Report the missing source. Do not infer decisions from the event
title, old summaries, or the empty section. Continue with other sourced
meetings and report partial success.

## Existing summary with missing todos

**Given:** A sourced September 29 summary already exists. Its Jason-owned
action item is missing from Tuesday's todo list.

**Expect:** Keep the summary unchanged. Add the exact task under Tuesday's
`## 🤖 Todos`, even when the run date is September 30. Persist only the snippet.

## Owners, open tasks, and follow-ups

**Given:** A date section has Jason-owned, shared, unowned, other-owned, and
completed checkboxes. It also has a plain Jason-assigned task and an unresolved
question under Follow-up Items.

**Expect:** Copy the open Jason-owned, shared, and unowned tasks unchanged.
Add checkbox syntax to the explicit plain Jason task. Skip the other owner,
completed checkbox, and unresolved question. Do not guess ownership from
generated speaker labels.

## Weekly duplicates and exact text

**Given:** Wednesday's meeting repeats a task already listed on Tuesday.
Another task has a completed copy in the weekly snippet. Two different tasks
refer to the same URL.

**Expect:** Add neither repeated task. Preserve the existing open and completed
copies and their positions. Keep both distinct tasks that share a URL.
Preserve spelling, links, owners, order, and source group labels.

## Dry run

**Given:** The user requests a dry run for September 28-30. Linked sections
contain new tasks, old dates, and code blocks with sample checkboxes.

**Expect:** Preview only eligible tasks in the requested date sections.
Show exact text, dates, and source links. Ignore code and older dates.
Keep every vault file and the vault Git index unchanged. Do not call
`persist-work-notes`, commit, push, or create missing sections.

## Missing destination

**Given:** Tasks exist, but the handwritten weekly snippet cannot be identified.

**Expect:** Report the destination error and ask for the correct file.
Do not write a guessed file or put tasks in a work-log note.

## Completion in another source

**Given:** Monday has an unchecked task to demo a prototype to David.
Tuesday's transcript records that demo. A RUM task has two parts, and the
work log confirms only its sampling change is done.

**Expect:** Skip the completed demo. Keep the partially finished RUM task
unchanged and explain which part remains open. Do not edit either source.
