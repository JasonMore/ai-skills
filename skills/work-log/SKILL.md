---
name: work-log
description: >
  Builds a sourced, append-only weekly work log from verified GitHub, Slack,
  meeting, document, Copilot, and user-focus activity. Use when the user asks
  to log work, capture daily activity, summarize sessions, record focused work,
  update the work log, or run work capture from update-daily-snippet.
---

# Work Log

Record verified activity in `snippets/work-log/`. Keep generated prose out of
handwritten daily sections.

Read these files before collection:

- [schema](references/schema.md)
- [source policy](references/source-policy.md)
- [examples](references/examples.md)

## Inputs

- Date or date range. Default to today in the user's local time.
- User focus. Store it as a manual entry, then use it to rank candidates.
- Vault root. Default to `/Users/jasonmore/code/work_notes`.
- GitHub owner. Default to `github`.

## Prepare

1. Resolve the date range with an exclusive end date for search APIs.
2. Resolve the authenticated GitHub and Slack users.
3. Read `snippets/work-log/index.md` and each indexed weekly log needed for
   global source-key deduplication.
4. Initialize one status record per collector. A failed collector must return
   an explicit error.

## Gather

Run independent collectors in parallel when tools permit:

1. Query local and cloud Copilot sessions, checkpoints, changed files, and
   GitHub references for the range.
2. Run `gh agent-task list -L 50` and keep completed or materially changed
   tasks in the range.
3. Run `scripts/github_activity.py` for meaningful PR, review, issue, commit,
   and discussion events.
4. Use Slack MCP to find high-signal authored threads, replies, linked work,
   decisions, action items, mentions, and recognition. Fall back to `gh-slack`
   only when MCP is unavailable or fails.
5. Read calendar-linked meeting note sections for matching dates.
6. Inspect meaningful changed documents. Exclude generated logs, application
   state, formatting-only changes, and unrelated vault churn.

Use [source policy](references/source-policy.md) for queries and filters.

## Select

1. Convert every result to the candidate schema.
2. Verify the event timestamp, actor role, source ID, and factual outcome.
3. Reject focus, assignments, review requests, mentions, reactions, and raw
   item counts as proof by themselves.
4. Reject acknowledgements, bot-only activity, brief lookups, empty
   exploration, secrets, and claims with no durable outcome.
5. Correlate sources that prove the same outcome. Prefer one strong entry with
   several sources over repeated entries.
6. Keep separate events for distinct commits, reviews, decisions, incidents,
   or deliverables on the same PR, issue, or thread.
7. Rank by durable outcome, focus match, source strength, and collaboration
   impact.

## Write

1. Map each date to `snippets/work-log/YYYY MM mon DD - mon DD.md`.
2. Append supplied focus first as a `focus` entry with a `manual` source.
3. Build stable dated entries from verified candidates.
4. Canonicalize source URLs and IDs.
5. Skip an activity when its stable entry ID or all unique event source keys
   already exist.
6. Append new entries. Never edit, delete, reorder, or merge prior entries.
7. Fix a prior claim with an appended correction entry.
8. Add each new weekly file to the index. Refresh its row after later appends.
   Keep newest weeks first. Include a one-line summary and key focus tags.

Every activity claim needs at least one event source. A parent PR, issue, or
thread URL can add context, but it does not prove a new event by itself.

## Failures

- Continue after one optional collector fails.
- Report each failed or unavailable collector and the missing coverage.
- Stop before writing when deduplication state cannot be read or when candidate
  identity is not stable.
- Never replace a failed source with an unsupported claim.

## Persistence

After changes, invoke `persist-work-notes` once. Pass exact changed weekly log
files and the index when changed. Include a short action summary.

Skip persistence on a no-op.

## Result

Return:

- new entry IDs
- skipped duplicate keys and noise reasons
- collector counts, failures, and missing coverage
- changed files
- commit SHA
- push result

See [evaluations](references/evaluations.md).
