---
name: weekly-snippet
description: >
  Builds David Poll's weekly report from handwritten snippets and sourced work
  logs. Use when the user asks to "write my weekly snippet", "format snippets
  for David", "generate weekly report", "create weekly summary", review weekly
  ships, or compile top-of-mind themes, shoutouts, risks, and blockers.
---

# Weekly Snippet

Build one final summary from handwritten notes and append-only work logs. Append
it only to the current handwritten weekly snippet.

See [example output](examples/update.md) before writing.

## Read sources

Read all five inputs:

1. Current handwritten file: `snippets/<current-week>.md`
2. Prior handwritten file: `snippets/<prior-week>.md`
3. Current work log: `snippets/work-log/<current-week>.md`
4. Prior work log: `snippets/work-log/<prior-week>.md`
5. `snippets/work-log/index.md`

Treat a missing work log as empty and flag it. Never create or change a work
log in this skill.

The window starts after the last `# Weekly Snippet` in the prior handwritten
file. If none exists, use all prior content. Include current-week content.

## Build evidence

- Use handwritten notes for intent, meeting context, todos, blockers, and
  personal detail.
- Use work-log entries and corrections for sourced activity.
- Treat work-log focus tags as theme hints, not evidence.
- Let a correction replace the corrected claim during synthesis.
- Deduplicate by stable Entry ID, canonical source URL or ID, then normalized
  claim.
- Count one activity once when it appears in handwritten and work-log sources.
- Compare prior and current todo checkboxes. Include new, non-trivial completed
  items once.
- Verify current PR or issue state before making a status claim.

## Filter PRs in Key Ships & Accomplishments

- Include a PR only when the user is its author or one of its assignees.
- Confirm the user's GitHub login with `gh api user --jq .login`.
- For each candidate PR, fetch `author` and `assignees` with
  `gh pr view <url> --json author,assignees`.
- Compare logins without case sensitivity. Either an author match or an
  assignee match is sufficient. Include a PR that matches both only once.
- Exclude PRs that the user only reviewed, discussed, or mentioned in notes.
  Team ownership alone does not qualify a PR.
- If identity or PR ownership cannot be verified, flag the missing evidence.
  Omit the PR from this section until ownership is verified.
- Apply this filter to every PR in the section, including inline references.
  Other sections can still cite relevant PRs by other authors.

## Conflicts and stale status

List source conflicts and stale status before the draft.

- Prefer a correction entry over its target.
- Prefer a current source-system status over old prose.
- Keep the old dated activity as history. Do not repeat its stale status.
- If a conflict cannot be verified, omit the claim from the final summary and
  ask the user to resolve it.
- Never turn missing source data into a fact.

## Draft

Create:

- Two to four top-of-mind themes
- Ships and accomplishments grouped by feature area, with the PR filter applied
- Warm, specific shoutouts
- Risks and blockers

Show the draft and source flags for user review. After approval, append:

```markdown
# Weekly Snippet

### 💡 What's top of mind for you this week?

### 🚢 Key Ships & Accomplishments

### ✨ Shoutouts

### 🔴 Risks and Blockers

---
<sup>:rocket: Posted via `/snippet` for standardized reporting</sup>
```

## Format

- Preserve any existing draft or daily content.
- Use bold theme and feature headers.
- Put every PR link in an unordered list, in every section.
- Use one bare PR URL per list item, with activity day in parentheses:
  `- https://github.com/<owner>/<repo>/pull/<number> (Tue)`.
- Do not put PR links in prose, tables, or comma-separated groups.
- Do not add PR titles or status words after PR URLs.
- Use markdown links for inline issue, Slack, and document references.
- Use backticks around `@handles`.
- Keep one ship per line. Use active, specific prose.
- Use no em dash or en dash.

## Persist

Read the current file and its Git diff before editing. Append the approved
summary only to that file.

Then invoke `persist-work-notes` with that exact handwritten file and a short
action summary. Skip persistence on a no-op.

See [evaluations](references/evaluations.md).
