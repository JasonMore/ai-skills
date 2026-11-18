---
name: create-pr
description: Use whenever a task is about to end in a new pull request. That covers explicit requests ("create a PR", "open a draft PR", "send a pull request", "push this and open a PR") AND byproduct PRs where the user never said "PR" but the work ends in one (after implementing a fix, removing a feature flag, mirroring another PR, resolving an investigation, etc.). Invoke this skill before running `gh pr create` or pushing a branch to open a PR. Covers github/github monolith and other GitHub repos that ship code via PR.
metadata:
  summary: >-
    Open polished pull requests using each repository's live template
    and required review conventions.
---

# Create PR — open a high-quality pull request the user won't have to fix up

Use this skill any time your work ends in a new pull request — whether explicitly requested ("create a draft PR", "push this and open a PR", "send a pull request") or implied as a byproduct ("implement this fix and send it for review"). For iterating on an already-open PR (addressing comments, re-requesting review, watching CI), use `manage-pr` instead.

## Before opening a new PR

Resolve the target repository and base first: use the explicitly requested branch, otherwise the agreed stack parent, otherwise the target repository's default branch. An unresolved/unknown stack parent is a blocker, never permission to fall back to the default branch. Select the configured remote for that target repository (verifying `git remote get-url <remote>` matches the target repository) and fetch the base before checking whether the work is needed:

```bash
cd /path/to/their/repo || exit 1
REMOTE='<resolved-target-remote>'
BASE='<resolved-target-base>'
git fetch --quiet "$REMOTE" "+refs/heads/$BASE:refs/remotes/$REMOTE/$BASE" || exit 1
BASE_SHA=$(git rev-parse --verify "refs/remotes/$REMOTE/$BASE^{commit}") || exit 1
printf '%s\n' "$BASE_SHA"
```

Record the target repository, remote, base name, and fetched `BASE_SHA` in session state and rebind them from that record in each new shell; never reselect the default later. If the lookup or fetch fails, stop and report the missing base — do not fall back to a local branch, stale tracking ref, or default branch. The `+` only updates the remote-tracking ref if a published parent was rewritten; it never resets a working branch or authorizes a force-push.

