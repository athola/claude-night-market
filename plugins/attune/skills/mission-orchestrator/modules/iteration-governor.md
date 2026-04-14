---
name: iteration-governor
description: >-
  Track review rounds (max 3), warn at round 2,
  force decision at round 3 exhaustion with
  escalation options.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 150
---

# Iteration Governor

## Purpose

Prevent infinite plan-churn by capping review
iterations at 3 rounds. If the plan is still not
satisfactory after 3 rounds, the problem is likely
upstream in the specification.

## Round Tracking

| Round | Status | User Sees |
|-------|--------|-----------|
| 1 | Normal | "Round 1/3" in review header |
| 2 | Warning | "Round 2/3 -- next round is final" |
| 3 | Final | "Final round (3/3)" |
| 3 exhausted | Forced decision | Escalation options |

## War Room Feedback Counts

War-room feedback that triggers a revision counts
toward the iteration cap. If the user approves on
round 2 but the war room sends it back, that revision
is round 3 (final).

Example:
- Round 1: User reviews, requests revision
- Round 2: User approves, war room rejects
- Round 3: Final revision, then forced decision

## Escalation at Cap

When round 3 is exhausted (user or war room still not
satisfied), present these options:

```
Round 3 exhausted. The plan has been revised 3 times.

Options:
  [A] Approve current version as-is
  [B] Abort mission
  [C] Restart planning from specification
      (re-invoke Skill(attune:project-planning)
       with clean slate, no revision context)
```

Option C resets the iteration counter to 0 and starts
fresh. The previous plan history is preserved for
reference but not fed as context.

## Round 2 Warning

At the start of round 2 review, display:

```
--- Warning: Round 2 of 3 ---
This is the penultimate review round.
Round 3 will be the final opportunity to revise.
After round 3, you must approve, abort, or restart.
-----------------------------------------
```

## State Integration

The governor reads and writes `plan_review.current_round`
in `.attune/mission-state.json`. See mission-state
module for the schema.

## Governor Logic

```
function check_iteration(current_round):
    if current_round > 3:
        present_escalation_options()
        return BLOCKED
    elif current_round == 3:
        display "Final round (3/3)"
        return FINAL
    elif current_round == 2:
        display round 2 warning
        return WARNING
    else:
        return NORMAL
```
