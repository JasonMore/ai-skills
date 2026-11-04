---
name: slack-context
description: Use when the user asks to fetch context, requirements, decisions, or bug details from a Slack thread, or gives a Slack permalink for another task.
---

# Slack Context

Fetch a Slack thread and use its technical context in the requested task.

## Workflow

### 1. Find the thread

Accept either:

- A permalink such as `https://github.slack.com/archives/C123/p1234567890123456`
- A channel ID plus parent message timestamp

Ask for a permalink only when the user did not provide a thread reference.

Validate a permalink before you read it:

- It contains `/archives/`.
- It has a channel ID (`C[A-Z0-9]+`).
- It has a message timestamp (`p[0-9]+`).

Do not use this skill for these thread types:

- Customer support conversations
- Private DMs, unless the user gives explicit permission
- HR or personnel matters
- Security incident details
- Threads marked confidential or threads with customer PII

### 2. Read it

Prefer Slack MCP `slack_read_thread`. If Slack MCP is unavailable or fails, use:

```bash
gh-slack read <slack-permalink>
```

Do not pause for user review or confirmation after fetching. Use the thread as context at once.

### 3. Keep output safe

Use only details needed for the task. Omit:

- Credentials, tokens, and secrets
- Customer data
- Unrelated personal details
- Unrelated internal links

Do not copy a full thread when a short summary will work.

### 4. Extract useful context

Capture:

- Decisions and requirements
- Reproduction steps
- Expected behavior
- Impact and scope
- Owners and next steps
- Relevant links

Do not infer facts the thread does not support. Mark missing details as open questions.

Focus on technical details. Extract requirements, not opinions about people. Summarize decisions,
not the full conversation. Link to the thread as the source.

For a simple thread, give a short list of the main points. For a complex thread, use this
structure:

```text
Slack thread: <permalink>
Topic: <topic>
Participants: <count>

Requirements:
1. <requirement> (source: <author>)

Implementation notes:
- <note>

Next steps:
1. <step> (owner: <author>)

Open questions:
- <question>
```

### 5. Continue the task

Use the extracted context without asking for a separate content confirmation. Ask only when the
task itself needs a decision, such as unclear scope or conflicting requirements.

## Errors

If Slack MCP fails, try `gh-slack`. If both fail, report the exact error and stop. Do not guess
at thread content.

Common `gh-slack` fixes:

| Problem | Fix |
| --- | --- |
| Extension not installed | `gh extension install rneatherway/gh-slack` |
| Not authenticated | `eval $(gh slack auth -t github)` |
| No channel access or deleted thread | Ask the user for a thread that they can access |
| Invalid URL | Ask for `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TIMESTAMP>` |

## Boundaries

**Will:**

- Read Slack permalinks
- Summarize technical discussions
- Extract decisions, requirements, and bug reports
- Use thread context in follow-up work

**Will not:**

- Store or cache Slack content
- Share Slack content with third-party services
- Fetch non-Slack URLs
- Include secrets or unrelated sensitive details in output

See `README.md` and `examples/feature-implementation.md` for setup and examples.
