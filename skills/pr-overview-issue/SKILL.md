---
name: pr-overview-issue
description: This skill should be used when the user asks to "make a new feedback issue", "turn this Slack thread into an issue", "create a PRs Overview issue from Slack", "file a pull-requests issue from this thread", "make a bug/suggestion issue for PRs Overview", or provides a Slack permalink and wants a GitHub issue created in github/pull-requests and added to the PRs Overview project. CRITICAL - always draft and confirm before creating the issue.
---

# PRs Overview Issue from Slack

Turn a Slack thread into a GitHub issue in `github/pull-requests` using the repo's issue-form
templates, then add it to the PRs Overview org project (#19770).

## When to Use

- User shares a Slack permalink and wants a feedback issue for PRs Overview work
- User asks to file a bug or suggestion captured in a Slack thread

## Fixed Targets

- Repo: `github/pull-requests`
- Project: `https://github.com/orgs/github/projects/19770/views/64` (number `19770`, owner `github`)
- Parent: the open `[Batch] Bugs and Feedback` issue (currently `#24787`)
- Never use: the "PRs: First Responder" board (project `3140`); never tag `@github/pull-requests`

## Workflow

### 1. Get the Slack thread reference

Ask for a Slack permalink if none was given. Accept a permalink or a channel ID plus thread
timestamp.

### 2. Read the thread

Prefer the Slack MCP `slack_read_thread`. If the MCP is unavailable or failing, fall back to
`gh-slack read <permalink>` (per user instructions).

Apply `slack-context` handling: omit credentials, customer data, and unrelated personal details.
Use the thread without a separate user review or confirmation step.

### 3. Check for an existing issue

Before drafting, search `github/pull-requests` for an issue that already covers this thread.
See `references/github-ops.md` "Check for an existing issue" for the commands. Build a keyword
query from the thread's feature area and symptom. Avoid bare numbers.

- **If a clear match exists:** return its link. Do not create a duplicate. Then judge whether
  it needs updating (next paragraph).
- **If no match exists:** go to step 4 and draft a new issue.

**Update judgement.** Compare the thread against the matched issue's body and comments. Update
only when the thread adds real signal the issue lacks: new repro steps, added impact, a new
occurrence on a closed issue, or a wrong/missing detail. If the issue already covers it, return
the link and stop. When an update is warranted, propose the specific edit or comment and get
the user's confirmation before writing. Do not tag the team or change routing on an existing issue.

### 4. Draft the issue

Classify the thread as a **Bug** or a **Suggestion**, then fill the matching repo template from
`references/issue-format.md`. Bugs use the bug sections and the `[Bug]` title prefix;
suggestions use the suggestion sections and the `[Suggestion]` prefix. End the body with the
Slack link footer: `[View original Slack conversation](<permalink>)`.

Write the title and all new issue text in ASD-STE100 Simplified Technical English (STE). Use
short sentences, one main idea per sentence, active voice, and common words. Keep required
template headings, labels, product names, error messages, and links unchanged. Use STE for
proposed issue edits and comments too.

Fill sections from what the thread says. Do not invent scope the thread does not support. Where
the thread is silent, keep the section brief or mark an open question. If the type is unclear,
ask the user.

### 5. Confirm before creating

Show the full drafted title and body. Let the user edit. Get explicit confirmation before any
`gh` write command. Never create the issue without confirmation.

### 6. Create the issue and file it

Follow `references/github-ops.md` in order:

1. `gh issue create` with the right label and the current milestone.
2. Attach the parent issue (`addSubIssue` to the open `[Batch] Bugs and Feedback`, currently #24787).
3. `gh project item-add 19770 --owner github --url <issue-url>`.
4. Remove the issue from the "PRs: First Responder" board (project #3140) if automation added it.

If `gh` returns an OAuth error, retry with `env -u GITHUB_TOKEN -u GH_TOKEN gh ...`.

### 7. Report

Return the new issue as a **full URL** (`https://github.com/github/pull-requests/issues/<n>`),
never `#<n>` shorthand: a bare number resolves against the current repo. Confirm: milestone set,
parent linked, added to project #19770 (status `Triage`), NOT on the First Responder board, and
the team was not tagged.

## Always use full links

Every issue, PR, or parent reference you return to the user must be a full URL
(`https://github.com/github/pull-requests/issues/<n>`). Never use `#<n>` shorthand in output:
a bare number resolves against whatever repo the user is in, which points at the wrong place.

## References

- `references/issue-format.md` - Bug and suggestion templates, title convention, Slack footer
- `references/github-ops.md` - Dedupe search, update judgement, and the create/milestone/parent/project/First Responder commands

## Boundaries

**Will:**
- Read a Slack thread and draft a bug or suggestion issue from the repo templates
- Search for an existing issue first and return its link instead of creating a duplicate
- Judge whether an existing issue needs updating and, on confirmation, comment or edit it
- Create the issue in `github/pull-requests` (with the `bug` or `suggestion` label) after user confirmation
- Set the current milestone and link the issue to the `[Batch] Bugs and Feedback` parent
- Add the created issue to org project #19770
- Remove the issue from the "PRs: First Responder" board if automation added it
- Report the issue URL

**Will Not:**
- Create an issue when a matching one already exists
- Create an issue without showing the draft and getting confirmation
- Tag the pull-requests team (`cc/ @github/pull-requests`) or leave the issue on the First Responder board
- Fabricate steps, impact, or metrics not grounded in the thread
- Include sensitive Slack content the user has not reviewed
- Target any repo or project other than the fixed targets above unless the user asks
