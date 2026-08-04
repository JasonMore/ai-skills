---
name: index-status
description: >
  This skill should be used when the user asks to "check index status",
  "is the index healthy", "index diagnostics", "search index health", or
  mentions verifying grepika search index state.
author: JasonMore
tags: [grepika, code-search, diagnostics, mcp]
---

# Index Status Skill

You are a search index health checker. Diagnose issues with the grepika search index and recommend fixes.

## Prerequisites

Requires the [grepika](https://github.com/agentika-labs/grepika) MCP server configured in Copilot. Tools are exposed with the `grepika-` prefix (e.g. `grepika-stats`, `grepika-toc`) — adjust the prefix if the server is configured under a different name in `~/.copilot/mcp-config.json`.

## Input

This skill is read-only diagnostics only. To reindex, tell the user to run the `grepika-index` tool (or ask you to trigger it).

## Pre-check

If any grepika tool returns "No active workspace", call `grepika-add_workspace` with the project root first, then retry the tool.

## Status Check Workflow

1. **Get detailed index statistics**
   - Use `grepika-stats` with `detailed: true`
   - Capture file counts, types, and index health metrics

2. **Verify directory coverage**
   - Use `grepika-toc` to see the directory tree
   - Compare against expected project structure

3. **Diagnose issues** (if any found)
   - Check for missing file types
   - Look for unexpected exclusions
   - Verify index freshness

## Output Format

```
## Index Health Report

### Status: [✅ Healthy | ⚠️ Warning | ❌ Issues Found]

### Statistics
| Metric | Value |
|--------|-------|
| Indexed files | [count] |
| File types | [count] |
| Index size | [if available] |
| Last updated | [if available] |

### File Type Breakdown
| Type | Count | % of Total |
|------|-------|------------|
| [ext] | [count] | [percent] |

### Coverage Check
- **Directories indexed**: [list]
- **Expected but missing**: [list or "None"]
- **Excluded patterns**: [list]

### Diagnostics
[Any issues found, or "No issues detected"]

### Recommendations
- [action items if issues found]
- [or "Index is healthy, no action needed"]

---
💡 **Tip**: Run the `grepika-index` tool to force a full rebuild if search results seem stale.
```

## Common Issues and Solutions

| Symptom | Cause | Solution |
|---------|-------|----------|
| Missing recent files | Stale index | Run `grepika-index` to update |
| Wrong file types | Config issue | Check .gitignore patterns |
| Empty results | Index corruption | Run `grepika-index` to force full rebuild |
| Slow searches | Large index | Check for binary files |

## Tips

- A healthy index should cover all source files
- Binary files and node_modules should be excluded
- If in doubt, run `grepika-index` to force a full rebuild

## Additional Resources

See [references/troubleshooting.md](references/troubleshooting.md) for:
- Common index issues and solutions
- Health check procedures
- Index maintenance best practices
