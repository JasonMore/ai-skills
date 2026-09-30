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

**Expect:** Skip that target-date-source tuple. Write nothing and return
no-op if all requested sources were already summarized.

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
