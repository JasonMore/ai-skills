# Evaluations

## Dual sources

**Given:** Same PR appears in current handwritten notes and current work log.
Prior sources contain a related todo. The user is the PR author.

**Expect:** Read all five inputs. List the PR once. Include the todo only when
it became complete in the reporting window.

## PR author

**Given:** GitHub confirms the user authored a candidate PR but is not assigned.

**Expect:** Allow the PR in Key Ships & Accomplishments.

## PR assignee

**Given:** Another person authored a candidate PR. GitHub lists the user among
its assignees.

**Expect:** Allow the PR in Key Ships & Accomplishments.

## Author and assignee

**Given:** The user is both author and assignee. The login case differs
between the user response and the PR response.

**Expect:** Match logins without case sensitivity. List the PR once.

## Reviewed or team PR

**Given:** The user reviewed, discussed, or recorded a teammate's PR.
The user is neither its author nor an assignee.

**Expect:** Exclude the PR from Key Ships & Accomplishments, including inline
references. Other sections can cite it when relevant.

## Missing ownership evidence

**Given:** The user's GitHub login or a candidate PR's author and assignees
cannot be fetched.

**Expect:** Flag the missing evidence. Omit the PR from Key Ships &
Accomplishments until ownership is verified. Do not infer ownership from notes.

## Conflict

**Given:** Handwritten prose says a PR merged. Work log has a later correction
that says closed unmerged.

**Expect:** Use the correction, flag the conflict, and omit any merged claim.

## Stale status

**Given:** A dated entry says CI is running. GitHub now shows the PR merged.

**Expect:** Flag the old status as stale. Keep the activity date. Use current
status only if the final prose needs a status.

## PR link lists

**Given:** The draft cites several PRs across Ships and other sections.

**Expect:** Put every PR link in an unordered list. Each item contains one bare
PR URL and the activity day in parentheses. Do not put PR links in prose,
tables, or comma-separated groups. Keep the ownership filter for Ships.

## Final write

**Given:** User approves the draft.

**Expect:** Append only to the current handwritten file. Keep drafts and daily
content. Persist that one exact file.
