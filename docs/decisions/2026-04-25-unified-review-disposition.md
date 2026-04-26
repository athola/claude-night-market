# Disposition: pensive:unified-review

**Date**: 2026-04-25
**Status**: deferred -- no code change this branch
**Owner**: skill audit follow-up session

## Finding

`pensive:unified-review` is documented as a hub orchestrating
seven domain-specific review skills (rust, api, architecture,
bug, test, makefile, math). Its `dependencies:` array lists
all seven, and its module structure (`modules/auto-detect.md`,
`modules/focused-mode.md`, `modules/full-mode.md`,
`modules/release-notes.md`) supports three operating modes.

But the audit shows it has exactly **one inbound `Skill()`
caller** in skill prose: `plugins/abstract/skills/plugin-
review/modules/tier-release.md`. `egregore:summon` references
it indirectly via the `quality-gate` routing table.

Meanwhile, `sanctum:pr-review` (581 LOC, modular) does its
own phase-based review without calling `unified-review`,
even though its `dependencies:` array names it.

The two skills have measurable prose overlap and will
diverge as both receive independent enhancements.

## Three options

### Option A: Retire

Delete `pensive:unified-review`, migrate the one caller
(`abstract:plugin-review`) to invoke each domain review
directly, and drop the dependency from `sanctum:pr-review`.

**Pros**: removes 839 LOC of redundant orchestration; one
fewer skill to maintain; eliminates the divergence risk.

**Cons**: loses the auto-detect / focused / full mode
abstraction; consumers have to choose review skills
individually; each future caller has to re-implement the
orchestration.

### Option B: Absorb into sanctum:pr-review

Move the unified-review modules into `sanctum:pr-review`
as additional internal modes; retire the standalone skill.

**Pros**: single authoritative review skill in the
ecosystem; clear ownership in sanctum; the divergence
problem disappears because there's only one
implementation.

**Cons**: HIGH risk -- 7+ callers reference at least one
of the two skills (counted in the previous audit); a
focused mission with caller analysis is required;
sanctum:pr-review grows to ~750 LOC.

### Option C: Promote with usage campaign

Keep `pensive:unified-review`, add it to the canonical
gate-orchestration sequence in `docs/quality-gate-
orchestration.md`, and update consumers to prefer it over
hand-rolled review chains.

**Pros**: preserves the hub abstraction; clarifies the
intended call pattern; lowest blast radius.

**Cons**: requires updating multiple consumers; existing
prose overlap with `sanctum:pr-review` remains; doesn't
solve the divergence problem on its own.

## Recommendation

**Option C (promote with usage campaign)** as the next
step, with **Option B (absorb)** as the eventual
direction once the federation is observable in practice.

Rationale: Option A throws away a valid abstraction; Option
B is the right end state but is HIGH risk and needs the
caller analysis a focused mission can provide. Option C is
the smallest reversible step that resolves the immediate
"orphan-shaped" finding without committing to retirement.

## What this branch does NOT do

- It does NOT delete `pensive:unified-review`.
- It does NOT modify `sanctum:pr-review` to remove or
  add the dependency.
- It does NOT update any caller to switch invocation
  patterns.

The disposition is recorded; the actual move belongs to a
focused mission with a caller analysis attached.

## Cross-references

- `docs/audit-2026-04-25-comprehensive-skill-audit.md` --
  audit that surfaced the 1-caller finding (Cluster A).
- `docs/skill-taxonomy.md` -- entrypoint vs library
  distinction relevant to this disposition.
- `docs/quality-gate-orchestration.md` -- Option C
  integration point.
- `plugins/pensive/skills/unified-review/SKILL.md`
- `plugins/sanctum/skills/pr-review/SKILL.md`
- `plugins/abstract/skills/plugin-review/modules/
  tier-release.md` -- the one current caller.
