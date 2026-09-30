# Meeting todos

Use the daily todo convention from
[Update Daily Snippet](../../update-daily-snippet/SKILL.md).
This phase collects meeting tasks only. Do not run calendar capture, work
logging, or prior-week task carryover.

## Read the requested dates

Read the handwritten weekly snippet and its linked meeting-date sections.
Also read any matching note sections processed by Meeting Notes in this run.
Include existing summaries when their source marker caused summary insertion
to be skipped. New summaries planned in memory count as sources in a dry run.

Use the [shared date rules](../../calendar-notes/references/date-sections.md).
Ignore fenced code. A date section ends at the next date heading, not a topic
heading. Do not collect tasks from older dates outside the requested range.
An empty section has no tasks. Report missing or duplicate date headings.
Use other notes in the requested range and existing work-log entries to check
completion. Do not treat an unchecked box as proof that a task is still open.
Use work logs only as status evidence, not as another source of todos.

## Select tasks

- Collect open checkboxes from handwritten notes, Action Items, and Follow-up
  Items in the matching date section.
- Include tasks owned by Jason or `@JasonMore`, and shared tasks that name
  Jason as an owner. Keep unowned open checkboxes without adding an owner.
- Use explicit source context to resolve owners. Generated speaker labels are
  not proof of identity. Report unclear shared assignments instead of guessing.
- Convert a plain follow-up to a checkbox only when it states a concrete task
  and explicitly assigns it to Jason. Keep the wording; add only `- [ ]`.
- Skip completed checkboxes, tasks assigned only to others, blank placeholders,
  general discussion, unresolved questions, and tasks confirmed done or obsolete.
  A partially finished task remains open; do not silently discard it.

## Preserve and deduplicate

Copy each task's text exactly. Keep case, spelling, punctuation, links, owner
text, indentation, and checkbox syntax. Preserve source order and source group
labels that contain selected tasks. Do not create topic groups or add owners.

Check the whole destination weekly snippet before adding a task, not just the
destination day's list. Normalize whitespace and case for comparison only.
Compare task text, linked targets, and owners. A shared URL alone does not make
different tasks duplicates. An existing open or completed copy blocks another
copy. Keep existing text; do not move a task from Tuesday to Wednesday.

When source candidates duplicate each other, keep the newest source version
exactly. Preserve source order for the remaining tasks. A repeat run adds
nothing unless there is a new task.

## Destination

Use `## 🤖 Todos` under the meeting's day in its handwritten weekly snippet.
Reuse an existing section. Append missing tasks after its existing content,
before the next heading. Create the section only when tasks need to be added.
Use the existing day-heading convention. Do not move calendar or user notes.
Leave the final `# todo` section unchanged.

Use the snippet's week range to map dates to day headings. If the week file or
day mapping is unclear, ask rather than create a guessed destination.

## Preview and persistence

A dry run reads sources and builds a plan in memory. It changes no vault files
or vault Git state. Show the exact proposed task text, destination date, and
source link. Report skipped items and missing-source coverage. Do not call
`persist-work-notes` or leave a preview file unless the user asks for one.

In a normal run, include changed handwritten snippets with changed summary
notes in the skill's single `persist-work-notes` call. A skipped summary can
still produce a todo-only change. Return no-op only when neither phase changes
anything.
