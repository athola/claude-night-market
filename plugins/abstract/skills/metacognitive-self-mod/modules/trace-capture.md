---
name: trace-capture
description: >-
  Execution trace recording for continuous
  learning. Captures tool sequences, decision
  points, and outcome attribution.
parent_skill: abstract:metacognitive-self-mod
category: self-improvement
tags: [traces, execution-recording, attribution, continuous-learning]
dependencies: [metacognitive-self-mod]
estimated_tokens: 200
---

# Execution Trace Capture

Record execution traces so that metacognitive-self-mod
can analyze concrete decision sequences, not just
aggregate metrics. Inspired by Microsoft Trace
(AutoDiff-like backward propagation through execution
traces), Trajectory-Informed Memory Generation (arXiv
2603.10600, decision attribution from trajectories),
and the ACE framework (evolving playbooks via
generation, reflection, and curation).

## Trace Structure

Each trace captures a single skill invocation from start
to finish.

```json
{
  "trace_id": "session-{date}-{hash}",
  "skill": "attune:project-execution",
  "started": "2026-04-14T10:30:00Z",
  "completed": "2026-04-14T10:32:15Z",
  "outcome": "success",
  "capture_mode": "decision-only",
  "steps": [
    {
      "tool": "Read",
      "target": "src/main.py",
      "purpose": "understand entry point",
      "result": "success",
      "tokens_used": 1200,
      "decision_point": false
    },
    {
      "tool": "Edit",
      "target": "src/main.py:45",
      "purpose": "add error handling",
      "result": "success",
      "tokens_used": 800,
      "decision_point": true,
      "alternatives_considered": [
        "try/except",
        "result type",
        "assertion"
      ],
      "rationale": "try/except matches existing patterns"
    }
  ],
  "attribution": {
    "success_factors": [
      "followed existing patterns",
      "tested incrementally"
    ],
    "failure_factors": [],
    "key_decisions": [
      "chose try/except over result type at step 4"
    ]
  }
}
```

## Capture Modes

Not every invocation needs a full trace. Three modes
control the recording fidelity.

| Mode | Records | When to use |
|------|---------|-------------|
| `minimal` | Outcome and duration only | High-trust T3 skills |
| `decision-only` | Decision points, outcome, duration | Default for all skills |
| `full` | Every tool call, token counts, all fields | Skills with <85% success rate |

**Mode selection logic:**

- Default: `decision-only` (captures rationale without
  flooding storage).
- Enable `full` with `--trace=full` or automatically for
  any skill whose rolling success rate falls below 85%.
- Use `minimal` for T3 skills that consistently succeed
  and need only aggregate trend data.

## What to Capture

- **Tool calls** (full mode only): tool name, target,
  purpose, result, approximate tokens consumed.
- **Decision points** (all modes except minimal):
  alternatives considered (2-5), rationale for the
  chosen option, whether later revised.
- **Trace completion** (all modes): overall outcome
  (`success`/`failure`/`partial`), wall-clock duration,
  total tokens consumed.

## Attribution Analysis

After a trace completes, run backward attribution to
identify which decisions drove the outcome. This follows
the Microsoft Trace principle of propagating feedback
backward through the execution path.

**For successful traces:**

1. Identify decisions that aligned with known success
   patterns (from `improvement_memory.json`).
2. Flag novel successful patterns as candidate hypotheses.
3. Record `success_factors` in the trace's `attribution`
   block.

**For failed traces:**

1. Walk backward from the failure point.
2. Identify the earliest decision that diverged from
   known-good patterns.
3. Record `failure_factors` and the specific decision.
4. Generate a causal hypothesis for ImprovementMemory:

```python
memory.record_insight(
    skill_ref=trace["skill"],
    category="causal_hypothesis",
    insight="Failure correlated with choosing X over Y",
    evidence=[f"trace:{trace['trace_id']}"]
)
```

**Cross-trace pattern detection:**

When 5 or more traces exist for a skill, scan for
recurring decision-outcome correlations:

- Decisions that appear in >70% of successful traces
  become "recommended patterns."
- Decisions that appear in >50% of failed traces become
  "anti-patterns."

## Storage

| Location | Contents | Retention |
|----------|----------|-----------|
| `~/.claude/skills/traces/` | Raw JSON trace files | Rolling 30-day window |
| `improvement_memory.json` | Aggregate patterns and hypotheses | Persistent |

**Budget:** Maximum 100 trace files, FIFO eviction.
Traces linked to active causal hypotheses are protected
until the hypothesis is resolved. File naming:
`{trace_id}.json` (one file per trace).

## Integration Points

- **metacognitive-self-mod** (parent): consumes traces
  during periodic analysis (Step 3) to inspect specific
  decisions behind success or failure.
- **skill-improver**: queries traces for a target skill
  before proposing changes. Targets recurring failure
  points directly.
- **friction-detector**: cross-references friction signals
  with trace data to pinpoint where a workflow broke.

## Lightweight by Default

The default `decision-only` mode records only branching
points (typically 3-8 entries per trace vs 20-50 for
full mode). Additional storage hygiene:

- Prune full-mode traces older than 7 days down to
  decision-only.
- Cap `alternatives_considered` at 5 entries.
- Omit `tokens_used` in minimal mode.
