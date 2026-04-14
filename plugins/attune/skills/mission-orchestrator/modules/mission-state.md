---
name: mission-state
description: Mission state schema, persistence to .attune/mission-state.json, and recovery protocol
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 200
---

# Mission State

## State Schema

```json
{
  "mission_id": "mission-20260207-220000",
  "type": "tactical",
  "started_at": "2026-02-07T22:00:00Z",
  "updated_at": "2026-02-07T23:30:00Z",
  "status": "in_progress",
  "phases": {
    "brainstorm": {
      "status": "skipped",
      "reason": "Not in mission type 'tactical'"
    },
    "specify": {
      "status": "skipped",
      "reason": "Not in mission type 'tactical'"
    },
    "plan": {
      "status": "completed",
      "started_at": "2026-02-07T22:00:00Z",
      "completed_at": "2026-02-07T22:45:00Z",
      "artifact": "docs/implementation-plan.md",
      "notes": "Generated 24 tasks across 5 phases"
    },
    "execute": {
      "status": "in_progress",
      "started_at": "2026-02-07T22:50:00Z",
      "completed_at": null,
      "artifact": ".attune/execution-state.json",
      "notes": "12/24 tasks complete"
    }
  },
  "risk_summary": {
    "GREEN": 18,
    "YELLOW": 4,
    "RED": 2,
    "CRITICAL": 0
  },
  "errors": [
    {
      "phase": "execute",
      "task_id": "T015",
      "error": "Test timeout on integration suite",
      "category": "TRANSIENT",
      "recovery": "Retried successfully",
      "resolved": true
    }
  ],
  "user_decisions": [
    {
      "checkpoint": "plan → execute",
      "decision": "continue",
      "timestamp": "2026-02-07T22:48:00Z"
    }
  ],
  "plan_review": {
    "current_round": 2,
    "max_rounds": 3,
    "status": "in_review",
    "versions": [
      {
        "version": 1,
        "created_at": "2026-04-13T14:00:00Z",
        "path": ".attune/plan-history/plan-v1.md",
        "feedback_path": ".attune/plan-history/feedback/round-1.json",
        "overall_verdict": "revision_requested"
      },
      {
        "version": 2,
        "created_at": "2026-04-13T14:30:00Z",
        "path": ".attune/plan-history/plan-v2.md",
        "feedback_path": null,
        "overall_verdict": null
      }
    ],
    "war_room_verdict": null,
    "bias_findings_count": 3
  }
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `mission_id` | string | Unique ID: `mission-{YYYYMMDD}-{HHMMSS}` |
| `type` | string | Mission type: `full`, `standard`, `tactical`, `quickfix` |
| `started_at` | ISO 8601 | Mission start timestamp |
| `updated_at` | ISO 8601 | Last state update timestamp |
| `status` | string | `in_progress`, `completed`, `paused`, `aborted`, `failed` |
| `phases` | object | Per-phase status, timestamps, artifacts |
| `risk_summary` | object | Count of tasks per risk tier |
| `errors` | array | Errors encountered during execution |
| `user_decisions` | array | User checkpoint decisions |
| `plan_review` | object | Interactive review loop state |
| `plan_review.current_round` | int | Current review round (1-3) |
| `plan_review.max_rounds` | int | Maximum rounds (default 3) |
| `plan_review.status` | string | `in_review`, `approved`, `war_room_pending` |
| `plan_review.versions` | array | Per-version metadata |
| `plan_review.war_room_verdict` | string or null | `approved`, `concerns`, `rejected` |
| `plan_review.bias_findings_count` | int | Number of additive bias findings |

## Persistence

State is persisted to `.attune/mission-state.json`:

- **Write frequency**: After each phase completion and on error
- **Atomic write**: Uses temp file + rename pattern to prevent corruption
- **Directory creation**: Creates `.attune/` if it doesn't exist

```bash
# State file location
.attune/mission-state.json
```

## Recovery Protocol

When resuming a mission (`/attune:mission --resume`):

### Step 1: Load State

```
Read .attune/mission-state.json
If not found: No mission to resume, start fresh
If found: Parse and validate
```

### Step 2: Validate Artifacts

For each completed phase, verify its artifact still exists on disk:

```
For each phase where status == "completed":
    Check artifact path exists
    If missing: Mark phase as "needs_rerun"
    If present: Confirm still valid (quality checks)
```

### Step 3: Continue from Last Completed Phase

```
Find first phase where status != "completed" and status != "skipped"
If "in_progress": Resume this phase
If "pending": Start this phase
If all complete: Mission already done
```

### Step 4: Display Resume Summary

```
Resuming Mission: mission-20260207-220000
  Type: tactical
  Status: in_progress

  Phase Status:
    plan:    completed (22:00 - 22:45)
    execute: in_progress (12/24 tasks, started 22:50)

  Continuing from: execute phase
  Next task: T013
```

## State Transitions

```
           start
             |
             v
        in_progress ──────► completed
             |
             ├──► paused (--resume to continue)
             |
             ├──► aborted (user choice)
             |
             └──► failed (unrecoverable error)
```

- `paused → in_progress`: Via `--resume`
- `failed → in_progress`: Via `--resume --force` (resets failed phase)
- `aborted`: Terminal state (start new mission to retry)

### Plan Review Status Transitions

```
plan_review.status:
    pending --> in_review (first section presented)
    in_review --> approved (all sections approved)
    in_review --> revision_requested (any section rejected/revised)
    approved --> war_room_pending (war room invoked)
    war_room_pending --> approved (war room approves)
    war_room_pending --> revision_requested (war room rejects)
    revision_requested --> in_review (next round starts)
```
