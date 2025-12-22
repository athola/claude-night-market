---
name: context-optimization
description: |
  Reduce context usage with MECW principles (keep under 50% of total window).

  Triggers: context pressure, token usage, MECW, context window, optimization,
  decomposition, workflow splitting, context management, token optimization

  Use when: context usage approaches 50% of window, tasks need decomposition,
  complex multi-step operations planned, context pressure is high

  DO NOT use when: simple single-step tasks with low context usage.
  DO NOT use when: already using mcp-code-execution for tool chains.

  Use this skill BEFORE starting complex tasks. Check context levels proactively.
category: conservation
token_budget: 150
progressive_loading: true
---

# Context Optimization Hub

## Quick Start

Orchestrate specialized modules for context optimization:
- **mecw-principles**: MECW theory and the 50% context rule
- **mecw-assessment**: Context analysis and risk identification
- **subagent-coordination**: Workflow decomposition and delegation

## When to Use

- **Automatic**: Keywords: `context`, `tokens`, `optimization`, `MECW`
- **MECW Threshold**: When context usage approaches 50% of total window size
- **Complex Tasks**: For tasks requiring multiple steps or detailed analysis

## Core Hub Responsibilities

1. Assess context pressure and MECW compliance
2. Route to appropriate specialized modules
3. Coordinate subagent-based workflows
4. Manage token budget allocation across modules
5. Synthesize results from modular execution

## Module Selection Strategy

```python
def select_optimal_modules(context_situation, task_complexity):
    if context_situation == "CRITICAL":
        return ['mecw-assessment', 'subagent-coordination']
    elif task_complexity == 'high':
        return ['mecw-principles', 'subagent-coordination']
    else:
        return ['mecw-assessment']
```

## Context Classification

| Utilization | Status | Action |
|-------------|--------|--------|
| < 30% | LOW | Continue normally |
| 30-50% | MODERATE | Monitor, apply principles |
| > 50% | CRITICAL | Immediate optimization required |

## Integration Points

- **Token Conservation**: Receives usage strategies, returns MECW-compliant optimizations
- **CPU/GPU Performance**: Aligns context optimization with resource constraints
- **MCP Code Execution**: Delegates complex patterns to specialized MCP modules

## Detailed Resources

For implementation details:

- **MECW Theory**: See `modules/mecw-principles.md` for core concepts and 50% rule
- **Context Analysis**: See `modules/mecw-assessment.md` for risk identification
- **Workflow Delegation**: See `modules/subagent-coordination.md` for decomposition patterns
