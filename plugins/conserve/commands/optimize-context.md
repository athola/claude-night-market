---
name: optimize-context
description: Analyze and optimize context window usage using MECW principles
usage: /optimize-context [path]
---

# Optimize Context Usage

Analyzes context window usage and provides optimization recommendations based on Maximum Effective Context Window (MECW) principles.

## Usage

```bash
# Analyze current session context
/optimize-context

# Analyze specific skill or directory
/optimize-context skills/my-skill

# Deep analysis with recommendations
/optimize-context --detailed
```

## What It Does

1. **Context Pressure Assessment**: Evaluates current context utilization
2. **MECW Compliance Check**: Validates against MECW principles
3. **Optimization Recommendations**: Suggests specific improvements
4. **Token Budget Analysis**: Breaks down token usage by component

## MECW Thresholds

| Utilization | Status | Action |
|-------------|--------|--------|
| < 30% | Optimal | No action needed |
| 30-50% | Good | Monitor growth |
| 50-70% | Warning | Consider optimization |
| > 70% | Critical | Immediate action required |

## Examples

```bash
/optimize-context
# Output:
# Context Optimization Report
# ==========================
# Current Usage: 45% (Good)
# Estimated Tokens: 12,500
#
# Recommendations:
# - Consider extracting code examples to scripts/
# - 3 skills exceed recommended token budget

/optimize-context skills/context-optimization --detailed
# Full breakdown with per-module analysis
```

## Integration

Works with conservation plugin skills:
- `context-optimization` - Core MECW implementation
- `token-conservation` - Token reduction strategies
- `optimizing-large-skills` - Modularization patterns

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/growth_analyzer.py "${1:-.}"
```
