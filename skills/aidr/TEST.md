# aidr checks

## Rationale and checks

[Why is AI-generated language so hard to understand?](https://arxiv.org/html/2610.29162v1) reports patterns associated with reading difficulty, including stacked nouns and long dependencies between related words. These findings support checking clarity; they do not prove that any individual sentence is difficult.

Use the focused examples and meaning checks below when changing this skill.
Judge clarity and preserved meaning, not word count. Run the skill on each source
below. The revisions are examples, not exact-match requirements. They support
manual meaning checks; they do not prove that a model follows the skill.

For paired model tests, use [evals/evals.json](evals/evals.json). It includes these
two sources and a held-out technical-ambiguity case. Give each version the same
prompt in a separate context. Grade meaning and clarity against the expectations;
do not treat a structure check as a behavior test.

## Ruby comment: clearer references without invented details

Source:

```ruby
# `_layout` and `_deferred` are fetched as JSON. A direct HTML visit still mounts the repo app,
# which needs its layout route payload and client flags. JSON skips that extra work.
```

Example revision:

```ruby
# `_layout` and `_deferred` are fetched as JSON.
# A direct HTML visit still mounts the repo app.
# The repo app needs its layout route payload and client flags.
# With JSON, the extra work for a direct HTML visit is not done.
```

Check that the result:

- Keeps both identifiers, JSON, the direct HTML visit, and "still."
- States that the repo app needs both its layout route payload and client flags.
- Names the repo app instead of making the reader resolve "which." Connects
  the extra work to the direct HTML visit without inventing its exact steps.
- Keeps "layout route payload" as a technical term. The source does not establish
  a more specific relationship between these nouns.
- Does not claim that JSON never mounts any app, omits client flags, or avoids
  fetching the layout route payload. The source does not specify those details.

## Conditions, uncertainty, and repetition

Source:

```text
If the cache is empty, the service may fetch a payload for the layout route.
The service may fetch a payload for the layout route if the cache is empty.
The timeout is 2 s. The service must not retry unless an operator approves.
```

Example revision:

```text
If the cache is empty, the service may fetch a payload for the layout route.
The timeout is 2 s. The service must not retry unless an operator approves.
```

Check that the result preserves the empty-cache condition, "may," the timeout
value and unit, and the prohibition on retrying without approval. Approval must
not become a requirement to retry. Remove only the repeated fetch statement.
Here, "a payload for the layout route" is explicit in the source; this does not
permit the same expansion of "layout route payload" in the Ruby comment.

For both cases, return only the revised text, with no introduction or explanation.
Check whether the revision requires rereading or guessing a relationship. Improve
the wording only where the source supports the change.
