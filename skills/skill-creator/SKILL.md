---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
license: Apache-2.0; see LICENSE.txt
---

# Skill Creator

Create, review, and improve skills through tests and feedback.

## Load the upstream guide

Read [the upstream guide](references/upstream-guide.md) before using this skill.
It contains the full workflow and is preserved without changes.
Paths in that guide are relative to this skill's root, not `references/`.

For an existing draft, start with its test and improvement steps.
Use the conversation to identify the goal, current feedback, and expected behavior.
Ask only for decisions that the conversation does not resolve.

## Review principles

- Keep instructions short. Remove rules that do not improve the result.
- Explain why a rule matters instead of adding broad prohibitions.
- Generalize from failures. Do not tailor a skill to one example.
- Test both the intended behavior and valid exceptions.
- Read test outputs and transcripts before drawing conclusions.

Follow the upstream guide for paired runs, grading, the review viewer, and iteration.
Do not report a behavior test as passed based only on a text or format check.

## Resources

- [Grader](agents/grader.md): check assertions against test outputs.
- [Comparator](agents/comparator.md): compare outputs without version labels.
- [Analyzer](agents/analyzer.md): find patterns and explain differences.
- [Schemas](references/schemas.md): test, grade, and benchmark formats.
- `scripts/quick_validate.py`: check skill structure and frontmatter.
- `scripts/aggregate_benchmark.py`: combine graded test runs.
- `eval-viewer/generate_review.py`: create the results viewer.

## Source and local changes

Source: [anthropics/skills, skill-creator](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/skill-creator).
License: [Apache 2.0](LICENSE.txt).

Local adaptation: replaced the long entry point with this short guide to meet this
repository's 200-line limit. The original entry point is in
`references/upstream-guide.md`. All other upstream files remain unchanged.
