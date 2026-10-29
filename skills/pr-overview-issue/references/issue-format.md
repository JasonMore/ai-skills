# Issue Format

Issues in `github/pull-requests` follow the repo's issue-form templates. Match the template
that fits the thread. Do not invent your own sections.

## Pick the type

- **Bug**: something is broken, wrong, or regressed. Title prefix `[Bug]`. Label `bug`.
- **Suggestion**: a new feature or enhancement. Title prefix `[Suggestion]`. Label `suggestion`.

If the thread is unclear, ask the user which type. Confirm the type in the draft step.

## Title

`[Bug] <concise summary>` or `[Suggestion] <concise summary>`

State the change or defect, not the thread. Keep it short.

Examples:
- `[Bug] Copilot reviewer link opens a 404 page on the overview page`
- `[Suggestion] Use ColorPicker to set a saved-view color`

## Bug body template

```markdown
### Summary

<Concise description of the problem. Note the affected page/flow.>

### Steps to reproduce

1. <step>
2. <step>
3. **PROBLEM**: <what goes wrong>

### Expected behavior

<What should happen instead.>

### Impact

<Who is affected and how. Blocked? Workaround?>

### References

* <Relevant issues, PRs, tickets. One per line.>

### Additional details

<Any other detail that helps diagnose. Scope, edge cases.>

### Required team ping


[View original Slack conversation](<slack-permalink>)
```

## Suggestion body template

```markdown
### Summary

<What feature or enhancement is suggested.>

### Why

<The problem or pain point it solves. Who benefits.>

#### Customer evidence

* <Users or customers asking for this, with links.>

#### Metrics

<Metrics that show the feature works.>

### Additional details

<Anything else: prior art, past attempts, related issues.>

### Required team ping


[View original Slack conversation](<slack-permalink>)
```

## Rules

- Fill sections only from the thread. Where the thread is silent, leave the section brief or
  write `Open question:` and the gap. Do not fabricate steps, metrics, or impact.
- Write the title and all new issue text in ASD-STE100 Simplified Technical English (STE). Use
  short sentences, one main idea per sentence, active voice, and common words. Keep required
  template headings, labels, product names, error messages, and links unchanged. Use STE for
  proposed issue edits and comments too.
- **Never tag the pull-requests team.** Always leave `Required team ping` blank. Do not add
  `cc/ @github/pull-requests` or any team cc, even though the raw template includes it.
  Pinging the team routes the issue onto their First Responder board, which this skill avoids.
- Always end the body with the Slack link footer:
  `[View original Slack conversation](<slack-permalink>)`.

## Slack permalink for the footer

Use the full thread permalink with query params, like the reference issue:

`https://github.slack.com/archives/<CID>/p<TS_NO_DOT>?thread_ts=<TS_WITH_DOT>&cid=<CID>`

Derive `thread_ts` from the `p<...>` id: insert a dot six digits from the end.
Example: `p1783017402238479` -> `thread_ts=1783017402.238479`, and `cid` is the channel id
in the path (`C0B35BU9DFE`).

## Filled example (bug, from issue #25673)

```markdown
### Summary

On the PR overview page, the Copilot reviewer link opens https://github.com/Copilot. This page
returns a 404 error. On the conversation page, the same link opens the app URL. The overview
page does not show the button that starts a Copilot code review (CCR).

### Steps to reproduce

1. Open a draft PR with Copilot as a reviewer.
2. Open the PR overview page and find the reviewer list.
3. Select the Copilot link. It opens https://github.com/Copilot and shows a 404 error.
4. Open the conversation page and select the Copilot link. It opens the app URL.
5. Check the draft PR. The conversation page shows a button to start a CCR. The overview page
   does not show this button.

### Expected behavior

- The overview reviewer link should open the app URL.
- The overview page should show the same button to start a CCR as the conversation page.

### Impact

Users see a 404 error when they select the reviewer link. They cannot start a Copilot code
review from the overview page.

### References

* Slack internal thread comparing overview and conversation pages.

### Additional details

- This affects draft PRs with Copilot as a reviewer.
- The conversation page has the correct link and the review button.
- The overview page has the wrong link and does not show the review button.

### Required team ping


[View original Slack conversation](https://github.slack.com/archives/C0B35BU9DFE/p1783017402238479?thread_ts=1783017402.238479&cid=C0B35BU9DFE)
```
