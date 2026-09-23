# Examples

## Multi-source shipped work

```markdown
## [2026-09-23 15:40] ship | Safer service restart policy
- Entry ID: `activity:github-commit:github/service@abc1234`
- Summary: Added restart rules and a regression test, then merged the change.
- Focus: `reliability`, `codespaces`
- Sources:
  - `github-commit` | `github/service@abc1234` | [abc1234](https://github.com/github/service/commit/abc1234)
  - `github-pr-event` | `github/service#100:merged:2026-09-23T15:40:00Z` | [github/service#100](https://github.com/github/service/pull/100)
  - `copilot-session` | `53a7e996-ba21-4316-899e-a0f7a6240898`
```

The commit and merge event prove the activity. The session adds context.

## Genuine review

```markdown
## [2026-09-23 11:15] review | Cache invalidation edge cases
- Entry ID: `activity:github-review:github/web#200:prr_kwdo123`
- Summary: Requested changes for stale reads and documented three edge cases.
- Focus: `caching`, `reliability`
- Sources:
  - `github-review` | `github/web#200:PRR_kwDO123` | [review](https://github.com/github/web/pull/200#pullrequestreview-2)
  - `github-pr` | `github/web#200` | [github/web#200](https://github.com/github/web/pull/200)
```

A review request without a submitted review creates no entry.

## Slack decision with document

```markdown
## [2026-09-23 14:10] research | Selected cache-key strategy
- Entry ID: `activity:slack-message:C123:1758654600.000100`
- Summary: Compared cache-key options, selected the scoped-key design, and recorded the decision.
- Focus: `caching`
- Sources:
  - `slack` | `C123:1758654600.000100` | [decision thread](https://example.slack.com/archives/C123/p1758654600000100)
  - `document` | `projects/cache-design@def5678` | [[projects/cache-design]]
```

Store the result, not the private conversation.

## Focus without proof

```markdown
## [2026-09-23 09:00] focus | Reliability
- Entry ID: `focus:manual:2026-09-23t09:00:reliability`
- Summary: "Focus on reliability work."
- Focus: `reliability`
- Sources:
  - `manual` | `user-input:2026-09-23T09:00:00-05:00`
```

Write no activity entry when sources do not prove related work.

## Correction

```markdown
## [2026-09-24 10:15] correction | PR result
- Entry ID: `correction:2026-09-24:activity:github-pr-event:github/repo#123:merged:1`
- Corrects: `activity:github-pr-event:github/repo#123:merged`
- Reason: GitHub shows the PR closed without merge.
- Summary: Corrected the prior merge claim.
- Focus: `reliability`
- Sources:
  - `github-pr` | `github/repo#123` | [github/repo#123](https://github.com/github/repo/pull/123)
```
