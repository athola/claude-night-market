---
name: trust-tier
description: >-
  Progressive trust system that reduces user
  checkpoints for proven skills and increases
  oversight for unreliable ones.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 200
---

# Trust Tier

## Purpose

Reduce checkpoint friction for skills that have
demonstrated competence. Trust is earned slowly through
repeated success and lost quickly on failure. This
follows the Auto MoC principle: by batch four, 95% of
fixes ran without asking permission. Experienced users
increase both autonomy and strategic interruption
(Anthropic autonomy research).

## Three Trust Tiers

| Tier | Name | Checkpoint Frequency | Qualification |
|------|------|---------------------|---------------|
| T1 | Supervised | Every phase transition | Default for all new/untracked skills |
| T2 | Guided | Critical phases only (specify, execute) | 5+ executions, >85% success rate |
| T3 | Autonomous | Start and end only | 15+ executions, >95% success rate |

## Trust Score Tracking

Track per skill in `.attune/trust-scores.json`:

```json
{
  "brainstorm": {
    "executions": 18, "successes": 17, "failures": 1,
    "tier": "T3",
    "last_promotion": "2026-03-20T14:00:00Z",
    "last_failure": "2026-02-15T10:30:00Z"
  }
}
```

**Success**: phase completed without user intervention
or rollback. **Failure**: phase required user
correction, damage-control, or rollback.

## Tier Transitions

Trust is earned slowly, lost quickly: 5 successes
to promote, 1 failure to demote.

### Promotion

Check after every successful execution:

```
function check_promotion(skill):
    record = trust_scores[skill]
    rate = record.successes / record.executions
    if record.tier == "T1"
       and record.executions >= 5
       and rate > 0.85:
        promote(skill, "T2")
    elif record.tier == "T2"
       and record.executions >= 15
       and rate > 0.95:
        promote(skill, "T3")
```

### Demotion

Immediate on any failure at T2 or T3:

```
function on_failure(skill):
    record = trust_scores[skill]
    record.failures += 1
    if record.tier == "T3":
        demote(skill, "T2")
    elif record.tier == "T2":
        demote(skill, "T1")
    # T1 stays at T1 (already maximum oversight)
```

Demotion does not reset execution counts. The skill
must re-qualify by accumulating enough successes to
restore its success rate above the threshold.

## Checkpoint Reduction Rules

| Tier | Checkpoints Shown | Checkpoints Skipped |
|------|-------------------|---------------------|
| T1 (Supervised) | All per phase-routing protocol | None |
| T2 (Guided) | specify, execute | brainstorm, plan |
| T3 (Autonomous) | Mission start (confirm intent), mission end (review results) | All intermediate phases |

The `--auto` flag overrides all tiers to T3 behavior.
This is the existing feature from phase-routing; trust
tiers provide the same outcome without the global flag.

## Integration with Phase Routing

Phase-routing step 5 (User Checkpoint) consults the
trust tier before presenting a checkpoint:

```
function should_checkpoint(phase, skill):
    tier = trust_scores[skill].tier

    # Safety checkpoints always fire (see below)
    if is_safety_checkpoint(phase):
        return true

    if tier == "T1":
        return true
    elif tier == "T2":
        return phase in ["specify", "execute"]
    elif tier == "T3":
        return false  # start/end handled by orchestrator
```

When the tier allows skipping, the orchestrator logs
the checkpoint data (for auditability) but does not
pause for user input. When the tier requires it,
the checkpoint presents as normal.

## Strategic Interruption

Even at T3, certain events always trigger a checkpoint
regardless of trust tier. Trust reduces routine
checkpoints, not safety checkpoints.

**Always-checkpoint events:**

- Destructive operations: file deletion, force push,
  branch reset
- External-facing actions: PR creation, issue comments,
  release tagging
- Scope expansion: adding features not in the original
  plan or specification
- Cost thresholds: operations exceeding estimated
  token/time budgets

```
function is_safety_checkpoint(phase_context):
    return (phase_context.has_destructive_ops
         or phase_context.has_external_actions
         or phase_context.scope_expanded
         or phase_context.budget_exceeded)
```

## State and Dashboard

Storage: `.attune/trust-scores.json` (alongside mission
state). The orchestrator reads scores at mission start
and writes updates after each phase. Scores persist
across missions; they track long-term skill reliability,
not single-mission state. If the file does not exist,
all skills default to T1.

For `/attune:status`, display current trust tiers:

```
Trust Tiers:
  T3 (Autonomous): brainstorm, specify [15+ runs, 97%]
  T2 (Guided):     plan, execute [8 runs, 88%]
  T1 (Supervised): new-skill [0 runs]
```
