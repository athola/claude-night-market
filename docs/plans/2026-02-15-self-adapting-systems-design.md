# Self-Adapting System Design: Homeostatic Skill Health + Experience Library

**Date**: 2026-02-15
**Status**: Implemented
**Branch**: skill-atrophy-1.4.3

## User Decisions

- **Priority**: Composition > Autonomy > Accuracy
- **Focus**: Abstract + Memory-Palace plugins
- **Oversight**: Fully autonomous with human-gated rollback
- **Approach**: HYBRID - Homeostatic Skill Health (Approach 1) + Experience Library (Approach 3)

---

## Section 1: Architecture Overview

The hybrid system has 6 components forming a closed loop:

```
Skill Execution -> PostToolUse Hook (Homeostatic Monitor)
  -> Checks stability gap from memory-palace metrics
  -> If gap > 0.3: queue skill for improvement
  -> If 3+ flags: Auto-Improvement Trigger spawns skill-improver agent
  -> Skill-improver reads LEARNINGS.md + execution logs
  -> Generates improvement with versioned YAML frontmatter
  -> Re-evaluation Timer monitors next 10 executions
  -> If regression: FLAG FOR HUMAN REVIEW (create GitHub issue)
  -> If improvement: promote and store trajectory in Experience Library
  -> Experience Library feeds successful patterns back into future skill context
```

### Cross-plugin data flow

- **Memory-Palace**: provides stability metrics, stores experience library
- **Abstract**: provides skill-improver agent, execution logging, LEARNINGS.md
- **Integration point**: new `homeostatic_monitor.py` hook bridges both plugins

---

## Section 2: Homeostatic Monitor Hook

- **Type**: PostToolUse hook in Abstract plugin
- **Triggers**: after every Skill tool invocation
- **Reads**: stability gap from memory-palace's `.history.json`
- **Thresholds**:
  - gap > 0.3 = "degrading"
  - gap > 0.5 = "critical"
- **Maintains queue file**: `~/.claude/skills/improvement-queue.json`
- **Queue entry schema**:
  ```json
  {
    "skill_name": "example-skill",
    "stability_gap": 0.42,
    "flagged_count": 3,
    "last_flagged": "2026-02-15T04:00:00Z",
    "execution_ids": ["exec-001", "exec-002", "exec-003"]
  }
  ```
- **Trigger rule**: when `flagged_count >= 3`, emit improvement trigger event

---

## Section 3: Auto-Improvement Trigger

- Reads `improvement-queue.json`
- Filters skills with `flagged_count >= 3`
- For each qualifying skill, spawns `abstract:skill-improver` agent with specific context:
  - LEARNINGS.md data for that skill
  - Recent execution logs (last 30 days)
  - Current stability metrics
  - Previous improvement history (to avoid re-applying failed fixes)
- Runs as background Task agent
- Captures improvement proposal before applying

---

## Section 4: Versioned Skill Definitions

Each skill's YAML frontmatter gets new fields:

```yaml
adaptation:
  version_history:
    - version: "1.0.0"
      timestamp: "2026-02-15T04:00:00Z"
      baseline_metrics: {success_rate: 0.85, stability_gap: 0.15}
    - version: "1.1.0"
      timestamp: "2026-02-16T10:00:00Z"
      change_summary: "Added error handling for missing files"
      baseline_metrics: {success_rate: 0.92, stability_gap: 0.08}
  rollback_available: true
  current_version: "1.1.0"
```

- Git commit for each version change with conventional commit message
- Rollback = git revert of the improvement commit + frontmatter update

---

## Section 5: Re-evaluation Timer (Human-Gated Rollback)

After an improvement is applied, the system enters a monitored evaluation window.

### Evaluation window

- **Window size**: next 10 executions after improvement
- **Tracked in** `improvement-queue.json`:
  ```json
  {
    "evaluating": true,
    "eval_start": "2026-02-16T10:00:00Z",
    "eval_executions": 0,
    "eval_target": 10,
    "status": "evaluating"
  }
  ```