- **Gap check at `BASE_SHA`:** Confirm the requested gap still exists at `BASE_SHA` (not the primary checkout or another branch). Reuse valid evidence for `BASE_SHA` and investigate gaps. If the **entire requested outcome** is already satisfied on `BASE_SHA`, name the base SHA or superseding change and stop without opening a duplicate PR or closing another PR. If only part is satisfied, preserve and validate the unsatisfied remainder; never drop scope to make a smaller PR, and treat an uncertain premise as needing investigation or an explicit limitation.
- **Stack check:** If the change mixes concerns that should be reviewed separately, use `split-large-prs`. If a stack decomposition was already agreed in this session, reuse it rather than re-running `split-large-prs` on each layer.
- **`CODEOWNERS` check for new files:** When adding new files in shared repositories, discover the effective ownership file at `BASE_SHA` by checking `.github/CODEOWNERS`, root `CODEOWNERS`, then `docs/CODEOWNERS` in that precedence order. If present, check its rules so new team-owned files live under existing team-owned paths when appropriate, or include an update to that ownership file (noting GitHub evaluates the base branch's `CODEOWNERS` for the current PR).

## Workflow

### 1. Confirm the checkout and head branch

Use the repository checkout selected for the task. A worktree is optional. Preserve user changes and any implemented branch or upper stack layer; never recreate or reset existing work from the base. Verify and record the checkout path and actual head branch alongside the target repository, remote, and base in the session record:

```bash
BASE='<recorded-target-base>'
HEAD_BRANCH=$(git symbolic-ref --short HEAD) || exit 1
if [ "$HEAD_BRANCH" = "$BASE" ]; then
  echo "Resolve a feature head distinct from the target base before publishing." >&2
  exit 1
fi
```

If HEAD is detached or equals `$BASE`, stop and report that the head branch needs resolution; never push `$BASE` or invent a placeholder branch name for an existing layer. Rebind the checkout path and `HEAD_BRANCH` in every shell.

### 2. Read and follow the repo's PR template at `BASE_SHA`

Discover the template from the recorded `BASE_SHA` (checking root, `.github/`, `docs/`, and `PULL_REQUEST_TEMPLATE/` directories), never from the feature branch or default branch:

```bash
BASE_SHA='<recorded-base-sha>'
git ls-tree --name-only "$BASE_SHA"
git ls-tree -r --name-only "$BASE_SHA" -- .github docs
# Read the discovered template path from BASE_SHA (not a guessed filename):
git show "$BASE_SHA:<discovered-template-path>"
```

Copy applicable headings, option lines, and HTML-comment label markers **verbatim** from the live template and delete inapplicable options (see [`references/template-formats.md`](references/template-formats.md)). When delegating PR-body drafting to a sub-agent, paste the literal template from `git show "$BASE_SHA:<template-path>"`, instruct it to output only the body using verbatim markers from that template, and verify markers against `references/template-formats.md` before posting.

#### Body writing rules (see [`references/body-examples.md`](references/body-examples.md))

- **Lead with why, not what (1–3 sentence summary).** If a template starts with a no-heading summary above a *what* heading, put the motivation at the top and mechanics under the heading. Never open with filler ("This PR introduces…", "This change ensures…", "In order to…").
- **Link the issue, don't re-narrate it:** Use `Closes #N` for same-repo or `owner/repo#N` (or full URL) for cross-repo references (bare `#N` in `github/github` autolinks to `github/github#N`). Don't restate an incident timeline or earlier attempts either; the why must still make sense without opening the link.
- **Describe the final proposal, not abandoned pivots:** After a design pivot, delete stale narrative and recheck factual claims against the final diff, while keeping real rationale, companion/runtime dependencies, rollout risks, and validation limitations. Leave out process history too: review-fix SHAs, review rounds, size counts, draft-state notes ("opening as draft"), closed-PR references ("supersedes closed #N", "previously attempted in #N"), or "this was meant to go in #N".
- **Omit what the diff already shows** (unless requested): file/line stats, file/module lists, removed-symbol inventories, per-repo matrices, "non-goals" lists, and code-restatement prose ("matches precedent X", "reuses enum Y").
- **Always include what the diff cannot show:** why now / why safe, single-sentence per-FF rollout state (Gating), single-sentence per-consumer cross-repo impact (Coordination), 1–2 sentence test coverage area summary (Tests — not a list of test names), and normal + hard rollback paths (Rollback, when beyond plain revert).
- **Keep sections tight:** What is usually 2–4 behavior bullets; implementation edge cases belong in code and tests, but keep fallback or compatibility behavior a reviewer or user would notice. Tests links any manual or end-to-end run and names anything not verified (Step 3), without commands, run/assertion counts, OS/tool versions, lint/typecheck results, or the red/green story. Notes/risks cover only what a reviewer must act on or watch after merge.
- **Collapse bulky evidence:** Dry-run output or before/after samples a reviewer needs get a one-line summary in the body plus one collapsed `<details>` block, each sample shown once.
- **Reread before writing the body file** and cut redundant detail a reviewer can get from the diff, CI, or the linked issue; keep the short why and reviewer-visible behavior the rules above require.
- **Narrow exception — caller-required safety evidence:** When an owning workflow (e.g. `remove-feature-flag`) requires merge/deletion actors to inspect an inventory, keep the concise gate verdict, identifier list, expected residual set, search scope/completeness, timestamp, and unchecked checklist visible, and place the full inventory in one collapsed `<details>` appendix or an explicitly authorized linked PR comment accessible to those actors. Never substitute a private local path (e.g. `/tmp/...`) or invent template label markers. If the required evidence cannot be shared in the PR, stop and report the publication blocker.

### 3. Run the repository's targeted validation

Run the repo's existing formatter, linter, build, and focused tests on the changed files (using `bin/` scripts or contributing docs; never invent new tooling). Inspect `git diff` if formatting modifies files.

Select validation that exercises the claimed behavior and preserved existing behavior. A build, green CI, or a running preview alone does not prove a behavioral claim (e.g. state persistence across reload). If local tooling is unavailable or a behavioral claim could not be exercised locally, state that limitation explicitly in the PR body and final report rather than claiming it was verified (an authorized draft may still be opened with the limitation stated; do not provision an environment just to open a draft).

### 4. Write a concise commit message

Use a **lowercase sentence-fragment subject** (no `feat:` / `fix(scope):` prefixes, no capitalized titles, no "Opening as draft" hedges) with one logical change per commit. Add a short body **only** for a non-obvious why, risk, or trade-off (never to restate the diff), and always include the Copilot trailer:

```bash
git commit -m "<lowercase one-line subject>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### 5. Pre-push adversarial review and push

For non-trivial code or skill/prompt changes when `adversarial-review` is installed, run `adversarial-review` on `merge-base..HEAD` before pushing unless it already covered the current changes (still re-run if new commits landed after an earlier review), edits are trivial prose, or the user said to skip review. When addressing findings, prefer **deleting or simplifying** the code that provoked a finding over stacking new defensive guards, and compare `git diff --stat "$(git merge-base "$BASE_SHA" HEAD)"` before and after each round so review rounds shrink or hold steady rather than bloating the PR (if addressing a finding would add >15 net production lines or introduce a new fallback/configuration/validation layer, first look for a behavior-preserving simplification; if a verified necessary fix cannot meet the ≤15-line size budget without breaking required behavior, stop and ask the user to approve the larger fix rather than dismissing the finding). Fix, validate, and commit adopted findings, surface any open questions or incomplete panel to the user, and keep review output out of the PR body.

```bash
cd '<recorded-checkout-path>' || exit 1
REMOTE='<recorded-target-remote>'
HEAD_BRANCH='<recorded-head-branch>'
[ "$(git symbolic-ref --short HEAD)" = "$HEAD_BRANCH" ] || exit 1
git push -u "$REMOTE" "refs/heads/$HEAD_BRANCH:refs/heads/$HEAD_BRANCH" || exit 1
```

If the branch already exists upstream from a prior session, ask the user before force-pushing.

### 6. Refresh the actual base, create the PR (draft by default), and verify readback

Refresh the recorded target base after implementation and review. Rebind the checkout path, target repository, remote, base, and head branch from the session record, verify the remote URL still matches the target repository, and invalidate any prior validated base/head pair:

```bash
cd '<recorded-checkout-path>' || exit 1
REMOTE='<recorded-target-remote>'
BASE='<recorded-target-base>'
HEAD_BRANCH='<recorded-head-branch>'
[ "$(git symbolic-ref --short HEAD)" = "$HEAD_BRANCH" ] || exit 1
STATUS=$(git status --porcelain) || exit 1
[ -z "$STATUS" ] || { echo "Working tree is not clean" >&2; exit 1; }
git fetch --quiet "$REMOTE" "+refs/heads/$BASE:refs/remotes/$REMOTE/$BASE" || exit 1
REFRESHED_BASE_SHA=$(git rev-parse --verify "refs/remotes/$REMOTE/$BASE^{commit}") || exit 1
printf 'Refreshed base: %s\n' "$REFRESHED_BASE_SHA"
if ! git merge-base --is-ancestor "$REFRESHED_BASE_SHA" HEAD; then
  git merge "$REFRESHED_BASE_SHA" -m "merge $REMOTE/$BASE before PR creation

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>" || exit 1
fi
```

Save `REFRESHED_BASE_SHA` as pending in the session record across shells (even if the merge stops on a conflict; never replace it with a later fetch while resolving). Resolve conflicts without rebasing, force-pushing, or disabling commit signing. If HEAD changed, re-run affected Step 3 validation (or record unavailable tooling as an explicit limitation) and inspect/commit any edits. If the refreshed base already satisfies the entire requested outcome, stop per the initial gap check.

After validation and a successful explicit push (Step 5) succeed, record `BASE_SHA=REFRESHED_BASE_SHA` and `VALIDATED_HEAD=$(git rev-parse HEAD)` (plus any validation limitations) in the session record. If the push failed or the checkout switched branches, stop — never mark an unpushed or wrong-branch commit as validated/published. If the template changed at `BASE_SHA`, reread it per Step 2 and update the body.

Retry this refresh/validation cycle **at most once** across pre-create and post-create checks combined (persisting the retry count in the session record); if base churn or conflicts persist after one retry, stop and report publication blocked.

Write the body to a unique temp directory (`mktemp -d -t pr-body-XXXXXX`), re-verify base/HEAD/remote immediately before `gh pr create`, and default to `--draft` unless the user explicitly asked for a ready/open non-draft PR:

```bash
TARGET_REPO='<recorded-owner/repo>'
REMOTE='<recorded-target-remote>'
BASE='<recorded-target-base>'
HEAD_BRANCH='<recorded-head-branch>'
BASE_SHA='<recorded-validated-base-sha>'
VALIDATED_HEAD='<recorded-validated-head-sha>'
cd '<recorded-checkout-path>' || exit 1
PR_TMP=$(mktemp -d -t pr-body-XXXXXX)
cat > "$PR_TMP/body.md" <<'EOF'
<full template-formatted body>
EOF
[ "$(git symbolic-ref --short HEAD)" = "$HEAD_BRANCH" ] || exit 1
git fetch --quiet "$REMOTE" "+refs/heads/$BASE:refs/remotes/$REMOTE/$BASE" || exit 1
CURRENT_BASE_SHA=$(git rev-parse --verify "refs/remotes/$REMOTE/$BASE^{commit}") || exit 1
if [ "$CURRENT_BASE_SHA" != "$BASE_SHA" ] || [ "$(git rev-parse HEAD)" != "$VALIDATED_HEAD" ]; then
  echo "Base or HEAD moved; repeat refresh, affected validation, and push before creating the PR." >&2
  exit 1
fi
git merge-base --is-ancestor "$BASE_SHA" HEAD || exit 1
STATUS=$(git status --porcelain) || exit 1
[ -z "$STATUS" ] || { echo "Working tree is not clean" >&2; exit 1; }
REMOTE_HEAD=$(git ls-remote --exit-code "$REMOTE" "refs/heads/$HEAD_BRANCH") || exit 1
[ "$(printf '%s\n' "$REMOTE_HEAD" | cut -f1)" = "$VALIDATED_HEAD" ] || exit 1
PR_URL=$(gh pr create --repo "$TARGET_REPO" --draft \
  --base "$BASE" \
  --head "$HEAD_BRANCH" \
  --title "<lowercase sentence fragment, no feat:/fix(scope): prefixes — mirrors the commit subject>" \
  --body-file "$PR_TMP/body.md") || exit 1

printf '%s\n' "$PR_URL" "$PR_TMP/body.md"
gh pr view "$PR_URL" --repo "$TARGET_REPO" \
  --json body,baseRefName,headRefName,headRefOid,isDraft,mergeable,mergeStateStatus || exit 1
```

**Verify readback and mergeability:**
- Confirm `baseRefName == BASE`, `headRefName == HEAD_BRANCH`, `headRefOid == VALIDATED_HEAD`, `isDraft` matches the requested state, and the **entire** returned `body` (not just the first lines) matches `$PR_TMP/body.md`. If any field mismatches, fix the **existing** PR (never open a duplicate). If `gh pr edit --body-file` fails due to missing `read:org` token scope, patch via REST:
  ```bash
  jq -Rs '{body: .}' < "$PR_TMP/body.md" > "$PR_TMP/patch.json"
  gh api -X PATCH "repos/$TARGET_REPO/pulls/<n>" --input "$PR_TMP/patch.json" -q .body | head -5
  ```
- If `mergeable == UNKNOWN` or `mergeStateStatus == UNKNOWN`, wait briefly and reread (report unverified if `UNKNOWN` persists). If `mergeable == CONFLICTING` or `mergeStateStatus == DIRTY`, refresh/merge `$REMOTE/$BASE`, repeat affected validation, push, and recheck the **existing** PR within the same single retry budget (stop and report blocked if still conflicting). A conflict-free PR does not need another merge just because the base advanced after creation.
- Remove `$PR_TMP` only after readback verification and any correction succeed; keep `$PR_TMP` if blocked.

### 7. Report back

Report the PR URL, checkout path, branch name, diff size (files changed, +/- lines), and whether tests/linters ran locally or were deferred to CI. Report workflow evidence meant for the user (size-budget checks, test-first results, review-loop outcomes including findings not fixed) here, not in the PR body.

## Boundaries

**Will:**
- Resolve and fetch the explicit/stack/default base at the target remote, verify the gap at `BASE_SHA`, and preserve any existing layer head and user changes.
- Use the live PR template from `BASE_SHA` verbatim (including HTML label markers), write a concise why-first body, run targeted validation, and run pre-push `adversarial-review` when installed.
- Refresh the base before creation, open as `--draft` by default using a unique `--body-file`, and verify full readback (`body`, `baseRefName`, `headRefName`, `headRefOid`, `isDraft`, `mergeable`, `mergeStateStatus`).

**Will Not:**
- Overwrite user changes, fall back to another base when fetch fails, or reset an existing stack layer.
- Paraphrase template label markers, include unrequested file/symbol inventories (outside the caller-required safety-evidence exception) or "non-goals" sections, or substitute a private `/tmp` path for required shared safety evidence.
- Claim unexercised behavior was validated, force-push without permission, open a duplicate PR on readback/conflict mismatch, or claim completion while conflicting.

## References

- [`references/template-formats.md`](references/template-formats.md) — Reading live templates and validating HTML label markers.
- [`references/body-examples.md`](references/body-examples.md) — Good vs. bad PR description examples.
