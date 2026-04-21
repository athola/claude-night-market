---
name: model-routing
description: >-
  Route pipeline steps to appropriate model tiers
  based on task complexity and cost efficiency.
parent_skill: egregore:summon
category: orchestration
estimated_tokens: 180
---

# Model Routing Module

Selects the appropriate model tier for each pipeline step
based on task complexity, cost efficiency, and runtime
feedback signals. Production teams overwhelmingly use
multiple models (LangChain survey: 75%+), and different
models excel at different stages. This module formalizes
that practice for egregore.

## Model Tier Definitions

| Tier | Model | Strengths | Cost |
|------|-------|-----------|------|
| Lightweight | Haiku | Fast parsing, validation, simple classification | Low |
| Standard | Sonnet | Code review, documentation, test generation | Medium |
| Deep | Opus | Architecture decisions, complex reasoning, creative work | High |

Lightweight is roughly 10x cheaper than Deep.
Standard is roughly 3x cheaper than Deep.
These ratios inform the default routing table below.

## Pipeline Step Routing

Each step has a default tier chosen by matching the
cognitive demands of the task to model strengths.

| Pipeline Stage | Step | Default Tier | Rationale |
|----------------|------|--------------|-----------|
| INTAKE | parse | Lightweight | Structured extraction, no creativity needed |
| INTAKE | validate | Lightweight | Schema validation, binary decisions |
| INTAKE | prioritize | Standard | Requires judgment but not deep reasoning |
| BUILD | brainstorm | Deep | Creative divergent thinking |
| BUILD | specify | Deep | Requirements analysis, edge case discovery |
| BUILD | blueprint | Deep | Architecture decisions, dependency ordering |
| BUILD | execute | Deep | Code generation, complex implementation |
| QUALITY | code-review | Standard | Pattern matching, rule application |
| QUALITY | unbloat | Standard | Detection and removal, not creation |
| QUALITY | code-refinement | Standard | Improvement within existing patterns |
| QUALITY | update-tests | Standard | Test generation follows implementation |
| QUALITY | update-docs | Standard | Documentation follows implementation |
| SHIP | prepare-pr | Standard | Summarization and formatting |
| SHIP | pr-review | Standard | Review against criteria |
| SHIP | fix-pr | Deep | Addressing nuanced review feedback |
| SHIP | merge | Lightweight | Mechanical merge operation |

With this routing, roughly half the pipeline runs below
Deep tier, producing an estimated 40% cost reduction
compared to running every step at Opus.

## Dynamic Tier Adjustment

The default routing table is a starting point. Four
signals can shift the tier at runtime:

1. **Step failure**: if a step fails at its default tier,
   retry at one tier higher. Lightweight becomes Standard,
   Standard becomes Deep.
2. **Reflexion buffer**: if the reflexion buffer shows
   repeated failures for the same step across work items,
   escalate directly to Deep regardless of default tier.
3. **Trust tier**: if the skill's trust tier is T3
   (autonomous), the orchestrator may downgrade one tier
   to save cost. T3 indicates the skill has proven
   reliability, so a lighter model can handle it.
4. **Manual override**: a `model_override` field in the
   manifest work item config forces a specific tier for
   any step, bypassing all other logic.

Adjustment priority (highest wins): manual override,
reflexion escalation, step failure escalation, trust
downgrade, default table.

## Cost Tracking

The orchestrator tracks token usage per step and tier
in `.egregore/model-usage.json`:

```json
{
  "wrk-001": {
    "intake/parse": {
      "tier": "haiku",
      "tokens_in": 1200,
      "tokens_out": 350
    },
    "build/execute": {
      "tier": "opus",
      "tokens_in": 45000,
      "tokens_out": 12000
    }
  }
}
```

The completion summary includes a cost efficiency report
comparing actual spend against the baseline of running
every step at Deep tier.

## Integration with Egregore Budget

The budget module already tracks token windows and rate
limits. Model routing complements it by reducing the
token spend that counts against that budget:

- Lightweight steps at Haiku consume roughly 1/10 of the
  budget that Deep steps would.
- Standard steps at Sonnet consume roughly 1/3.
- The budget module's `estimated_tokens_used` field
  should weight by tier when model routing is active.

## Agent Model Selection

When the orchestrator spawns specialist agents, each
agent uses a tier matched to its role:

| Agent | Default Tier | Rationale |
|-------|--------------|-----------|
| reviewer | Standard | Pattern matching against review criteria |
| documenter | Standard | Follows implementation, no original design |
| tester | Standard | Test generation from existing code |

Override with a `model` field in the agent's frontmatter.
If the frontmatter specifies a model, that takes
precedence over the routing table.

## Fallback Protocol

When the specified tier is unavailable (rate limit hit,
quota exhausted, API error):

1. Try one tier higher. Standard falls back to Deep.
   Lightweight falls back to Standard.
2. If the higher tier is also unavailable, try the
   remaining tier. Lightweight tries Standard, then Deep.
3. If all tiers are exhausted, queue the step for retry
   after the budget module's cooldown period.
4. Never downgrade from Deep to a lower tier on fallback.
   Deep is selected for tasks requiring that level of
   reasoning, and a weaker model risks incorrect output
   that costs more to fix than waiting for availability.

The fallback decision is recorded in the manifest via
`manifest.record_decision()` with the step, chosen
fallback tier, and the reason for the original tier's
unavailability.
