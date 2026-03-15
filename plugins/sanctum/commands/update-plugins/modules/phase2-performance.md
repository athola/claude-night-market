# Phase 2: Performance and Improvement Analysis

After registration audit completes, automatically analyze
improvement opportunities.

## Step 1: Check Skill Performance Metrics

For each plugin being updated, invoke `pensive:skill-review`
to analyze execution history:

```bash
# If updating specific plugin
pensive:skill-review --plugin <plugin-name> --recommendations

# If updating all plugins
pensive:skill-review --all-plugins --recommendations
```

Look for:

- Unstable skills (stability_gap > 0.3)
- Recent failure patterns
- Performance degradation trends
- Low success rates (< 80%)

## Step 2: Surface Recent Failures

Query skill execution logs for failures:

```bash
/skill-logs --plugin <plugin-name> --failures-only --last 7d
```

Extract:

- Common error messages
- Recurring failure patterns
- Environmental dependencies causing issues

## Step 3: Check for Workflow Improvements

1. Check if `sanctum:workflow-improvement` skill has been
   invoked recently
2. Review git history for recent fixes to
   commands/skills/agents in this plugin
3. Check issue tracker for open improvement issues

Command to check recent workflow fixes:

```bash
git log --oneline --grep="improve\|fix\|optimize" \
  --since="30 days ago" -- plugins/<plugin-name>/
```

## Step 4: Generate Improvement Recommendations

Based on Steps 1-3, create recommendations in this format:

```markdown
## Improvement Recommendations for <plugin-name>

### Critical (Immediate Action)
- [ ] Skill: <skill-name> - Stability gap: 0.45 - Review error handling
- [ ] Command: <command-name> - 5 failures in last week - Missing validation

### Moderate (Schedule for Next Sprint)
- [ ] Agent: <agent-name> - Performance degradation detected - Review token usage
- [ ] Skill: <skill-name> - Low success rate (72%) - Improve documentation

### Low Priority (Backlog)
- [ ] Hook: <hook-name> - Occasional timeouts - Add async handling
```

## Step 5: Create Action Items (Automatic)

Critical and Moderate issues are automatically logged to
GitHub issues.

For each Critical or Moderate recommendation:

1. Check for duplicates in existing issues first
2. Create GitHub issue with appropriate labels:
   - Critical: `high-priority`, `plugin:<name>`, component label
   - Moderate: `medium-priority`, `plugin:<name>`, component label
3. Report created issues to user at end of command

Low Priority items are reported but NOT auto-created
(remain in backlog documentation).

To skip automatic creation: use `--no-auto-issues` flag.

Also create TodoWrite items for immediate tracking:

```
improvement:<plugin-name>:skill-<name>-stability
improvement:<plugin-name>:command-<name>-validation
improvement:<plugin-name>:agent-<name>-performance
```
