---
name: mcp-subagents
description: Create focused, single-purpose subagents for complex workflow
  decomposition with MECW compliance.
location: plugin
token_budget: 80  # Optimized with modules
progressive_loading: true
dependencies:
  hub: [mcp-code-execution]
  modules: [mcp-patterns, mcp-coordination]
---

# MCP Subagents Module

## Quick Start
Decompose complex workflows into focused subagents that operate within MECW limits.

## Critical: Base Overhead Reality

**Every subagent inherits ~8-16k tokens of system context** (tool definitions,
permissions, system prompts) regardless of your instruction length.

### The Efficiency Formula

```
Efficiency = Task_Reasoning_Tokens / (Task_Reasoning_Tokens + Base_Overhead)
```

| Task Reasoning | + Overhead (~8k) | Efficiency | Verdict |
|---------------|------------------|------------|---------|
| 50 tokens | 8,050 | **0.6%** | ❌ Parent does it |
| 500 tokens | 8,500 | **5.9%** | ❌ Parent does it |
| 2,000 tokens | 10,000 | **20%** | ⚠️ Borderline |
| 5,000 tokens | 13,000 | **38%** | ✅ Use subagent |
| 15,000 tokens | 23,000 | **65%** | ✅ Definitely use |

**Minimum threshold**: Task should require **>2,000 tokens of reasoning** to justify subagent overhead.

## CRITICAL: Check BEFORE Invoking

**The complexity check MUST happen BEFORE calling the Task tool.**

```
❌ WRONG: Invoke subagent → Subagent bails → 8k tokens wasted
✅ RIGHT: Parent checks → Skip invocation → 0 tokens spent
```

### Pre-Invocation Checklist

Before ANY Task invocation:
1. Can I do this in one command? → Do it directly
2. Is reasoning < 500 tokens? → Do it directly
3. Check agent's ⚠️ PRE-INVOCATION CHECK in description → Follow it

## SDK MCP Tool Access Fix (Claude Code 2.1.30+)

**Critical fix**: Prior to 2.1.30, subagents could not access SDK-provided MCP tools because they were not synced to the shared application state. This meant any workflow delegating MCP tool usage to subagents was **silently broken** — the subagent would simply not have the MCP tools available.

**Now fixed**: MCP tools are properly synced across subagent boundaries. No workarounds needed.

## Sub-Agent Spawning Restrictions (Claude Code 2.1.33+)

Agent `tools` frontmatter now supports `Task(agent_type)` to restrict which sub-agents can be spawned. This provides governance over delegation chains and prevents uncontrolled spawning.

```yaml
tools:
  - Read
  - Bash
  - Task(research-agent)
  - Task(testing-agent)
```

Use for orchestrator agents that should only delegate to specific workers. Combined with the pre-invocation complexity check, this ensures both *whether* and *to whom* delegation occurs is controlled.

## When to Use
- **Automatic**: Keywords: `subagent`, `decompose`, `break down`, `modular`
- **Complex Workflows**: Multi-step processes requiring specialization
- **MECW Pressure**: When single approach would exceed 50% context rule
- **Task Specialization**: Different phases require different expertise
- **NOT for simple tasks**: Parent should execute directly if reasoning < 2k tokens

## Required TodoWrite Items
1. `mcp-subagents:analyze-complexity`
2. `mcp-subagents:create-subagents`
3. `mcp-subagents:coordinate-execution`
4. `mcp-subagents:synthesize-results`

## Subagent Design Principles

### MECW-Compliant Structure
- Each subagent operates within strict token limits (default: 125 tokens)
- Dynamic budget allocation based on task complexity
- External state management for intermediate results
- Progressive loading to minimize context pressure

See [MCP Patterns](mcp-patterns.md) for implementation examples.

## Workflow Decomposition

### Step 1 – Analyze Complexity
- Assess workflow complexity factors (tool chain length, data volume, context pressure)
- Determine optimal decomposition strategy (sequential, parallel, or single)
- Plan coordination pattern (pipeline, parallel, or direct)

### Step 2 – Create Subagents
- Use factory patterns for common subagent types
- Configure MECW-compliant token budgets
- Set up external storage for intermediate results

### Step 3 – Coordinate Execution
- Monitor context usage before each subagent
- Execute with minimal context sharing
- Store intermediate results externally

### Step 4 – Synthesize Results
- Load external results within MECW limits
- Combine results with token-aware synthesis
- Validate MECW compliance and efficiency

## Advanced Patterns

For detailed coordination patterns, code examples, and troubleshooting:
- **[Coordination Patterns](mcp-coordination.md)** - Pipeline and parallel orchestration
- **[Implementation Patterns](mcp-patterns.md)** - Factory patterns and code examples

## Success Metrics
- **Subagent Efficiency**: >90% complete within token budget
- **MECW Compliance**: 100% adherence to 50% context rule
- **Decomposition Quality**: <5% need for emergency re-decomposition
- **Synthesis Accuracy**: >95% preservation of original insights
