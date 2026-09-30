# Meeting Notes Skill

Add transcript summaries to each meeting's dated section in its linked note.
The section and summary are created even when you took no handwritten notes.

## Install

Edit this skill in `JasonMore/ai-skills`, then run `./install` from that
repository. The installer links the source into `~/.copilot/skills/`.
Do not keep a separate copy in the user configuration directory.

## Use

- "Summarize my meetings from today"
- "Update my one-on-one notes"
- "Add a summary of my meeting with Emma"
- "Add summaries from today's transcripts to the linked meeting notes"

The skill processes the requested meetings with available sources and clear
targets. It asks only when the scope or note target is unclear.

## Source and target paths

Paths are relative to the Obsidian vault:

| Content | Path |
| --- | --- |
| One-on-one transcripts | `one-one/<person>/<date> <time> <participants>.md` |
| One-on-one notes | `one-one/@<handle>.md` |
| Group transcripts | `meetings/meeting transcripts/` |
| Group summary targets | Existing notes linked from the daily calendar |

Calendar capture first creates missing date sections. Meeting Notes fills
each matching section with a sourced summary. It can also create a missing
section when run on its own.

## Output

Each summary has `## TL;DR` with exactly 3 sentences, followed by
`## Key Discussion Points`, `## Action Items`, `## Follow-up Items`, and
`## References`. The references include the transcript.

Existing notes and images remain above the appended summary.
The next date's content stays unchanged. Repeat runs skip sources already
summarized. Missing transcripts produce an explicit report, not a guessed
summary.

Changed note files are committed and pushed through `persist-work-notes`.
See [evaluations](references/evaluations.md) for empty-section, date, and
repeat-run cases.
