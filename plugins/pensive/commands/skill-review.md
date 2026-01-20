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
| **Worst-Case Accuracy** | Lowest accuracy in execution history |
| **Stability Gap** | `average_accuracy - worst_case_accuracy` |

### Stability Gap (Key Metric)

The stability gap detects inconsistent skills - those that work sometimes but fail unpredictably:

```
stability_gap = average_accuracy - worst_case_accuracy
```

**Interpretation:**
- ✓ **< 0.2**: Stable - consistent performance
- ⚠️ **0.2 - 0.3**: Warning - occasional issues
- ✗ **> 0.3**: Unstable - needs attention

**Why it matters**: Traditional metrics only measure average performance. Stability gap catches skills that are "usually fine but sometimes catastrophically wrong."

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
/skill-review --unstable-only
```

Output:
```
Skills with Stability Gap > 0.3
================================

imbue:proof-of-work
  Stability gap: 0.38
  Issue: High failure rate (32%)
  Suggestion: Review recent failures with /memory-palace:skill-logs --skill imbue:proof-of-work --failures-only

your-custom:my-skill
  Stability gap: 0.45
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
  Worst-case accuracy: 0.85
  Stability gap: 0.09 ✓
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
  conjure:template-engine
    - Performance variance detected
    - Consider caching or optimization

HEALTHY (stability_gap < 0.2):
  45 skills performing well
```

## Integration

### Data Source

Reads from metrics stored by memory-palace:
- **Logs**: `~/.claude/skills/logs/*/*/*.jsonl`
- **History**: `~/.claude/skills/logs/.history.json`

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
