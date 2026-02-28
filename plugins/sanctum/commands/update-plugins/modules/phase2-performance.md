# Phase 2: Performance and Improvement Analysis

After registration audit completes, automatically analyze improvement opportunities.

## Step 1: Check Skill Performance Metrics

For each plugin being updated, invoke `pensive:skill-review` to analyze execution history:

```bash
pensive:skill-review --plugin <plugin-name> --recommendations
pensive:skill-review --all-plugins --recommendations
```

Look for:
- Unstable skills (stability_gap > 0.3)
- Recent failure patterns
- Performance degradation trends
- Low success rates (< 80%)

## Step 2: Surface Recent Failures

```bash
/skill-logs --plugin <plugin-name> --failures-only --last 7d
```

Extract common error messages, recurring failure patterns, and environmental issues.

## Step 3: Check for Workflow Improvements

1. Check if `sanctum:workflow-improvement` skill has been invoked recently
2. Review git history for recent fixes
3. Check issue tracker for open improvement issues

## Step 4: Generate Improvement Recommendations

Create concrete recommendations grouped by severity (Critical, Moderate, Low Priority).

## Step 5: Create Action Items

Critical and Moderate issues are automatically logged to GitHub issues. Also create TodoWrite items for immediate tracking. Use `--no-auto-issues` to skip automatic creation.
