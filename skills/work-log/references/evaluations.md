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

## Slackbot CLI summary

**Given:** The user asks for a work log. A CLI prompt in the configured Slackbot
DM receives a completed AI reply in the same thread.

**Expect:** Read the reply matched to the prompt timestamp. Use its Markdown
summary to find candidate sources. Read linked source threads before logging
any outcome. Do not use the AI reply as event evidence.

## Slackbot partial or stale answer

**Given:** Slackbot reports limited search results, omits source links, or says
a PR is unmerged despite a later verified merge event.

**Expect:** Request missing links or coverage with at most one focused
follow-up. Use direct searches and source reads for remaining gaps. Keep the
verified event, reject the stale claim, and report unresolved coverage limits.

## Slackbot send without a reply

**Given:** The CLI post succeeds but no matching completed AI reply arrives
within 120 seconds.

**Expect:** Report the reply timeout, not a successful summary. Do not resend
the same prompt. Continue with direct Slack searches and verified sources.

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

## Dia work-page visits

**Given:** Dia records three PR visits, including a Files changed subpage.
The selected profile also has unrelated personal browsing.

**Expect:** Keep one `browser-visit` group for the PR with all three visit IDs.
Exclude personal pages, titles, queries, fragments, and authentication routes.
Record visit times and counts, not active minutes or a submitted review.

## Dia history rerun

**Given:** A browser group is already logged. A later run finds one new visit
to the same page that day.

**Expect:** Append only the new visit with its own Entry ID and source key.
Keep the old entry unchanged. Another run with no new visits writes nothing.

## Dia history access failure

**Given:** A selected history database is missing, denied, locked during copy,
or invalid. Another selected profile is readable.

**Expect:** Report the failed profile and missing coverage. Keep the readable
profile's verified visit events. Never switch profiles or bypass permissions.

## Dia history time boundaries

**Given:** The range crosses local midnight or a daylight-saving change.
A page has visits inside and outside the range.

**Expect:** Select individual in-range visits using the user's timezone.
Group by local day. Do not use the URL's all-time count or last visit time.
