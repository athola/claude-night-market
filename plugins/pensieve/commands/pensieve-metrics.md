# View Continual Learning Metrics

Display continual learning metrics for all tracked skills.

## Usage

```bash
/observability:metrics                    # Show all metrics
/observability:metrics --all-plugins      # Aggregate by plugin
/observability:metrics --skill <name>     # Specific skill
/observability:metrics --unstable-only    # Only skills with stability_gap > 0.3
/observability:metrics --top <n>          # Top N by execution count
```

## Examples

### View All Metrics

```bash
/observability:metrics
```

Output:
```
Continual Learning Metrics
==========================

abstract:skill-auditor:
  Executions: 47
  Success rate: 94%
  Average duration: 134ms
  Worst-case accuracy: 0.85
  Stability gap: 0.09 ✓ (stable)

sanctum:pr-review:
  Executions: 23
  Success rate: 91%
  Average duration: 2.1s
  Worst-case accuracy: 0.82
  Stability gap: 0.09 ✓ (stable)

imbue:proof-of-work:
  Executions: 31
  Success rate: 68%
  Average duration: 1.8s
  Worst-case accuracy: 0.40
  Stability gap: 0.38 ⚠️ (unstable)
```

### Find Unstable Skills

```bash
/observability:metrics --unstable-only
```

Output:
```
Skills with Stability Gap > 0.3
================================

imbue:proof-of-work
  Stability gap: 0.38
  Issue: High failure rate (32%)
  Suggestion: /abstract:improve-skills --skill imbue:proof-of-work

your-custom:my-skill
  Stability gap: 0.45
  Issue: Inconsistent performance
  Suggestion: Review error messages in logs
```

### By Plugin

```bash
/observability:metrics --all-plugins
```

Output:
```
Metrics by Plugin
=================

abstract:
  Skills tracked: 12
  Total executions: 1,234
  Avg success rate: 92%
  Skills with issues: 2

sanctum:
  Skills tracked: 8
  Total executions: 856
  Avg success rate: 89%
  Skills with issues: 1
```

## Implementation

Reads from: `~/.claude/skills/logs/.history.json`

Formats metrics as Markdown tables with color coding:
- ✓ Green: Stable (gap < 0.2)
- ⚠️ Yellow: Warning (gap 0.2-0.3)
- ✗ Red: Unstable (gap > 0.3)
