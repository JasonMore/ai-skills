# Evaluations

## PR event inside range

**Given:** A PR was created before the range and merged inside the range.

**Expect:** Create one merge candidate with the merge event timestamp. Do not
drop it because the PR creation date is outside the range.

## New work on an old PR

**Given:** A PR URL already exists in the log. A new commit and submitted review
occur in the range.

**Expect:** Keep the commit and review as separate event candidates. The parent
PR URL does not cause either event to deduplicate.

## Genuine review

**Given:** The user was requested for review and later submitted a changes
request with inline comments.

**Expect:** Record the submitted review. Do not record the review request.

## Bot and self-review noise

**Given:** A bot posts a review and the user comments on their own PR without a
separate review outcome.

**Expect:** Skip both as review work.

## Issue participation

**Given:** The user is assigned to an issue, investigates it, posts a detailed
root cause, and closes it.

**Expect:** Assignment alone creates no candidate. Keep the substantive comment
and close event. Correlate them when they describe one completed outcome.

## Slack decision

**Given:** The user starts a thread, compares options, and records a decision
that links to a design document.

**Expect:** Create one high-confidence candidate with the message event and
document context source. Do not copy the full thread.

## Slack low-signal messages

**Given:** The user posts acknowledgements, emoji-only replies, and repeated
link unfurls.

**Expect:** Create no candidates. Return the skipped reason counts.

## Slack recognition

**Given:** Another person mentions the user and states that the user unblocked a
deployment. The thread links to the fixed PR.

**Expect:** Create one collaboration candidate after the PR or thread verifies
the result. A mention with only praise and no work context is not enough.

## Meeting decision

**Given:** A calendar-linked note has a matching date section with a recorded
decision and owner.

**Expect:** Create one meeting candidate. Attendance without a decision or
outcome creates no candidate.

## Meaningful document

**Given:** A research document gains a comparison, decision, and follow-up.

**Expect:** Create a research candidate with commit or content-hash evidence.
Formatting-only changes and generated work-log changes create no candidate.

## Copilot correlation

**Given:** A Copilot session changes a document, creates a commit, and opens a
PR for one outcome.

**Expect:** Write one activity entry with all useful sources. Do not write one
entry per source.

## Partial collector failure

**Given:** Slack authentication fails while GitHub and Copilot collection
succeed.

**Expect:** Continue with verified GitHub and Copilot candidates. Report Slack
as unavailable and state the missing coverage.

## Search truncation

**Given:** A GitHub query reaches its result limit.

**Expect:** Split the date range, deduplicate event IDs, and report complete
coverage. If splitting still cannot give complete coverage, return `partial`.

## Rerun deduplication

**Given:** Stable event IDs and canonical source keys already exist.

**Expect:** Append nothing, leave the index unchanged, and return a no-op with
the skipped duplicate keys.

## Focus without activity

**Given:** User focus is `caching`, but no event source proves activity.

**Expect:** Append the manual focus entry only. Report that no related activity
had proof.

## Correction

**Given:** A prior entry says a PR merged. GitHub shows it closed unmerged.

**Expect:** Append a correction with a new ID. Keep the prior entry unchanged.
