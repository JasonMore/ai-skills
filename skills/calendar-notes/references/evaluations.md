# Evaluations

## Calendar only

**Given:** Wednesday has handwritten notes and no calendar section. WorkIQ
returns two routed events.

**Expect:** Add `## 🤖 Calendar` and two bullets. Create missing event-date
sections in their linked notes. Keep handwritten text byte-for-byte.
Do not create or edit a work-log file. Persist only the changed weekly file
and linked notes.

## Skip focus and lunch blocks

**Given:** WorkIQ returns events with normalized subjects `Focus time`,
`Lunch`, and `Team sync`.

**Expect:** Skip `Focus time` and `Lunch`. Add only `Team sync`.

## Rerun dedupe

**Given:** Same event source, unchanged handwritten file, and every linked
date section already exists.

**Expect:** Add no bullet. Create no commit. Return no-op.

## Route conflict

**Given:** One event matches two note files.

**Expect:** Write nothing. Return the event and both candidates.

## Missing date anchor on an existing bullet

**Given:** Wednesday already links to `one-one/@emmaviolet#2026-09-30`,
but Emma's note has no heading for that date.

**Expect:** Add the date heading in Emma's note without adding a calendar
bullet. Preserve all old notes. Persist only Emma's note. Return a change,
not no-op. A second run changes nothing.

## Existing empty date section

**Given:** The linked note already contains `## 2026-09-30` with no notes.

**Expect:** Reuse that section. Do not create a second heading or claim that
the meeting has a summary.

## Date range and frontmatter

**Given:** Two events link to the same note on different dates. The note has
YAML frontmatter and uses `#YYYY-MM-DD` headings.

**Expect:** Ensure both date sections exist below frontmatter. Match the
heading style, preserve existing content, and persist the note once.
