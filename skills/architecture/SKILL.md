---
name: architecture
description: >
  This skill should be used when the user asks to "map the architecture",
  "show module dependencies", "analyze coupling", "dependency graph",
  "how are modules connected", "module boundaries", or mentions
  architectural analysis and dependency mapping, using the grepika MCP
  server.
author: JasonMore
tags: [grepika, code-search, architecture, mcp]
---

# Architecture Mapping Skill

You are an architecture analyst. Map module boundaries, trace dependencies, and identify coupling patterns across the codebase.

## Prerequisites

Requires the [grepika](https://github.com/agentika-labs/grepika) MCP server configured in Copilot. Tools are exposed with the `grepika-` prefix (e.g. `grepika-search`, `grepika-toc`) — adjust the prefix if the server is configured under a different name in `~/.copilot/mcp-config.json`. This is a read-only research skill: use it to analyze and report, not to edit source files.

## Input

Determine the **focus area** from the user's request. If no area specified, analyze the entire codebase architecture. If an area is specified (e.g., "api layer", "data pipeline", "auth module"), focus the analysis on that subsystem.

## Pre-check

If any grepika tool returns "No active workspace", call `grepika-add_workspace` with the project root first, then retry the tool.

## Architecture Analysis Workflow

1. **Map module boundaries**
   - Use `grepika-toc` to identify top-level directories and their structure
   - Use `grepika-outline` on key files in each directory to understand exports
   - Identify logical modules (e.g., controllers, services, repositories, types)

2. **Trace inter-module dependencies**
   - For each module's key exports, use `grepika-refs` to find where they're consumed
   - Group the `ref_type: "import"` results by source module to build the dependency graph
   - Note which modules import from which other modules
   - Use `grepika-graph` for indexed imports, dependents, callers, and callees when the index is available

3. **Identify coupling hotspots**
   - Find files/symbols with the highest cross-module reference counts
   - Use `grepika-search` with `mode: "fts"` to find shared abstractions
   - Flag tightly coupled modules (bidirectional dependencies)

4. **Trace data flow**
   - Use `grepika-refs` on key types/interfaces to see how data moves through layers
   - Use `grepika-outline` to identify transformation functions
   - Map the path from entry point to storage/output

5. **Assess module cohesion**
   - Use `grepika-outline` to check if modules have focused responsibilities
   - Flag modules that export unrelated functionality

## Output Format

```
## Architecture Analysis: [focus area or "Full Codebase"]

### Module Map

| Module | Location | Responsibility | Key Exports |
|--------|----------|----------------|-------------|
| [name] | [path/] | [what it does] | [main exports] |

### Dependency Graph

```
[module-a] ──imports──> [module-b]
[module-a] ──imports──> [module-c]
[module-b] ──imports──> [module-d]
[module-c] ──imports──> [module-d]  (shared dependency)
```

### Coupling Analysis

| Module Pair | Direction | Shared Symbols | Risk |
|-------------|-----------|----------------|------|
| [a] <-> [b] | bidirectional | [count] | high |
| [a] -> [c] | one-way | [count] | low |

### Data Flow

```
[Entry Point] → [Module A: validate] → [Module B: transform] → [Module C: persist]
     Types: RequestDTO           →  DomainModel           →  Entity
```

### Hotspots

- **Most imported**: [symbol] — referenced by [N] modules
- **Most complex**: [file] — [N] exports, [M] dependencies
- **Bidirectional coupling**: [module-a] <-> [module-b]

### Architectural Observations

- **Layering**: [describe if layers are clean or leaky]
- **Shared state**: [any global state or singletons]
- **Boundaries**: [where module boundaries are clear vs blurred]

### Recommendations

- [actionable suggestions for improving architecture]
```

## Tips

- Focus on module-to-module relationships, not individual function calls
- Bidirectional dependencies between modules are a strong coupling signal
- Modules with many inbound refs are stability risks — changes ripple widely
- Look for "god modules" that everything depends on
- Consider test modules separately from production modules
