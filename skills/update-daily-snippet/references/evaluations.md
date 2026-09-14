# Evaluations

## Orchestrator order

**Given:** Calendar, todo refresh, and work-log all have work.

**Expect:** `calendar-notes` finishes first. Todo refresh runs second.
`work-log` runs last. Results appear in that order.

## Persistence per phase

**Given:** Calendar changes one handwritten file, todo refresh adds missing
follow-ups to the current handwritten file, and work log changes its weekly file
and index.

**Expect:** Calendar creates one commit. Todo refresh creates one commit for
the current handwritten file. Work log creates one later commit. No phase stages
unrelated paths.

## Prior-week todos

**Given:** The prior handwritten file has open items in `# todo`, and the
current file does not mark them done or obsolete.

**Expect:** Todo refresh adds the still-open, non-trivial items to
`## 🤖 Todos` under the target day. It skips blank items and duplicate tasks.
It copies each todo exactly and keeps the source order and group labels. It
does not fix spelling, change case, rewrite text, add owners, or regroup items.

## Exact todo copy

**Given:** A source todo contains custom spelling, capitalization, indentation,
a URL, and owner text.

**Expect:** The copied todo matches the source text exactly. The refresh does
not normalize or improve the text.

## Meeting todos

**Given:** Calendar bullets link to meeting notes with matching date anchors,
and those sections contain open action items.

**Expect:** Todo refresh reads only those date sections and adds missing open
items with owners. It skips old todos from other date sections.

## Child failure

**Given:** Calendar cannot route one event.

**Expect:** Calendar writes nothing and reports the event. Todo refresh and
work-log do not run. Orchestrator returns the routing error.

## Work-log failure

**Given:** Calendar and todo refresh commit and push, then work-log fails.

**Expect:** Return calendar success, todo success, and work-log error as
partial success. Do not roll back earlier commits.
