---
name: context-optimizer
description: |
  Autonomous agent for context window optimization and MECW compliance.

  Triggers: context audit, MECW compliance, token optimization, skill optimization,
  context analysis, growth monitoring, context health check

  Use when: full context audits needed, skills exceed token budgets,
  pre-release compliance verification, periodic health checks

  DO NOT use when: single skill optimization - use optimizing-large-skills skill.
  DO NOT use when: quick token counts - use skills-eval instead.
tools: [Read, Glob, Grep, Bash, Write]
model: haiku
escalation:
  to: sonnet
  hints:
    - ambiguous_input
    - high_stakes
---

# Context Optimizer Agent

Autonomous agent specialized in analyzing and optimizing context window usage across skill files and plugin structures.

## Capabilities

- **Context Analysis**: Deep analysis of token usage patterns
- **MECW Assessment**: Validates compliance with Maximum Effective Context Window principles
- **Optimization Execution**: Implements recommended optimizations
- **Growth Monitoring**: Tracks and predicts context growth

## When to Use

Dispatch this agent for:
- Full context audits across large skill collections
- Automated optimization of skills exceeding token budgets
- Pre-release context compliance verification
- Periodic health checks of plugin context efficiency

## Agent Workflow

1. **Discovery**: Find all SKILL.md files in target directory
2. **Analysis**: Calculate token usage and growth patterns for each
3. **Assessment**: Evaluate against MECW thresholds
4. **Recommendations**: Generate prioritized optimization suggestions
5. **Reporting**: Produce detailed context health report

## Example Dispatch

```
Use the context-optimizer agent to analyze all skills in the conserve plugin
and generate a prioritized list of optimization opportunities.
```

## Output Format

The agent produces a structured report including:
- Summary statistics (total files, total tokens, average per file)
- Skills exceeding thresholds with specific recommendations
- Growth trajectory predictions
- Suggested modularization opportunities

## Integration

This agent uses tools from:
- `scripts/growth-analyzer.py` - Growth pattern analysis
- `scripts/growth-controller.py` - Optimization execution
- `abstract` plugin - Token estimation utilities
