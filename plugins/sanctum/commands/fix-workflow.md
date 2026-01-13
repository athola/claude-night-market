---
name: fix-workflow
description: Retrospective analysis and improvement of workflow components
usage: /fix-workflow [--scope sanctum|repo] [--dry-run] [--focus skills|agents|commands|hooks|all]
---

# Fix Workflow

<identification>
triggers: fix workflow, workflow improvement, retrospective, session analysis

use_when:
- Workflow execution felt inefficient or needs optimization
- Post-session improvement of skills/agents/commands/hooks
</identification>

Run a lightweight retrospective on the **most recent command or session slice** visible in the current context window, then implement targeted improvements to the workflow components involved (skills, agents, commands, hooks).

## Usage

```text
/fix-workflow [--scope sanctum|repo] [--dry-run] [--focus skills|agents|commands|hooks|all]
```

- `--scope sanctum|repo`: Default `sanctum`. If `repo`, improvements may touch non-plugin code and project docs/tests as needed.
- `--dry-run`: Produce an improvement plan without making changes.
- `--focus`: Default `all`. Limit to a component type to keep the change set small.

## Workflow

### Phase 0: Gather Improvement Context (Automatic)

Before starting retrospective analysis, automatically gather existing improvement data:

#### Step 0.1: Check Skill Execution Metrics

Identify performance issues in workflow components:

```bash
# Get recent skill executions (last 7 days)
/skill-logs --last 7d --format json > /tmp/recent-skills.json

# Check for failures in workflow components
/skill-logs --failures-only --last 7d
```

**Extract:**
- Skills that failed during the workflow slice
- Skills with high stability_gap (> 0.3) indicating instability
- Common error patterns
- Performance degradation signals

#### Step 0.2: Query Memory Palace for Lessons

Check if similar workflow issues have been captured:

```bash
# Search review-chamber for workflow-related lessons
# (If memory-palace commands are available)
/review-room search "workflow" --room lessons --limit 5
/review-room search "efficiency" --room patterns --limit 5
```

**Look for:**
- Previously identified workflow inefficiencies
- Patterns from past PR reviews
- Architectural decisions affecting workflows

#### Step 0.3: Check Recent Git History

Look for recent fixes to workflow components:

```bash
# Find recent improvements to the workflow components
git log --oneline --grep="improve\|fix\|optimize\|refactor" --since="30 days ago" \
  -- plugins/sanctum/skills/ plugins/sanctum/commands/ plugins/sanctum/agents/

# Check if similar workflows were fixed recently
git log -p --since="30 days ago" --grep="workflow" -- plugins/sanctum/
```

**Identify:**
- Recurring issues that keep getting fixed
- Components with frequent changes (instability signals)
- Patterns in fix commit messages

### Phase 1: Retrospective Analysis

1. **Capture the target slice and key evidence:**
   - Load workflow-improvement skill: `Skill(sanctum:workflow-improvement)` or read `plugins/sanctum/skills/workflow-improvement/SKILL.md`
   - **Include Phase 0 findings** as additional context

2. **Recreate the workflow and surface inefficiencies:**
   - Use `workflow-recreate-agent` to restate the steps, identify friction, and list involved components
   - **Cross-reference with Phase 0 data** to identify recurring patterns

3. **Analyze improvement options:**
   - Use `workflow-improvement-analysis-agent` to generate candidate improvements with trade-offs and expected impact
   - **Prioritize fixes** for components with high failure rates or stability gaps

4. **Plan collaboratively (converge on a small, high-use patch):**
   - Use `workflow-improvement-planner-agent` to choose the best approach, define acceptance criteria, and assign work
   - **Create TodoWrite items** referencing Phase 0 metrics

5. **Implement the improvements:**
   - Use `workflow-improvement-implementer-agent` to apply code/doc changes, keeping diffs focused and reversible

6. **Validate the improvement is substantive:**
   - Use `workflow-improvement-validator-agent` to run targeted tests/validators and re-run a minimal reproduction of the workflow
   - **Compare metrics** before/after using skill-logs data

## Output

Conclude with:

### Phase 0 Summary
- **Skill Failures**: List of skills that failed recently with frequency
- **Memory Palace Lessons**: Relevant patterns/lessons from review-chamber
- **Git History Insights**: Recurring issues identified in commit history

### Retrospective Summary
- **Workflow Slice**: The reconstructed workflow (1 screen max)
- **Improvements Applied**: Per-file changes with before/after metrics
- **Validation Evidence**: Commands run + results showing improvement
- **Follow-ups**: Deferred items with TodoWrite references

### Metrics Comparison

Before:
```
- Step count: 15
- Tool calls: 23
- Failures: 3
- Duration: 8.5 minutes
```

After:
```
- Step count: 11 (-4 steps, -27%)
- Tool calls: 17 (-6 calls, -26%)
- Failures: 0 (-3 failures, -100%)
- Duration: 5.2 minutes (-3.3 min, -39%)
```
