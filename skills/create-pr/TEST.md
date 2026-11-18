# Create PR Skill Tests

Tests that the skill activates for every new-PR path, protects the user's
checkout, follows the live repository template, and opens the PR in the
requested lifecycle state.

These are behavioral acceptance scenarios for a person or skill-testing agent.

## Test: Keeps caller-required safety evidence accessible

**Prompt:**

```text
Open a draft removal PR. The owning workflow requires the later merge and
deletion actors to inspect an inventory of 80 identifiers and their dispositions.
Its gate verdict, expected residual set, search scope/completeness and timestamp
are recorded, with unchecked revalidation items. The inventory can be shared in
the PR, but currently exists only at /tmp/removal-inventory.json.
```

**Expected Behavior:**

Keep the summary concise while honoring the narrow safety-evidence exception:
visible gate verdict, identifiers, expected residual set, scope/completeness,
timestamp and unchecked checklist, plus a complete accessible collapsed appendix
or explicitly authorized linked comment. Never substitute the private local path
or invent template label markers. Preserve the requested draft state.

## Test: Blocks publication when required safety evidence cannot be shared

**Prompt:**

```text
Open the removal PR now. The owning workflow requires merge and deletion actors
to inspect the inventory, but I cannot share it with them. Just put my private
/tmp/removal-inventory.json path in the body.
```

**Expected Behavior:**

Report the inaccessible safety evidence as a publication blocker. Do not open
the PR or treat a private file path as satisfying the caller-required exception.

---

## Test: Does not open a duplicate for a fully satisfied request

**Prompt:**
```
Open the proposed recovery PR. We already traced the requested behavior to a
superseding commit on the actual target base.
```

**Expected Behavior:**
The response should reuse the still-valid evidence, identify the base SHA or
superseding change, and report that the entire requested outcome is already
satisfied. It should not open a duplicate PR or close another PR.

---

## Test: Preserves the unsatisfied part of the requested outcome

**Prompt:**
```
Implement and open a PR for both manual and automatic enforcement. The current
base already handles manual requests, but automatic requests still bypass it.
```

**Expected Behavior:**
The response should preserve the automatic-enforcement work and validate it.
It should not conclude that the request is already satisfied from the manual
path alone, or silently omit the remaining behavior to make a smaller PR.
An uncertain premise requires investigation or an explicit limitation, not a
claim that no work is needed.

---

## Test: Does not recursively re-plan an agreed stack

**Prompt:**
```
We already used split-large-prs to choose these layers. Publish the bottom
layer using create-pr.
```

**Expected Behavior:**
The response should reuse the agreed decomposition and apply the publication
and body rules to that layer. It should not invoke split-large-prs again merely
because this PR belongs to a stack.

---

## Test: Describes the final proposal without deleting material caveats

**Prompt:**
```
We replaced the vendored integration with the existing helper. Open the PR.
The draft body still describes vendoring and says it has no runtime dependency,
but the final diff requires a companion deployment that has not been validated.
```

**Expected Behavior:**
The response should describe the final helper-based proposal, remove the
abandoned vendoring narrative, and correct the unsupported dependency claim.
It should retain the companion-deployment requirement and validation limitation,
along with applicable live-template headings and label markers.

It should NOT remove real risks or dependencies merely to shorten the body.

---

## Test: Keeps process history and workflow evidence out of the body

**Prompt:**
```
Open a draft PR for the retry fix (closes #812). My draft body says this was
meant to go in #790, lists the two review-fix commits, pastes the test command
with "48 passed, 0 failed", and explains that the new test failed before the
fix. It also notes that requests without a retry header now fall back to the
default policy.
```

**Expected Behavior:**
The body should keep a short why, the `Closes #812` link, and the fallback for
requests without a retry header, because a reviewer needs that behavior. Tests
should summarize the coverage area in a sentence or two. The final report to
the user should include the test-first result.

It should NOT put the "meant to go in #790" note, review-fix commits, test
command, run counts, or red/green narrative in the PR body, and should NOT drop
the fallback behavior as an implementation edge case.

---

## Test: Green checks do not prove an unexercised claim

**Prompt:**
```
The build and CI are green and the preview starts. Open a draft for the settings
fix, but nobody has checked whether the saved value survives a reload.
```

**Expected Behavior:**
The response should distinguish the successful checks from the unverified
persistence claim and select validation that exercises the saved/reloaded
behavior and relevant existing behavior. If that cannot be exercised, it may
open the authorized draft with the limitation stated.

It should NOT claim the fix was verified from readiness alone or automatically
provision an environment just to publish the draft.

---

## Test: Activates for a byproduct pull request

**Prompt:**
```
Implement this small fix, push it, and send it for review.
```

**Expected Behavior:**
The response should treat the requested end state as a new pull request even
though the user did not use the words "create a PR", and should follow the
create-pr workflow before pushing the new branch and opening the PR.

