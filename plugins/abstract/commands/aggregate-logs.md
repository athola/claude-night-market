# Aggregate Skill Execution Logs

Generate LEARNINGS.md from skill execution logs.

## Usage

```bash
/abstract:aggregate-logs                    # Last 30 days (default)
/abstract:aggregate-logs --days 7           # Last 7 days
/abstract:aggregate-logs --days 90          # Last 90 days
```

## Purpose

Part of Issue #69 Phase 3, this command processes skill execution logs to generate actionable insights for skill improvement.

## What It Does

1. **Loads logs** from `~/.claude/skills/logs/<plugin>/<skill>/`
2. **Calculates metrics** for each skill:
   - Execution count, success rate
   - Average/max duration
   - Average user rating (from evaluations)
   - Common friction points
   - Improvement suggestions
3. **Detects patterns**:
   - High failure rates (>30%)
   - Slow execution (>10s average)
   - Low ratings (<3.5/5.0)
4. **Generates LEARNINGS.md** at `~/.claude/skills/LEARNINGS.md`

## Output Format

### LEARNINGS.md Structure

```markdown
# Skill Performance Learnings

**Last Updated**: 2026-01-08 04:30:00 UTC
**Analysis Period**: Last 30 days
**Skills Analyzed**: 15
**Total Executions**: 342

## High-Impact Issues

### imbue:proof-of-work
**Type**: high_failure_rate
**Severity**: high
**Metric**: 42.3% success rate
**Detail**: 11/26 failures
**Recent Errors**:
- ValidationError: Missing acceptance_criteria field
- FileNotFoundError: PROOF.md not found
- KeyError: 'evidence' in evaluation

## Slow Execution

| Skill | Avg Duration | Max Duration | Executions |
|-------|--------------|--------------|------------|
| `sanctum:pr-agent` | 45.2s | 120.5s | 18 |
| `pensive:code-reviewer` | 32.1s | 89.3s | 24 |

## Low User Ratings

### abstract:skill-auditor - 2.8/5.0
**Common Friction**:
- Too verbose output
- Missing examples for modular skills
- Unclear token optimization guidance

**Improvement Suggestions**:
- Add --quiet flag
- Include example audits
- Link to token optimization docs

## Skill Performance Summary

| Skill | Executions | Success Rate | Avg Duration | Rating |
|-------|------------|--------------|--------------|--------|
| `imbue:proof-of-work` | 26 | 42.3% | 2.1s | 3.2/5.0 |
| `sanctum:pr-agent` | 18 | 94.4% | 45.2s | 4.5/5.0 |
```

## Examples

### Weekly Rollup

```bash
# Run every Monday morning
/abstract:aggregate-logs --days 7

# Output:
# Aggregating logs from last 7 days...
#
# ✅ LEARNINGS.md generated: ~/.claude/skills/LEARNINGS.md
#
# Summary:
#   Skills Analyzed: 8
#   Total Executions: 47
#   High-Impact Issues: 2
#   Slow Skills: 1
#   Low-Rated Skills: 1
```

### Full History Analysis

```bash
/abstract:aggregate-logs --days 90

# Analyzes last 3 months of data
```

## Integration

**Phase 2** (Evaluation):
- Reads `qualitative_evaluation` field from logs
- Calculates average ratings
- Aggregates friction points and suggestions

**Phase 4** (/fix-workflow):
- `/fix-workflow` reads LEARNINGS.md
- Surfaces known issues before manual analysis
- Prioritizes improvements by frequency × impact

**Phase 5** (/improve-skills):
- Uses LEARNINGS.md to identify improvement opportunities
- Prioritizes by severity (high-impact issues first)
- Tracks improvements over time (version comparison)

**Phase 6a** (Collective Intelligence):
- After LEARNINGS.md is generated, posts a summary to athola/claude-night-market Discussions
- Check opt-out: reads `~/.claude/skills/discussions/config.json`
- If `auto_post_learnings` is `true` (default), runs `post_learnings_to_discussions.py`
- Reports: "Posted learning summary to Discussions: {url}"
- Skips silently if `gh` is not authenticated or network is unavailable

## Automation

### Cron Job (Optional)

```bash
# Add to crontab for weekly rollup
0 9 * * MON cd /path/to/claude-night-market && ./plugins/abstract/scripts/aggregate_skill_logs.py 7
```

### Manual Workflow

```bash
# After evaluating several skills:
/abstract:evaluate-skill proof-of-work
/abstract:evaluate-skill code-reviewer
/abstract:aggregate-logs

# Review LEARNINGS.md
cat ~/.claude/skills/LEARNINGS.md

# Act on insights
/abstract:improve-skills  # Phase 5
```

## Metrics Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Success Rate | <80% | <70% |
| Avg Duration | >5s | >10s |
| User Rating | <4.0 | <3.5 |
| Failure Count | >5 | >10 |

## Performance

- **Runtime**: ~1-2s for 30 days of data (hundreds of executions)
- **Memory**: Loads one skill's logs at a time (streaming)
- **Disk**: LEARNINGS.md typically <50KB

## Related

- `/abstract:evaluate-skill` - Capture qualitative feedback (Phase 2)
- `/abstract:improve-skills` - Act on insights (Phase 5)
- `/abstract:promote-discussions` - Promote highly-voted learnings to Issues (Phase 6c)
- `Skill(abstract:skill-execution-logger)` - Raw data capture (Phase 1)

## Version

1.1.0 (Phase 6a integration)
