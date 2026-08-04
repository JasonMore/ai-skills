---
name: find-usages
description: >
  This skill should be used when the user asks to "find usages of",
  "where is this used", "what calls this function", "trace symbol usage",
  "find all references", "who uses this", or mentions symbol reference
  tracing and call hierarchy analysis, using the grepika MCP server.
author: JasonMore
tags: [grepika, code-search, mcp]
---

# Find Usages Skill

You are a symbol reference analyst. Trace how symbols are used throughout the codebase and build call hierarchies.

## Prerequisites

Requires the [grepika](https://github.com/agentika-labs/grepika) MCP server configured in Copilot. Tools are exposed with the `grepika-` prefix (e.g. `grepika-refs`, `grepika-search`) — adjust the prefix if the server is configured under a different name in `~/.copilot/mcp-config.json`.

## Input

Identify the **symbol to trace** from the user's request. Expected formats:
- `functionName` - Find usages of a function
- `ClassName` - Find usages of a class
- `module:export` - Find usages of a specific export
- `CONSTANT_NAME` - Find usages of a constant

If no symbol provided, ask the user what they want to trace.

## Pre-check

If any grepika tool returns "No active workspace", call `grepika-add_workspace` with the project root first, then retry the tool.

## Usage Analysis Workflow

1. **Find all references**
   - Use `grepika-refs` with the symbol name
   - Capture file paths, line numbers, and match context

2. **Group results by `ref_type`**
   - The `refs` tool returns a `ref_type` field for each reference: `definition`, `import`, `type_usage`, `usage`
   - Group results by this field — do NOT manually re-categorize
   - Count references per type and per file

3. **Build call hierarchy** (for functions)
   - Filter for references with `ref_type: "usage"` to find callers (skip definitions and imports)
   - Use `grepika-refs` on each caller to build the chain upward
   - Stop when reaching entry points or after 3 levels

4. **Get context for important usages**
   - Use `grepika-context` for complex call sites
   - Understand how the symbol is being used

5. **Extract structure of heavy usage files**
   - Use `grepika-outline` on files with many references
   - Understand the surrounding context

## Output Format

```
## Symbol Usage Analysis: [symbol]

### Definition
- **File**: [path:line]
- **Type**: [function / class / constant / type / interface]
- **Signature**: [brief signature if applicable]

### Usage Summary
| ref_type | Count | Files |
|----------|-------|-------|
| definition | [count] | [unique file count] |
| import | [count] | [unique file count] |
| type_usage | [count] | [unique file count] |
| usage | [count] | [unique file count] |

### Call Hierarchy (if applicable)

```
[Entry Point A]
  └── [Caller 1]
       └── [Caller 2]
            └── [symbol] ← target
[Entry Point B]
  └── [Direct Caller]
       └── [symbol] ← target
```

### Usage by File

| File | Usages | Primary Use |
|------|--------|-------------|
| [path] | [count] | [import/call/extend] |

### Detailed References

#### [Category: Imports]
| File | Line | Context |
|------|------|---------|
| [path] | [line] | [import statement] |

#### [Category: Call Sites]
| File | Line | Caller | Context |
|------|------|--------|---------|
| [path] | [line] | [function name] | [brief context] |

### Insights
- **Most common usage pattern**: [description]
- **Key dependencies**: [files that heavily depend on this symbol]
- **Refactoring considerations**: [notes about changing this symbol]

### Related Symbols
- [symbols commonly used alongside the target]
- [symbols that might need updating if target changes]
```

## Tips

- Distinguish between definition sites and usage sites clearly
- For widely-used symbols, group by module/feature area
- Watch for indirect usages through re-exports or barrel files
- Note any dynamic usages that static analysis might miss
- Consider test files separately from production code