It should NOT wait for an explicit `gh pr create` instruction after finishing
the code change.

---

## Test: Hands existing PR iteration to manage-pr

**Prompt:**
```
Address the comments on the PR that is already open, then wait for CI.
```

**Expected Behavior:**
The response should recognize that no new PR needs to be opened and hand the
work to `manage-pr`.

It should NOT create another branch or duplicate pull request for an
already-open PR.

---

## Test: Uses the current checkout without requiring a worktree

**Prompt:**
```
Open a PR for this change in the current repository.
```

**Expected Behavior:**
With no requested base or stack parent, the response should fetch the target
repository's default branch and use the current checkout when it is on the
intended feature branch. It should preserve user changes and any existing
implemented head. It should not require worktree creation, a sibling directory,
or a worktree-keyed session record. Worktrees remain an option.

---

## Test: Carries a release base through the complete workflow

**Prompt:**
```
Open the fix against release/1.x, not main. Main already has the fix, but the
release branch does not and has a different PR template. The next commands will
run in separate shells. The target repository is configured as upstream;
origin points to a different repository.
```

**Expected Behavior:**
The response should resolve and record the target repository, configured
remote, and `release/1.x` base. Before the gap check, it should fetch
`+refs/heads/release/1.x:refs/remotes/<remote>/release/1.x` and record the
resolved SHA. It should evaluate the gap and read the template at that SHA,
not at main or the primary checkout.

An existing completed head must be preserved.
Each shell should rebind values from the same session record, and
`gh pr create --base` and readback `baseRefName` should both be `release/1.x`.
After selecting the checkout, it should record its actual head branch,
push that branch to `upstream`, and use the same branch for `--head`. It should
not publish to `origin` or substitute a naming-convention placeholder.
It should not suppress the PR because the fix exists only on main.

---

## Test: Preserves an existing upper stack layer and its parent

**Prompt:**
```
Publish the implemented child layer. Its isolated worktree is already at the
topic/existing-child head, its agreed parent branch is topic/foundation, and that parent is
published in the target repository. Do not change the stack.
```

**Expected Behavior:**
The response should fetch and record `topic/foundation` as the base before the
gap check, preserve the existing child head/worktree, and use that parent for
the template, `--base`, and `baseRefName` readback. It should not create a new
head from the parent, reset the child, or substitute the default branch.
If the published parent was rewritten, the fetch may update its tracking ref
non-fast-forward while preserving the implemented child head.
It should record `topic/existing-child`, push that branch to the recorded target
remote, and pass `--head topic/existing-child`, not invent a new head name.
If the selected worktree is detached or is on the base branch rather than the
child branch, it should stop and report that the head needs resolution before
publishing; it must not push the base branch.

---

## Test: Fails closed when the requested base cannot be fetched

**Prompt:**
```
Open against release/missing. A same-named local branch exists, but the target
remote has no such branch and the explicit fetch fails.
```

**Expected Behavior:**
The response should stop before treating the gap as verified or publishing.
It should report the missing target base, not fall back
to the local branch, a stale tracking ref, or the repository default. An unknown
stack parent likewise needs resolution rather than a silent default.

---

## Test: Does not accept a different base in the created PR

**Prompt:**
```
The recorded target base is release/1.x, but gh pr view reports baseRefName main
after creation. The title and body are correct. Is the PR complete?
```

**Expected Behavior:**
The response should report a base mismatch rather than success and correct
the existing PR to the requested target before claiming completion. It should
not accept main merely because the body matches, or create a duplicate PR.

---

## Test: Uses the live template and preserves label markers

**Prompt:**
```
Create the PR and fill out its description.
```

**Expected Behavior:**
The response should locate and read the target repository's current pull request
template, retain its applicable headings, option text, and HTML marker comments
verbatim, and fill every applicable section. The body should be concise,
why-first, and avoid file inventories or facts the diff already shows.

It should NOT invent remembered template sections or paraphrase marker comments
that repository automation may use for labels.

---

## Test: Creates a concise commit and reports validation honestly

**Prompt:**
```
Commit the finished change and open the pull request.
```

**Expected Behavior:**
The response should create a focused commit with a lowercase sentence-fragment
subject and the required `Co-authored-by: Copilot
<223556219+Copilot@users.noreply.github.com>` trailer. It should run the
repository's available targeted validation and clearly say when local tooling
was unavailable instead of claiming tests ran.

It should NOT add a verbose commit body that merely restates the diff.

---

## Test: Reviews non-trivial changes before pushing when adversarial-review is installed

**Prompt:**
```
Open a PR for the role-scope refactor. The adversarial-review skill is
installed and ran on an earlier commit; I've since added two fix commits, and
one review candidate about prompt fall-through was left as an open question.
```

**Expected Behavior:**
Before pushing, the response should run a follow-up `adversarial-review` pass
covering the new commits on the branch diff and surface the unanswered open
question to the user, while keeping review output out of the PR body. It should
NOT require a pass for trivial prose-only edits, when `adversarial-review` is
not installed, or when the user said to skip review.

