# Work-log schema

## Candidate

Collectors return facts, not prose:

```json
{
  "event_id": "github-review:github/repo#123:PRR_kwDO...",
  "event_at": "2026-09-23T15:20:00-05:00",
  "event_type": "review",
  "title": "Review safer cache invalidation",
  "summary_facts": [
    "Submitted a changes-requested review",
    "Left three inline comments"
  ],
  "focus_hints": ["caching", "reliability"],
  "source": {
    "type": "github-review",
    "id": "github/repo#123:PRR_kwDO...",
    "url": "https://github.com/github/repo/pull/123#pullrequestreview-1"
  },
  "context_sources": [
    {
      "type": "github-pr",
      "id": "github/repo#123",
      "url": "https://github.com/github/repo/pull/123"
    }
  ],
  "role": "reviewer",
  "confidence": "high"
}
```

Required fields are `event_id`, `event_at`, `event_type`, `title`, one
`summary_facts` item, `source.type`, `source.id`, `role`, and `confidence`.

Use source-native event IDs. A parent item ID is not an event ID unless the
item creation or state change is the event.

Confidence values:

- `high`: the source directly proves the actor, time, and outcome
- `medium`: two sources together prove the outcome
- `low`: discovery hint only; do not write an entry

## Collector result

```json
{
  "collector": "github",
  "status": "ok",
  "candidate_count": 4,
  "candidates": [],
  "errors": [],
  "coverage": ["pull-requests", "reviews", "issues", "commits", "discussions"]
}
```

Status is `ok`, `partial`, `unavailable`, or `failed`. Keep source-specific
errors. Do not return `ok` when a required query failed.

## Weekly file

```markdown
# Work Log: 2026-09-21 to 2026-09-25

## [2026-09-23 15:20] review | Safer cache invalidation
- Entry ID: `activity:github-review:github/repo#123:prr_kwdo`
- Summary: Requested changes to prevent stale cache reads and documented three edge cases.
- Focus: `caching`, `reliability`
- Sources:
  - `github-review` | `github/repo#123:PRR_kwDO...` | [review](https://github.com/github/repo/pull/123#pullrequestreview-1)
  - `github-pr` | `github/repo#123` | [github/repo#123](https://github.com/github/repo/pull/123)
```

Use local ISO date and time when known. Use `[YYYY-MM-DD]` only when the source
time is unknown.

Entry types include `focus`, `ship`, `review`, `research`, `meeting`,
`incident`, `tooling`, and `correction`.

Keep Entry IDs stable and lowercase. Normalize URLs by removing fragments that
do not identify the event, tracking query strings, and trailing slashes.

Focus tags are hints. Use short lowercase tags. Write `none` when no focus was
supplied or supported.

## Manual focus entry

```markdown
## [2026-09-23 09:00] focus | Service reliability
- Entry ID: `focus:manual:2026-09-23t09:00:service-reliability`
- Summary: "Focus on service restart behavior and test coverage today."
- Focus: `service-reliability`, `test-coverage`
- Sources:
  - `manual` | `user-input:2026-09-23T09:00:00-05:00`
```

Manual focus proves intent. It does not prove related work.

## Correction entry

```markdown
## [2026-09-24 10:15] correction | Correct PR result
- Entry ID: `correction:2026-09-24:activity:github-pr:github/repo#123:merged:1`
- Corrects: `activity:github-pr:github/repo#123:merged`
- Reason: The source status changed or the prior text was wrong.
- Summary: Corrected the sourced claim.
- Focus: `reliability`
- Sources:
  - `github-pr` | `github/repo#123` | [github/repo#123](https://github.com/github/repo/pull/123)
```

Append corrections. Never alter the corrected entry.

## Index

```markdown
# Work Log Index

- [[snippets/work-log/2026 09 sep 21 - sep 25|2026-09-21 to 2026-09-25]] - Focus: `reliability`, `reviews` - Shipped reliability work and completed design reviews.
```

Keep one row per week. Sort newest first. Do not add counts or timestamps that
cause no-op churn. Replace only the changed week's row.
