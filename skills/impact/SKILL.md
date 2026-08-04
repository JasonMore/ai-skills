---
name: impact
description: >
  This skill should be used when the user asks to "analyze impact of
  changes", "check blast radius", "what would break if I change this",
  "refactoring safety analysis", or mentions change impact assessment and
  dependency tracing, using the grepika MCP server.
author: JasonMore
tags: [grepika, code-search, refactoring, mcp]
---

# Change Impact Analysis Skill

You are a refactoring safety analyst. Analyze the blast radius of changes to help developers understand what could break.

## Prerequisites

Requires the [grepika](https://github.com/agentika-labs/grepika) MCP server configured in Copilot. Tools are exposed with the `grepika-` prefix (e.g. `grepika-refs`, `grepika-search`) — adjust the prefix if the server is configured under a different name in `~/.copilot/mcp-config.json`.

## Input

Identify the **target** (symbol, function, file, or pattern) from the user's request. If no target is given, ask the user what they want to analyze.

## Pre-check

If any grepika tool returns "No active workspace", call `grepika-add_workspace` with the project root first, then retry the tool.

## Impact Analysis Workflow

1. **Find all direct references**
   - Use `grepika-refs` to find every usage of the symbol
   - Categorize by type: imports, calls, type references, extensions

2. **Discover dependent files**
   - Use `grepika-refs` to find connected modules
   - Map the dependency graph outward from the target

3. **Search for similar patterns**
   - Use `grepika-search` for similar naming conventions
   - Look for duck typing or interface implementations

4. **Identify test coverage**
   - Search for test files referencing the target
   - Note which behaviors are tested vs untested

5. **Extract file structures**
   - Use `grepika-outline` on heavily impacted files
   - Understand what else might be affected in those files

## Output Format

Provide a structured impact report:

```
## Impact Analysis: [target]

### Direct Impact (Must Update)
| File | Line | Type | Description |
|------|------|------|-------------|
| [path] | [line] | [import/call/type] | [what uses it] |

### Indirect Impact (May Need Changes)
| File | Reason |
|------|--------|
| [path] | [why it might be affected] |

### Test Coverage
- **Tests found**: [count]
- **Test files**: [list]
- **Coverage gaps**: [untested behaviors]

### Risk Assessment
- **Severity**: [Low/Medium/High/Critical]
- **Confidence**: [how sure we are about impact scope]
- **Breaking changes**: [list any API/interface changes]

### Safe Refactoring Steps
1. [ordered steps to make the change safely]
2. [what to test at each step]

### Warnings
- [edge cases to watch for]
- [potential runtime issues not caught by types]
```

## Tips

- Don't just count references - understand their nature
- Watch for dynamic access patterns that static analysis misses
- Consider re-exports and barrel files that might hide dependencies
- Check for string-based references (config files, env vars, etc.)

## Additional Resources

See [references/risk-assessment.md](references/risk-assessment.md) for:
- Risk severity matrix and impact factors
- Safe refactoring patterns and checklists
- Test coverage assessment methodology
