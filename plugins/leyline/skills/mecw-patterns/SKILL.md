---
name: mecw-patterns
description: |
  MECW theory and patterns for hallucination prevention via context management. Implements 50% rule.

  Triggers: MECW, context window, hallucination, 50% rule, context pressure
  Use when: implementing context-aware systems or monitoring context pressure
category: infrastructure
tags: [context-management, mecw, hallucination-prevention, token-optimization, thresholds]
dependencies: []
tools: [mecw-monitor, context-tracker]
provides:
  infrastructure: [context-monitoring, mecw-compliance, pressure-calculation]
  patterns: [context-optimization, safe-budgeting, hallucination-prevention]
usage_patterns:
  - context-window-management
  - hallucination-prevention
  - token-budget-planning
  - pressure-monitoring
complexity: intermediate
estimated_tokens: 350
progressive_loading: true
modules:
  - modules/mecw-theory.md
  - modules/monitoring-patterns.md
  - modules/prevention-strategies.md
reusable_by: [conserve, abstract, conjure, spec-kit, sanctum, imbue]
---

# MECW Patterns

## Overview

Maximum Effective Context Window (MECW) patterns provide the theoretical foundations and practical utilities for managing context window usage to prevent hallucinations. The core principle: **Never use more than 50% of total context window for input content.**

## When to Use

- Need to prevent hallucinations in long-running sessions
- Managing context-heavy workflows
- Building systems that process large amounts of data
- Want proactive context pressure monitoring
- Require safe token budget calculation

## Core Principle: The 50% Rule

Context pressure increases non-linearly as usage approaches limits. Exceeding 50% of context window significantly increases hallucination risk.

### Pressure Levels

| Level | Usage | Effect | Action |
|-------|-------|--------|--------|
| **LOW** | <30% | Optimal performance, high accuracy | Continue normally |
| **MODERATE** | 30-50% | Good performance, within MECW | Monitor closely |
| **HIGH** | 50-70% | Degraded performance, risk zone | Optimize immediately |
| **CRITICAL** | >70% | Severe degradation, high hallucination | Reset context |

## Quick Start

### Basic Pressure Check

```python
from leyline import calculate_context_pressure

pressure = calculate_context_pressure(
    current_tokens=80000,
    max_tokens=200000
)
print(pressure)  # "MODERATE"
```

### Full Compliance Check

```python
from leyline import check_mecw_compliance

result = check_mecw_compliance(
    current_tokens=120000,
    max_tokens=200000
)

if not result['compliant']:
    print(f"Overage: {result['overage']:,} tokens")
    print(f"Action: {result['action']}")
```

### Continuous Monitoring

```python
from leyline import MECWMonitor

monitor = MECWMonitor(max_context=200000)

# Track usage throughout session
monitor.track_usage(80000)
status = monitor.get_status()

if status.warnings:
    for warning in status.warnings:
        print(f"[WARN] {warning}")

if status.recommendations:
    print("\nRecommended actions:")
    for rec in status.recommendations:
        print(f"  • {rec}")
```

## Detailed Topics

For detailed implementation patterns:

- **[MECW Theory](modules/mecw-theory.md)** - Theoretical foundations, research basis, thresholds
- **[Monitoring Patterns](modules/monitoring-patterns.md)** - Integration patterns, quota management, token estimation
- **[Prevention Strategies](modules/prevention-strategies.md)** - Early detection, compression, delegation, progressive disclosure

## Best Practices

1. **Plan for 40%**: Design workflows to use ~40% of context, leaving buffer
2. **Buffer for Response**: Leave 50% for model reasoning + response generation
3. **Monitor Continuously**: Check context at each major step
4. **Fail Fast**: Abort and restructure when approaching limits
5. **Document Aggressively**: Keep summaries for context recovery after reset

## Integration with Other Skills

This skill provides foundational utilities referenced by:
- `conserve:context-optimization` - Uses MECW for optimization decisions
- `conjure:delegation-core` - Uses MECW for delegation triggers
- Plugin authors building context-aware systems

Reference in your skill's frontmatter:
```yaml
dependencies: [leyline:mecw-patterns]
```

## Exit Criteria

- Context pressure monitored before major operations
- MECW compliance checked when loading large content
- Safe budget calculated before batch operations
- Recommendations followed when warnings issued
- Context reset triggered before CRITICAL threshold