---

## Test: Defaults to draft and verifies the created body

**Prompt:**
```
Push this branch and open a PR.
```

**Expected Behavior:**
The response should push normally, open the new pull request as a **draft** by
default, use a body file for a non-trivial description, and read the PR back to
verify the intended body landed. The final report should include the PR URL,
checkout path, branch, diff size, and validation status.

The readback must include the complete body, not an opening-line preview.
A substituted body that shares the template's first three lines but differs
later must be detected and corrected before claiming success.

It should NOT force-push if the remote branch already exists, and should NOT
open a ready-for-review PR unless the user explicitly asks for a ready or open
non-draft PR.

---

## Test: Uses the actual release or stacked base throughout

**Prompt:**
```
Create a PR against release/next using the target repository's upstream remote,
not origin. Keep the already implemented topic/fix worktree and head. The next
publication commands run in separate shells.
```

**Expected Behavior:**
Fetch the explicit base with an explicit remote-tracking refspec, preserve the
existing worktree/head, and retain the same target remote and base through
creation. Rebind the repository, remote, base, checkout path and head branch from
the session record, not variables assumed to survive shell calls.
Use an explicit target-remote/head push even if pushDefault points elsewhere;
verify the published head matches the inspected commit before creating the PR.
A failed fetch must stop; do not fall back to a stale ref or repository default.

---

## Test: Resists Pre-Push Review Bloat by Simplifying

**Prompt:**
```
Open a PR for the new parser. `adversarial-review` is installed and flags an edge case in a complex fallback branch we added.
```

**Expected Behavior:**
Before pushing, the response should prefer deleting or simplifying the complex fallback branch that provoked the finding over stacking new defensive guards, compare `git diff --stat "$(git merge-base "$BASE_SHA" HEAD)"` before and after the fix round so review rounds do not bloat the PR (or stop and ask the user to approve a larger fix if a verified defect cannot be simplified to ≤15 net production lines), and re-run validation before pushing.

---

## Test: Base moves during implementation or validation

**Prompt:**
```
The target base advanced while you were implementing or validating the change.
Open the PR now.
```

**Expected Behavior:**
Refresh the actual base, retain its immutable pending SHA across shells even
when the merge stops on a conflict, merge it without
rebasing/force-pushing, and repeat affected validation after the merge. After a
successful explicit push, record the validated base/HEAD pair and any validation
limitations. Reread a changed template from that base SHA. Immediately before
creation, fetch again without overwriting the saved pair and compare to
the recorded base and HEAD; if either changed, repeat rather than creating the PR.
If base churn continues after one retry, stop and report publication blocked;
do not livelock or silently allow a stale base.
Do not introduce a large new validator or silently disable signing to progress.

---

## Test: Head changes or the final push fails

**Prompt:**
```
The refresh and validation finished, but the final push failed. In a later shell,
the worktree is on another branch at the same commit. Can you open the PR now?
```

**Expected Behavior:**
Stop rather than marking the pair as validated/published after a failed push.
Require the recorded head branch as well as its inspected commit and a clean
worktree, and verify the target remote's published head before creation.
Do not adopt a different branch, overwrite unexpected edits, or reuse a stale
session record merely because the local commit matches.

---

## Test: Conflict appears after creation

**Prompt:**
```
You just created the pull request as part of this workflow, and GitHub now
reports its mergeability as UNKNOWN or DIRTY. Is the new PR ready for me?
```

**Expected Behavior:**
Reread UNKNOWN; for CONFLICTING/DIRTY, refresh/merge the actual base,
repeat affected validation, push, and recheck the existing PR. Do not create a
second PR or claim completion while it remains conflicting. Verify body, base,
head and lifecycle; keep the intended body available until verification and any
correction succeeds. Use the same single retry budget as before creation and
report blocked or unverified if it is exhausted or UNKNOWN persists.
A conflict-free PR does not need another merge merely because the base advanced.
Leave the worktree and unrelated files untouched.

---

## Test: Checks effective CODEOWNERS at BASE_SHA when adding new files

**Prompt:**
```
Open a PR that adds a new team-owned validator script. At `BASE_SHA`, `.github/CODEOWNERS` and `docs/CODEOWNERS` both exist, and our feature branch also has local edits to `.github/CODEOWNERS`.
```

**Expected Behavior:**
The response should inspect the effective ownership file at `BASE_SHA` following GitHub's precedence order (`.github/CODEOWNERS`, root `CODEOWNERS`, then `docs/CODEOWNERS` — here `.github/CODEOWNERS` at `BASE_SHA`, not the feature branch's copy or `docs/CODEOWNERS`), and either place the new team-owned file under an existing team-owned path or include an update to `.github/CODEOWNERS` while noting that GitHub evaluates the base branch's `CODEOWNERS` for the current PR.
