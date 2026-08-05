---
name: update-daily-snippet
description: >
  This skill should be used when the user asks to "update my snippets",
  "add to my weekly summary", "update daily snippet", "what did I work on",
  "summarize my sessions", "add today's work to snippets", or needs to
  gather work from Copilot sessions (local and remote) and add summaries
  to the weekly snippets file.
author: JasonMore
---

# Update Daily Snippet

Gather work from local Copilot CLI sessions and remote coding agent tasks, then append concise summaries to the weekly snippets file.

## When to Use

- End of day or start of next day, to capture what was done
- User asks to update snippets, summarize sessions, or log daily work
- User wants to see what they worked on across all Copilot sessions

## Snippets File Location

Weekly snippet files live in `Github/snippets/` with the naming pattern:

```
YYYY MM mon DD - mon DD.md
```

Example: `2026 03 mar 16 - mar 20.md`

If the file for the current week does not exist, create it.

## Process

### 1. Identify the date range

Determine which day(s) to summarize. Default: today. The user may ask for yesterday, a range, or the whole week.

### 2. Gather local CLI sessions

Query the session store for sessions created in the target date range:

```sql
SELECT s.id, s.cwd, s.repository, s.branch, s.summary, s.created_at, s.updated_at
FROM sessions s
WHERE s.created_at >= '<start_date>T00:00:00'
  AND s.created_at < '<end_date_exclusive>T00:00:00'
ORDER BY s.created_at ASC
```

Then fetch first few turns for context on what was done:

```sql
SELECT session_id, turn_index, substr(user_message, 1, 500) as user_msg,
       substr(assistant_response, 1, 500) as asst_resp
FROM turns
WHERE session_id IN ('<id1>', '<id2>', ...)
  AND turn_index <= 3
ORDER BY session_id, turn_index
```

Also check checkpoints for longer sessions:

```sql
SELECT session_id, checkpoint_number, title, overview, work_done
FROM checkpoints
WHERE session_id IN ('<id1>', '<id2>', ...)
ORDER BY session_id, checkpoint_number
```

### 3. Gather remote agent tasks

```bash
gh agent-task list -L 50
```

This returns tab-delimited rows: title, PR number, repo, status, timestamp. Filter to the target date range. Cross-reference PR numbers with local session context to avoid duplication.

For any interesting agent task PRs, get details:

```bash
gh pr view <PR_NUMBER> -R <OWNER/REPO> --json title,url,state,headRefName,createdAt
```

### 4. Read the current snippets file

Check what is already written to avoid duplicating content.

### 5. Organize summaries

Plan the content by day using `# Mon`, `# Tue`, etc. as top-level headers. Do not edit the snippet file yet.

Group related work under descriptive `##` subheadings. For each group:
- Write a short prose summary of what was accomplished (1-3 sentences)
- List PRs with links in the format `[repo#number](url) - description`
- Include agent task PRs that were opened, noting if they were closed/superseded

**What to include:**
- Feature work, bug fixes, and PRs (both manual and agent-created)
- Research and investigation sessions with key findings
- Tooling and developer experience improvements
- Meeting notes processing and notable decisions from 1:1s
- Documentation and onboarding work

**What to skip:**
- Very brief sessions with no meaningful output (typos, quick lookups)
- Sessions that only explored without producing artifacts
- Git alias changes, minor config tweaks (unless part of a larger tooling effort)

### 6. Resolve Calendar notes and write the snippet

Resolve all Calendar links first. After every event has one target, write the Calendar and planned summaries to the snippet file.

Each day starts with a `## 🤖 Calendar` section listing that day's meetings. Format one bullet per event:

```
- <start time>: <subject> (<duration> min) [[<resolved-note-path>#<YYYY-MM-DD>]]
```

Resolve every event to an existing meeting note before writing any snippet content. Follow [calendar note routing](references/calendar-note-routing.md). Use the note's full vault-relative path and the event date anchor.

If no unique note matches, stop and ask the user which note to use. Do not write a partial snippet or create a link from the raw event subject.

Skip all-day blocks (e.g. "Home"), generic placeholder holds (untitled "busy"), and canceled events.

Example:
```
## 🤖 Calendar

- 10:30 AM: Weekly Jason <> Katie (30 min) [[one-one/@inkblotty Katie McCormick#2026-08-03]]
- 11:35 AM: PR future experience cadence (25 min) [[projects/pr-overview/! PR future experience#2026-08-04]]
```

### 7. Preserve existing content

Never overwrite existing content. Insert new day sections or append to existing sections. Keep any "Still open from last week" section at the bottom.

## Writing Rules

- No em dashes or en dashes. Use colons, periods, or hyphens.
- Keep summaries concise and scannable.
- Use active voice.
- Link every PR mentioned.
- Note when agent-created PRs were closed or superseded by manual work.
- Every Calendar event bullet must link to one resolved existing note.

## Example Output

```markdown
# Tue

## Widget refactor

Extracted shared widget logic into a reusable hook. Replaced three duplicate implementations across the overview, detail, and settings pages.

- [github-ui#12345](https://github.com/github/github-ui/pull/12345) - new `useWidget` hook with tests
- [github-ui#12350](https://github.com/github/github-ui/pull/12350) (agent, closed) - initial attempt on `copilot/widget-refactor` branch, work folded into #12345
- Coding agent also opened [github-ui#12348](https://github.com/github/github-ui/pull/12348) for lint fixes found during refactor

## 1:1 with teammate

- Discussed rollout plan for feature X, agreed on phased approach
- Action item: write RFC by Friday
```

## Boundaries

**Will:**
- Query both local session store and remote agent tasks
- Cross-reference to avoid duplication
- Organize by day and theme
- Preserve existing snippets content

**Will Not:**
- Delete or rewrite existing content without being asked
- Include sensitive meeting details beyond action items and decisions
- Fabricate work that does not appear in session data
