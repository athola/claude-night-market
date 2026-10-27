---
name: skill-review
description: Analyze skill execution metrics and identify unstable or underperforming skills.
---

# Skill Performance Review

Analyze skill execution metrics and identify unstable or underperforming skills using continual learning analysis.

## Usage

```bash
/skill-review                          # Show all skill metrics
/skill-review --all-plugins            # Aggregate by plugin
/skill-review --skill <plugin:skill>   # Specific skill deep-dive
/skill-review --unstable-only          # Only skills with stability_gap > 0.3
/skill-review --top <n>                # Top N by execution count
/skill-review --recommendations        # Get improvement recommendations
```

## What It Analyzes

### Continual Learning Metrics

For each skill, calculates:

| Metric | Description |
|--------|-------------|
| **Execution Count** | Total invocations |
| **Success Rate** | Percentage of successful executions |
| **Average Duration** | Mean execution time |
| **Worst Window Rate** | Lowest success rate over any 5 consecutive runs |
| **Stability Gap** | `1 - worst_window_rate` |

### Stability Gap (Key Metric)

The stability gap measures the worst stretch of a skill's history. Each
run is a pass (1) or a fail (0). The success rate is taken over every
window of 5 consecutive runs, and the gap is the worst window's shortfall
from perfect:

```
stability_gap = 1 - min(success rate of each 5-run window)
```

One failure in a window costs 0.2, so the gap moves in steps of 0.2 and
the 0.2 - 0.3 band below holds exactly one failure. The gap is 0.0 until a
skill has 5 runs. The definition lives in
`plugins/abstract/hooks/shared/stability.py`.

**Interpretation:**
- ✓ **< 0.2**: Stable - consistent performance
- ⚠️ **0.2 - 0.3**: Warning - occasional issues
- ✗ **> 0.3**: Unstable - needs attention

**Why it matters**: An average hides a bad stretch. A skill that passes
94% of the time overall but failed 3 runs in a row has a worst window of
0.4 and a gap of 0.6.

## Examples

### View All Metrics

```bash
/skill-review
```

Output:
```
Skill Performance Review
========================

abstract:skill-auditor:
  Executions: 47
  Success rate: 94%
  Average duration: 134ms
  Worst 5-run window: 1.00
  Stability gap: 0.00 ✓ (stable)

sanctum:pr-review:
  Executions: 23
  Success rate: 91%
  Average duration: 2.1s
  Worst 5-run window: 0.80
  Stability gap: 0.20 (monitoring)

imbue:proof-of-work:
  Executions: 31
  Success rate: 68%
  Average duration: 1.8s
  Worst 5-run window: 0.60
  Stability gap: 0.40 ⚠️ (unstable)
```

### Find Unstable Skills

```bash
/skill-review --unstable-only
```

Output:
```
Skills with Stability Gap > 0.3
================================

imbue:proof-of-work
  Stability gap: 0.40
  Issue: High failure rate (32%)
  Suggestion: Review recent failures with /memory-palace:skill-logs --skill imbue:proof-of-work --failures-only

your-custom:my-skill
  Stability gap: 0.60
  Issue: Inconsistent performance
  Suggestion: Check error patterns in execution logs
```

### Deep-Dive Specific Skill

```bash
/skill-review --skill abstract:skill-auditor
```

Output:
```
Skill Analysis: abstract:skill-auditor
======================================

Summary:
  Total executions: 47
  First seen: 2025-01-01
  Last used: 2025-01-08

Performance:
  Success rate: 94% (44/47)
  Average duration: 134ms
  Median duration: 128ms
  95th percentile: 245ms

Stability:
  Worst 5-run window: 1.00
  Stability gap: 0.00 ✓
  Trend: Improving (last 10: 100% success)

Recent Failures (3):
  2025-01-05: "Skill file not found"
  2025-01-03: "Invalid frontmatter format"
  2025-01-02: "Timeout exceeded"

Recommendation: HEALTHY - No action needed
```

### By Plugin

```bash
/skill-review --all-plugins
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

memory-palace:
  Skills tracked: 6
  Total executions: 423
  Avg success rate: 95%
  Skills with issues: 0
```

### Get Recommendations

```bash
/skill-review --recommendations
```

Output:
```
Skill Improvement Recommendations
=================================

CRITICAL (stability_gap > 0.5):
  None

NEEDS ATTENTION (stability_gap > 0.3):
  imbue:proof-of-work
    - Review last 5 failures for common patterns
    - Consider adding input validation
    - Check for environmental dependencies

MONITORING (stability_gap 0.2 - 0.3):
  conjure:delegation-core
    - Performance variance detected
    - Consider caching or optimization

HEALTHY (stability_gap < 0.2):
  45 skills performing well
```

## Integration

### Data Source

Reads from metrics written by abstract's `skill_execution_logger.py` hook:

- **Logs**: `~/.claude/skills/logs/*/*/*.jsonl`
- **History**: `~/.claude/skills/logs/.history.json`

Skip entries whose `context.session_id` starts with `test-`, `dogfood-`
or `fixture-`, the same rule as `_is_synthetic_session` in
`plugins/abstract/scripts/aggregate_skill_logs.py`. Test runs once wrote
71 `test-session` entries into the real store and made
`abstract:skill-auditor` read as 41% successful when it had no real runs.
`.history.json` carries no session ids, so a skill whose history
disagrees with its filtered logs has synthetic runs in its history.

### Related Commands

| Command | Plugin | Description |
|---------|--------|-------------|
| `skill-logs` | sanctum | View raw execution history and failures |
| `skill-review` | pensive | Analyze metrics and stability (this command) |
| `skill-history` | pensive | Recent executions with context |
| `skill-auditor` | abstract | Deep skill quality analysis (static) |

## Output Formats

Default: Markdown with color-coded indicators
JSON: Add `--format json` for programmatic access

## Implementation

Uses the continual evaluation approach from Avalanche (ICLR 2023) to detect:
1. **Accuracy degradation**: Skills getting worse over time
2. **Stability issues**: Skills with high variance
3. **Performance regressions**: Duration increases

This enables proactive skill improvement before users notice problems.
