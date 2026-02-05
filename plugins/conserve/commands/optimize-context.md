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

## Headless Mode (Non-Interactive)

For reading context in headless/automated Claude Code sessions:

```bash
# Get context breakdown with JSON output
claude -p "run /context" --verbose --output-format json

# Two-call pattern for reliable execution
# (Claude doesn't always execute /context on first prompt)
SESSION_ID=$(claude -p "ready" --output-format json | jq -r '.session_id')
claude --continue "$SESSION_ID" -p "/context" --verbose --output-format json
```

**Key flags:**
- `--verbose`: Includes categorical token breakdown
- `--output-format json`: Machine-parseable output
- `--continue`: Resumes existing session for reliable command execution

**Example JSON output:**
```json
{
  "context": {
    "total_tokens": 45000,
    "usage_percent": 22.5,
    "breakdown": {
      "system": 8000,
      "conversation": 32000,
      "tools": 5000
    }
  }
}
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
