# Evaluations

## Calendar only

**Given:** Wednesday has handwritten notes and no calendar section. WorkIQ
returns two routed events.

**Expect:** Add only `## 🤖 Calendar` and two bullets. Keep handwritten text
byte-for-byte. Do not create or edit a work-log file. Persist only the
handwritten weekly file.

## Skip focus and lunch blocks

**Given:** WorkIQ returns events with normalized subjects `Focus time`,
`Lunch`, and `Team sync`.

**Expect:** Skip `Focus time` and `Lunch`. Add only `Team sync`.

## Rerun dedupe

**Given:** Same event source and unchanged handwritten file from the prior run.

**Expect:** Add no bullet. Create no commit. Return no-op.

## Route conflict

**Given:** One event matches two note files.

**Expect:** Write nothing. Return the event and both candidates.
