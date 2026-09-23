# Source policy

Use the narrowest query that covers the date range. Use an exclusive end date
for GitHub and Slack searches.

## GitHub

Run:

```bash
python3 "$SKILL_DIR/scripts/github_activity.py" \
  --owner github \
  --start YYYY-MM-DD \
  --end YYYY-MM-DD \
  --output /path/to/github-activity.json
```

Date-only `--start` and `--end` values are inclusive local dates. The script
converts them to UTC API boundaries. Use `--timezone` when the host timezone
does not match the user's timezone.

Meaningful events:

- authored PR opened, marked ready, merged, or closed
- authored commit pushed during the range
- submitted approval, changes request, review body, or inline review comments
- issue authored, closed, or completed by the user
- substantive issue comment or investigation update
- authored discussion, substantive reply, or accepted answer

Do not count:

- review requests with no submitted review
- assignments, mentions, labels, or reactions without a later outcome
- bot-only events
- state snapshots with no event in the range
- a PR or issue URL reused without a new event source

Search can truncate. Split the date range when a query reaches its result
limit, then deduplicate by source-native event ID.

## Slack

Prefer Slack MCP:

1. Resolve the user's profile and member ID.
2. Search authored messages:
   `from:<user> after:START before:END_EXCLUSIVE`.
3. Search mentions:
   `<@USER_ID> after:START before:END_EXCLUSIVE`.
4. Read each candidate thread before classification.

Keep:

- authored thread roots that received useful replies
- replies that unblock work, answer a technical question, or make a decision
- messages with PR, issue, incident, task, or durable document links
- messages with clear decision or action language
- mentions that prove a handoff, unblock, completed result, or recognition

Skip:

- acknowledgements such as "thanks", "done", "sounds good", or emoji-only text
- automated posts, link unfurls, reminders, and repeated bot output
- casual conversation
- repeated messages that support the same outcome

Use the message timestamp as the event ID. Use the thread timestamp as context.
Store the permalink and a factual summary. Do not copy a private conversation
into the work log.

If Slack MCP fails, use `gh-slack` with the same date, author, and thread rules.
Report unavailable private-channel coverage.

## Copilot

Query session history for the date range. Start with seven days or less and
filter by exact session IDs before reading turns.

Use:

- sessions with a durable result
- checkpoints that name a decision or completed phase
- `session_files` changes outside generated work logs
- `session_refs` for exact PR, issue, and commit links
- completed remote agent tasks with a material output

Skip:

- brief lookups
- abandoned exploration with no output
- repeated sessions that only restate the same source event
- assistant claims that have no file, GitHub, Slack, meeting, or document proof

## Meetings

Use calendar-linked notes. Read only the matching date section.

Keep:

- decisions
- completed action items
- incident response
- substantial design, review, planning, or coordination work

Use `meeting-note:<path>#<date>` as the event source. A calendar event alone
proves attendance, not an outcome.

## Documents

Consider files from Copilot session changes, Git commits in the range, and
current vault changes with an in-range modification time.

Keep research, design, investigation, decision, and handoff documents with
meaningful content changes.

Exclude:

- `snippets/work-log/`
- `.obsidian/`, `.git/`, and session state
- generated indexes and formatting-only changes
- deleted or moved files when no work outcome can be verified

Use a commit SHA when committed. For an uncommitted file, use its repository
path plus content hash and modification timestamp.

## Correlation

Merge candidates when they share one outcome and have matching links, source
references, files, or close timestamps.

Examples:

- Copilot session + commit + PR merge
- Slack decision + design document
- meeting decision + issue update
- agent task + PR review

Keep separate candidates for separate reviews, commits, decisions, incidents,
or deliverables, even when they use the same parent PR or issue.

## Ranking

Rank in this order:

1. shipped or completed outcome
2. incident response or unblock
3. substantive review or decision
4. durable research or design document
5. meaningful coordination with a verified result

Increase rank for focus match and several independent sources. Do not promote a
low-confidence candidate only because it matches user focus.
