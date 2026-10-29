# GitHub Operations

All writes happen only after the user confirms the drafted issue. Draft first, confirm, then
run these steps in order.

## Auth fallback

If any `gh` command returns an OAuth error, retry the same command prefixed with
`env -u GITHUB_TOKEN -u GH_TOKEN`:

```bash
env -u GITHUB_TOKEN -u GH_TOKEN gh <command>
```

## Do not tag the team, do not use the First Responder board

- The issue body must never contain `cc/ @github/pull-requests` (see `issue-format.md`).
- The issue must not stay on the "PRs: First Responder" board (project `3140`). Automation can
  add `bug` issues there. Step 5 removes it if it appears.

## Check for an existing issue

Run this before drafting. Do not create a duplicate.

Build a keyword query from the thread: feature area plus symptom (for example
`Copilot reviewer overview link`). Drop bare numbers; a lone number matches issue IDs.

```bash
env -u GITHUB_TOKEN -u GH_TOKEN gh issue list --repo github/pull-requests \
  --search '<keywords>' --state all -L 10 \
  --json number,title,state,url
```

Review the hits. A match shares the same feature area and symptom, not just a shared word.

- Match found: return its URL. Then judge whether it needs updating (see below).
- No match: proceed to create.

### Update judgement

Read the matched issue body and comments:

```bash
env -u GITHUB_TOKEN -u GH_TOKEN gh issue view <number> --repo github/pull-requests \
  --json title,state,body,comments
```

Update only when the thread adds signal the issue lacks: new repro steps, added impact, a fresh
occurrence on a closed issue, or a wrong detail. Otherwise return the link and stop. When an
update is warranted, propose the exact edit or comment and get user confirmation first:

```bash
# Add context as a comment (preferred for new occurrences):
env -u GITHUB_TOKEN -u GH_TOKEN gh issue comment <number> --repo github/pull-requests --body-file /tmp/update.md
# Or edit the body when a section is wrong or missing:
env -u GITHUB_TOKEN -u GH_TOKEN gh issue edit <number> --repo github/pull-requests --body-file /tmp/body.md
```

Do not tag the team or change milestone, parent, or project routing on an existing issue unless
the user asks.

## 1. Create the issue

Write the confirmed body to a temp file, then create from it. A body file avoids shell-quoting
problems with multi-line Markdown. Set the milestone at creation.

Bug:

```bash
gh issue create \
  --repo github/pull-requests \
  --title "[Bug] <summary>" \
  --label bug \
  --milestone "<current milestone>" \
  --body-file /tmp/pr-overview-issue.md
```

Suggestion: same command with `--title "[Suggestion] <summary>"` and `--label suggestion`.

The command prints the new issue URL. Capture it as `ISSUE_URL` and the number as `ISSUE_NUM`.

## 2. Pick the milestone

Attach the current PRs Overview milestone. Do not hardcode it: milestones roll over. Derive it
from a recent sibling under the batch, then confirm with the user before creating.

```bash
# Milestone of the most recent bug/feedback issues (skip nulls):
env -u GITHUB_TOKEN -u GH_TOKEN gh api graphql -f query='
query { repository(owner:"github", name:"pull-requests") {
  issues(first:20, states:OPEN, orderBy:{field:CREATED_AT, direction:DESC},
         filterBy:{labels:["bug"]}) {
    nodes { number milestone { number title } }
  }
} }' --jq '.data.repository.issues.nodes[] | select(.milestone!=null) | .milestone.title' | head -1
```

At authoring time this was `Overview Default Landing (Staff Ship Opt-out)` (milestone `164`).

## 3. Attach the parent issue (sub-issue link)

Parent: the open `[Batch] Bugs and Feedback` issue (currently `#24787`). Find it by title so
the link survives a new batch:

```bash
PARENT_NUM=$(env -u GITHUB_TOKEN -u GH_TOKEN gh issue list --repo github/pull-requests \
  --search '"[Batch] Bugs and Feedback" in:title' --state open -L 1 --json number --jq '.[0].number')
```

`gh issue create` cannot set a parent, so link with the `addSubIssue` GraphQL mutation using
node IDs:

```bash
PARENT_ID=$(env -u GITHUB_TOKEN -u GH_TOKEN gh issue view "$PARENT_NUM" --repo github/pull-requests --json id --jq .id)
CHILD_ID=$(env -u GITHUB_TOKEN -u GH_TOKEN gh issue view "$ISSUE_NUM" --repo github/pull-requests --json id --jq .id)

env -u GITHUB_TOKEN -u GH_TOKEN gh api graphql -f query='
mutation($p:ID!, $c:ID!) {
  addSubIssue(input:{issueId:$p, subIssueId:$c}) { issue { number } subIssue { number } }
}' -f p="$PARENT_ID" -f c="$CHILD_ID"
```

## 4. Add the issue to the PRs Overview project

Project: `https://github.com/orgs/github/projects/19770/views/64`
(number `19770`, owner `github`, title "Inklings - PRs Experience Board").

```bash
gh project item-add 19770 --owner github --url "$ISSUE_URL"
```

New items land in `Triage`. If an item shows no status, set it to `Triage` with the
`projects-mastery` skill.

## 5. Remove from the First Responder board if present

Check whether automation put the issue on "PRs: First Responder" (project `3140`) and remove
it if so:

```bash
ITEM_ID=$(env -u GITHUB_TOKEN -u GH_TOKEN gh project item-list 3140 --owner github -L 200 --format json \
  --jq ".items[] | select(.content.number==$ISSUE_NUM) | .id")
if [ -n "$ITEM_ID" ]; then
  env -u GITHUB_TOKEN -u GH_TOKEN gh project item-delete 3140 --owner github --id "$ITEM_ID"
fi
```

## 6. Report

Give the user (all as full URLs, never `#<n>` shorthand):
- The new issue URL
- Milestone attached, parent issue linked (full URL to the parent)
- Added to project #19770 (status `Triage`)
- Confirmation it is NOT on the First Responder board and the team was not tagged

## Notes

- Do not create a real issue while building or testing this skill.
- If a later step fails, report the issue URL and the exact failing step so the user can retry.
