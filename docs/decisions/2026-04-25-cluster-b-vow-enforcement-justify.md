# Disposition: Cluster B retirement (vow-enforcement / justify)

**Date**: 2026-04-25
**Status**: keep both -- retire neither
**Owner**: skill audit follow-up session 2

## Finding

The 2026-04-25 morning audit identified Cluster B (quality
gates) as a consolidation candidate (overlap=62%, score=37.8)
and proposed retiring `imbue:vow-enforcement` and
`imbue:justify` as duplicative of `imbue:proof-of-work` plus
`leyline:additive-bias-defense`.

The afternoon session documented the gate federation in
`docs/quality-gates.md#skill-level-quality-gate-composition`
and `docs/quality-gate-orchestration.md` instead of retiring,
and recommended re-evaluating after a few sprints of
observation.

This session re-evaluates with current caller data.

## Caller Analysis

### vow-enforcement (1 reference)

Only `docs/quality-gate-orchestration.md` references this
skill. The orchestration doc was added in this branch
(commit `b4eaf050`) precisely to give vow-enforcement a
Skill() entry path, since prior to that it was only
invoked indirectly via the karpathy-principles federation.

It appears in `imbue:karpathy-principles` outbound
references but as part of the federation routing, not as a
direct Skill() call.

The skill has no production callers in plugin code; its
purpose is documented soft/hard/Nen-Court vow enforcement
that no plugin calls today.

### justify (8 references)

Real production callers:

- `plugins/imbue/commands/justify.md` (its own command)
- `plugins/imbue/skills/karpathy-principles/SKILL.md` (gate)
- `plugins/imbue/skills/karpathy-principles/modules/anti-patterns.md`
- `plugins/imbue/README.md`
- `plugins/sanctum/skills/pr-review/SKILL.md`
- `plugins/sanctum/skills/pr-prep/SKILL.md`
- `plugins/pensive/skills/code-refinement/SKILL.md`
- Test file: `tests/unit/commands/test_justify_command.py`

This is a load-bearing post-implementation gate. It is the
only skill that ties additive-bias scanning into a
post-hoc audit workflow (vs proof-of-work's pre-/during-
implementation enforcement).

## Decision

**Retire neither.**

### Rationale for keeping vow-enforcement

The skill is conceptually distinct from proof-of-work:

- proof-of-work demands evidence ("did you run it?")
- vow-enforcement enforces commitments ("did you keep your
  promise to the user?")

Even with one current caller, the abstraction is healthy
infrastructure for the scope-creep prevention work that
karpathy-principles started. The proper response to "low
caller count" for new infrastructure is **promotion**, not
retirement. Aligns with the `pensive:unified-review`
disposition (Option C: promote with usage campaign).

### Rationale for keeping justify

Eight callers including two sanctum hubs (pr-review, pr-prep)
and a karpathy-principles gate. Retirement would force a
multi-plugin migration with no clear benefit -- the overlap
with proof-of-work / additive-bias-defense is in
*coordination*, not in *enforcement of distinct ideas*.

The federation graph in `docs/quality-gates.md` already
distinguishes:

- **proof-of-work**: pre/during, evidence
- **additive-bias-defense**: at-edit, code addition
- **justify**: post-hoc, change audit
- **vow-enforcement**: cross-cutting, commitment

Each occupies a distinct phase / cross-section. Removing
one collapses the lattice.

## Action Items

1. **Promote `imbue:vow-enforcement` usage**: open issue to
   wire it into the quality-gate orchestration of one
   downstream plugin (suggest `egregore:quality-gate` since
   that's already the canonical orchestrator).
2. **Add explicit cross-references** in justify and
   vow-enforcement skills' Related Skills sections so the
   federation is discoverable from any entry point.
3. **Re-evaluate annually**, not per-sprint: caller counts
   for cross-cutting infrastructure naturally lag behind
   feature skills.

## Closes

- Backlog item `[REFACTOR-003]` in
  `docs/backlog/queue.md#skill-audit-2026-04-25`
- Cluster B from
  `docs/audit-2026-04-25-comprehensive-skill-audit.md`
  Consolidation Priority Matrix
