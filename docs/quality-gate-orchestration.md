# Quality-Gate Orchestration Map

## Why this document exists

Commit `02fa8948` documented the gate federation in
`docs/quality-gates.md#skill-level-quality-gate-
composition`. That work showed which skills are gates and
how they relate. This document closes the next gap:
**which skill is allowed to compose them, and in what
order**.

Without an explicit orchestrator, every consumer (sanctum,
attune, scribe, abstract) cherry-picks individual gates.
The federation exists in code -- 18 outbound references
from `imbue:karpathy-principles` -- but never runs as a
coherent sequence at the marketplace level. One gate
(`imbue:vow-enforcement`) has zero `Skill()` callers in
prose despite being the third layer of the imbue
constraint system.

This doc proposes `egregore:quality-gate` as the canonical
orchestrator and gives the recommended composition order.

## The current state

### Documented gates

From `docs/quality-gates.md#skill-level-quality-gate-
composition`:

- `imbue:rigorous-reasoning` -- anti-sycophancy reasoning
  checklist; runs before any conflict analysis or
  contested decision.
- `imbue:scope-guard` -- worthiness scoring and branch
  budget enforcement; runs before implementation
  proposals.
- `imbue:karpathy-principles` -- four-principle
  pre-implementation gate (think first, simplicity,
  surgical edits, verification).
- `imbue:proof-of-work` -- evidence and validation gate;
  runs before claiming work is complete.
- `imbue:justify` -- post-implementation audit against
  minimal-intervention discipline.
- `imbue:vow-enforcement` -- three-layer constraint
  classifier (soft / hard / Nen Court).
- `leyline:additive-bias-defense` -- inverts the burden of
  proof for additions; runs alongside scope-guard.
- `imbue:karpathy-check` (slash command) -- preflight gate
  combining the above.

### Who currently orchestrates

Of the 23 plugins, exactly one ships an orchestrator that
sequences gates: `egregore:quality-gate` runs convention
checks and routes through review skills as part of its
QUALITY pipeline stage.

Other plugins reference individual gates:

| Caller | Gates invoked | Sequence |
|--------|---------------|----------|
| `sanctum:pr-review` | proof-of-work, scope-guard | parallel, ad-hoc |
| `attune:project-execution` | proof-of-work, scope-guard | per-task |
| `scribe:session-to-post` | proof-of-work | once at end |
| `abstract:bulletproof-skill` | rigorous-reasoning | once before refactor |

No caller invokes the full federation in the order the
gate authors intended. `imbue:vow-enforcement` is invoked
nowhere in skill prose -- it only fires through hook
paths (`imbue/hooks/vow_*.py`).

## The composition order (recommended)

When a workflow needs the full constraint stack, run gates
in this order:

```
1. imbue:rigorous-reasoning      (clarify the question)
2. imbue:scope-guard             (worthiness gate)
   + leyline:additive-bias-defense (parallel; same gate)
3. imbue:karpathy-principles     (pre-implementation gate)
4. <implementation>
5. imbue:proof-of-work           (evidence gate)
6. imbue:justify                 (post-implementation audit)
7. imbue:vow-enforcement         (constraint classification)
```

Steps 1-3 run before any code changes; 4 is the
implementation; 5-7 run before the work is declared
complete. The order matters: rigorous-reasoning shapes
the question before scope-guard scores it, and
karpathy-principles requires a question that's already
been clarified and scoped.

## Proposed canonical orchestrator

`egregore:quality-gate` is the right home for this
sequence because:

- It already orchestrates the QUALITY pipeline stage in
  egregore.
- It already declares routing tables for review skills
  per step.
- It runs in both self-review and PR-review modes, so the
  same orchestration applies whether you're gating your
  own work or someone else's.
- It is invoked from `egregore:summon` as part of the
  development lifecycle, so adding the federation gives
  every autonomous mission the same gate discipline.

### Integration path for `imbue:vow-enforcement`

The skill is currently a hook target (read by
`imbue/hooks/vow_*.py`) but has no Skill() entry path.
The orchestration should add it as the final step of the
QUALITY stage:

```yaml
# in plugins/egregore/skills/quality-gate/SKILL.md routing
- step: vow-classification
  conventions:
    - hard-vow-violations-blocked
  skills:
    - Skill(imbue:vow-enforcement)
```

This gives the skill a real entry path without removing
the hook layer; the hook continues to enforce hard vows
mechanically while the skill runs its classification logic
under the orchestrator.

## What this document does NOT do

- It does NOT modify `egregore:quality-gate`'s routing
  table this branch.
- It does NOT promote `imbue:vow-enforcement` from
  hook-target to library role yet.
- It does NOT change any hook behaviour.

These are explicit follow-up items for a focused mission
that touches egregore's pipeline. The federation is
documented; the orchestration is proposed; the
implementation is deferred to keep this branch's blast
radius bounded.

## Cross-references

- `docs/quality-gates.md#skill-level-quality-gate-
  composition` -- the federation graph (committed in
  `02fa8948`).
- `docs/skill-taxonomy.md` -- role classification that
  motivates promoting `vow-enforcement` to library role.
- `plugins/egregore/skills/quality-gate/SKILL.md` --
  proposed canonical orchestrator.
- `plugins/imbue/skills/vow-enforcement/SKILL.md` --
  gate skill needing an entry path.
- `plugins/imbue/skills/karpathy-principles/SKILL.md` --
  18 outbound references; today's de-facto gate hub.
