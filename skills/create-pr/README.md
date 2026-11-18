# create-pr

Skill for opening a high-quality pull request without forcing the user to clean up after you.

The failure modes this skill exists to prevent:

1. **Overwriting the user's work.** Preserve user changes and any existing implemented branch in the selected checkout.
2. **Bouncing in review** because the PR body skipped the repo's PR template. Always read `.github/PULL_REQUEST_TEMPLATE*` and fill in every section that applies.
3. **Opening against a stale or wrong base.** Start from the requested target branch, validate before pushing, and refresh that base again before creation. If it keeps moving after one retry, report publication blocked rather than silently accepting a stale base.

Before publication, it also checks that the requested gap still exists, reuses
an agreed reviewable scope, and distinguishes evidence of the claimed behavior
from green checks. Descriptions explain the final proposal, not discarded
implementation history.

The requested release branch or agreed stack parent is carried through the
gap check, checkout, template, publication, and base readback. The repository
default is used only when no other base is specified. Publication uses the
selected checkout's actual head branch and the recorded target remote.

See `SKILL.md` for the full workflow and `references/template-formats.md` for how to read and fill any repo's PR template — and how its label markers work — without hardcoding a specific template.
## Installation

```bash
# Run from a persistent checkout of JasonMore/ai-skills.
./install
```
