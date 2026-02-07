---
name: fix-workflow
description: Retrospective analysis and improvement of workflow components with self-evolving patterns
usage: /fix-workflow [--scope sanctum|repo] [--dry-run] [--focus skills|agents|commands|hooks|all] [--difficulty auto|simple|complex]
---

# Fix Workflow

Run a lightweight retrospective on the **most recent command or session slice** visible in the current context window, then implement targeted improvements to the workflow components involved (skills, agents, commands, hooks).

## When To Use

Use this command when you need to:
- Workflow execution felt inefficient or needs optimization
- Post-session improvement of skills/agents/commands/hooks

## When NOT To Use

- Simple changes that don't need the full workflow
- Work already completed through another sanctum command

## Self-Improvement Architecture

This command implements research-backed self-improvement patterns:

| Pattern | Purpose | When Applied |
|---------|---------|--------------|
| **Reflexion** | Self-critique before applying fixes | Phase 1.5 (after analysis) |
| **PDCA Loops** | Plan-Do-Check-Act validation | Each phase transition |
| **Difficulty-Aware** | Adjust depth based on complexity | Phase 0 (auto-detected) |
| **Outcome Feedback** | Learn from validation results | Phase 2 (close loop) |

## Usage

```text
/fix-workflow [--scope sanctum|repo] [--dry-run] [--focus skills|agents|commands|hooks|all] [--difficulty auto|simple|complex]
```

- `--scope sanctum|repo`: Default `sanctum`. If `repo`, improvements may touch non-plugin code and project docs/tests as needed.
- `--dry-run`: Produce an improvement plan without making changes.
- `--focus`: Default `all`. Limit to a component type to keep the change set small.
- `--difficulty auto|simple|complex`: Default `auto`. Controls orchestration depth:
  - `simple`: Single-pass improvement (1-2 files, clear fix)
  - `complex`: Full PDCA cycle with reflexion (multi-file, architectural)
  - `auto`: Detect from workflow complexity score

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

### Phase 1.5: Reflexion (Self-Critique Loop)

Before implementing, the agent evaluates its own improvement plan:

#### Reflexion Checklist

```markdown
## Self-Critique Questions

1. **Root Cause**: Does this fix address the root cause or just symptoms?
   - [ ] Verified root cause in Phase 0 data
   - [ ] Fix targets cause, not effect

2. **Unintended Consequences**: Could this improvement break something else?
   - [ ] Checked dependent workflows
   - [ ] Reviewed similar past fixes for side effects

3. **Reversibility**: Can this be easily rolled back?
   - [ ] Changes are incremental
   - [ ] No destructive modifications

4. **Recurrence Prevention**: Will this prevent future similar issues?
   - [ ] Addresses pattern, not just instance
   - [ ] Adds guardrails for detection
```

#### Difficulty-Aware Orchestration

Based on complexity score from Phase 0:

| Score | Difficulty | Orchestration |
|-------|------------|---------------|
| 1-3 | Simple | Skip reflexion, direct implement |
| 4-6 | Medium | Quick reflexion (2 questions) |
| 7-10 | Complex | Full reflexion + PDCA cycle |

**Complexity Score Factors:**
- Files affected (1 point per file)
- Cross-plugin changes (+2 points)
- Architectural changes (+3 points)
- Prior failures in component (+1 per failure)

5. **Implement the improvements (Plan-Do-Check-Act):**
   - **Plan**: Review reflexion output, confirm approach
   - **Do**: Use `workflow-improvement-implementer-agent` to apply changes
   - **Check**: Run immediate validation (syntax, lint, unit tests)
   - **Act**: If check fails, iterate on implementation

6. **Validate the improvement is substantive:**
   - Use `workflow-improvement-validator-agent` to run targeted tests/validators and re-run a minimal reproduction of the workflow
   - **Compare metrics** before/after using skill-logs data

### Phase 2: Outcome Feedback Loop

After validation, capture outcomes for self-evolution:

#### 2.1: Record Improvement Outcome

```bash
# Store outcome in skill execution history
/skill-logs add --skill sanctum:fix-workflow \
  --outcome "success|partial|failed" \
  --metrics '{"files_changed": N, "complexity": M, "validation_passed": true}'
```

#### 2.2: Update Component Stability Scores

For each component modified:
- **Success**: Decrease stability_gap by 0.1 (improved confidence)
- **Partial**: No change (neutral outcome)
- **Failed**: Increase stability_gap by 0.2 (requires attention)

#### 2.3: Feed Forward to Future Runs

Capture lessons for future `/fix-workflow` invocations:

```markdown
## Outcome Record

**Improvement ID**: fix-workflow-2026-01-13-001
**Complexity Score**: 5 (Medium)
**Reflexion Applied**: Yes (2 questions)
**Outcome**: Success

**Lessons Learned**:
- Pattern: "Early validation prevents cascading failures"
- Applied To: workflow-improvement skill, Step 2

**Feedback to Agents**:
- workflow-recreate-agent: Add validation checkpoint reminder
- workflow-planner-agent: Prioritize guardrail improvements
```

This feedback informs:
- Phase 0 context gathering (similar patterns)
- Difficulty scoring (prior outcomes)
- Agent behavior (learned preferences)

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