### Decision logic after 10 executions

| Condition | Action |
|---|---|
| `new_gap < baseline_gap` | **PROMOTE** -- mark improvement as successful, store trajectory in Experience Library |
| `new_gap >= baseline_gap` (regression) | **FLAG FOR HUMAN REVIEW** -- do NOT auto-rollback |
| `new_gap == baseline_gap` (no change) | **FLAG FOR HUMAN REVIEW** -- keep deployed but request human decision |

### Human-gated rollback process (revision from original design)

When regression is detected, the system does NOT auto-rollback. Instead:

1. **Create a GitHub issue** with the following details:
   - Skill name
   - Before metrics (baseline version)
   - After metrics (current version)
   - Improvement diff (what changed)
   - Rollback command (ready to copy-paste)
   - Label: `skill-regression`

2. **Mark in `improvement-queue.json`**:
   ```json
   {
     "status": "pending_rollback_review",
     "regression_detected": "2026-02-17T08:00:00Z",
     "github_issue": "#210",
     "baseline_gap": 0.15,
     "current_gap": 0.35,
     "rollback_command": "git revert abc123 && ..."
   }
   ```

3. **Human decides**: review the issue, then either:
   - Execute the rollback command provided in the issue
   - Close the issue if the regression is acceptable or transient
   - Request further investigation

### Rationale

Auto-rollback can discard improvements that appear regressive in the short term but are beneficial long-term (e.g., a skill that handles more edge cases may initially show a wider stability gap before settling). Human judgment is essential for this decision.

### Post-evaluation

- Store evaluation result in LEARNINGS.md for future reference regardless of outcome

---

## Section 6: Experience Library

- **Location**: `~/.claude/skills/experience-library/`
- **Structure**: `{skill_name}/{task_hash}.json`
- **Each entry**:
  ```json
  {
    "task_description": "Generate API documentation from OpenAPI spec",
    "approach_taken": "Used jinja2 templates with structured extraction",
    "outcome": "success",
    "duration_ms": 4200,
    "tools_used": ["Read", "Write", "Bash"],
    "key_decisions": ["Template-based over freeform generation"]
  }
  ```
- **Populated from**: successful skill executions (outcome=success, duration < 2x average)
- **Retrieved via**: similarity matching on task description (simple keyword overlap, not vector DB)
- **Injected into**: skill context as "Similar past successes" section (max 3 exemplars)
- **Pruning**: keep top 20 entries per skill by recency + success rate
- **Size budget**: max 500 tokens per exemplar injection

---

## Section 7: Testing Strategy

| Test Type | Target | What It Verifies |
|---|---|---|
| Unit | `homeostatic_monitor.py` | Mock stability gap data, verify queue behavior |
| Unit | Versioned skill definitions | YAML parsing, version increment, rollback |
| Integration | Degrading skill flow | Simulate degrading skill -> verify auto-improvement trigger fires |
| Integration | Regression detection | Simulate improvement regression -> verify GitHub issue creation + `pending_rollback_review` status (NOT auto-rollback) |
| Integration | Experience library | Storage and retrieval of execution trajectories |
| End-to-end | Full loop | Run skill 15 times with declining success -> verify full loop completes |

### Existing test infrastructure

- `plugins/sanctum/tests/test_continuous_improvement.py`
- `plugins/abstract/tests/scripts/skills_eval/test_improvement_suggester.py`

---

## Sources

- Memory-Palace stability metrics: `plugins/memory-palace/` (.history.json format)
- Abstract skill-improver agent: `plugins/abstract/` (LEARNINGS.md, execution logs)
- Existing continuous improvement tests: `plugins/sanctum/tests/test_continuous_improvement.py`
- Existing improvement suggester: `plugins/abstract/tests/scripts/skills_eval/test_improvement_suggester.py`
