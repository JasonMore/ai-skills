# Example: Summarize a Specific Meeting

Demonstrates processing a single, specific meeting transcript.

## Scenario

Jason just finished a meeting with Blake and wants to immediately summarize it.

## User Request

> "Summarize my meeting with Blake from today"

## Agent Response - Step 1: Find the Transcript

The agent searches for today's transcript in the blakewilliams subdirectory:

```bash
find "one-one/blakewilliams" -name "2026-02-11*" -type f
```

Output:
```
one-one/blakewilliams/2026-02-11 10.10.30  Blake _ Jason.md
```

## Agent Response - Step 2: Resolve

The named meeting maps to `one-one/@blakewilliams.md`. Read that note and its
Git diff, then reuse or create the meeting-date section. Ask only if several
transcripts match and the intended meeting remains unclear.

## Agent Response - Step 3: Process and Insert

The agent reads the full transcript, generates the summary, and appends it
under the matching date heading in `@blakewilliams.md`. Handwritten notes
are optional.

The output format follows:

```markdown
# 2026-02-11
[[one-one/blakewilliams/2026-02-11 10.10.30  Blake _ Jason.md]]
throw together really quick rfc docs

SDLC stuff is important
- heavy focus engineers on ground being productive
- goal: "how to rapidly iterate faster than before"

use storming, norming, forming

<!-- meeting-summary: one-one/blakewilliams/2026-02-11 10.10.30  Blake _ Jason.md -->
## TL;DR
...3 sentence summary...

## Key Discussion Points
- **Topic**: Details...

## Action Items
- [ ] Task description (Person)

## Follow-up Items
- Item to revisit later

## References
- [[one-one/blakewilliams/2026-02-11 10.10.30  Blake _ Jason|Transcript]]
- **Name**: Description or link
```

Note how the existing handwritten notes (transcript link, raw notes) are preserved above the formatted summary sections.

Persist only the changed note through `persist-work-notes`. On rerun, the
source marker prevents another summary for this target and date.
