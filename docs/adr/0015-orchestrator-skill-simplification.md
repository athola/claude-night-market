# ADR-0015: Over-Built Orchestrator Skill Simplification

**Date**: 2026-05-06
**Status**: Proposed. Accepted 2026-05-06; every implementation item
still unticked as of 2026-09-03.
**Deciders**: Claude Night Market maintainers
**Source**: Issue #455, Discussion #449 Wave-3 backlog item 3

## Context

The April 2026 audit identified the top four violators of AP-3
(Strategy Pattern for One Function):

| Skill | Violation | Recommendation |
|-------|-----------|----------------|
| ``abstract:skills-eval`` | 11 modules and (formerly) 5 fictional tools for a single audit flow | Collapse to a flat checklist |
| ``attune:mission-orchestrator`` | 12 modules and 11 dependencies for "detect phase, call phase skill" | Reduce to a router table |
| ``attune:war-room`` | 4 deliberation modes (Express, Lightweight, Full Council, Delphi) gated by reversibility-score formula | Hard-code one mode after collecting usage data |
| ``imbue:feature-review`` | RICE, WSJF, AND Kano (3 frameworks where 1 would suffice) | Pick one default; others as extensions |

These are publicly invoked skills, so refactoring without a
usage-data pass risks breaking real workflows.

## Decision

Adopt the **two-phase plan** the issue proposes.

### Phase 1: Usage-data collection (current step)

For 30 days starting from this ADR's release date, use
existing observability data (``abstract:skills-eval`` runs,
session logs) to capture for each of the four skills:

- Module-load frequency (which modules get pulled in?)
- Mode/framework selection frequency (which Express/RICE/etc.?)
- Caller distribution (which workflows invoke it most?)

The ``abstract:skill-graph-audit`` skill produces the inputs;
no new tooling required.

### Phase 2: Per-skill simplification

One PR per skill, ordered by data signal strength:

1. ``abstract:skills-eval``: collapse 11 modules to a flat
   checklist (already lost 5 fictional tools in Wave 1)
2. ``imbue:feature-review``: pick the most-used framework as
   default; others move to opt-in extensions
3. ``attune:mission-orchestrator``: replace dependency graph
   with a router table; eliminate unused phase modules
4. ``attune:war-room``: drop unused deliberation modes;
   reversibility-score formula stays only if data shows it
   routes meaningfully

### Compatibility

Public surface change is real. Mitigation: keep old skill names
as thin shims that warn for one release before removal. Same
pattern as ADR-0014.

## Consequences

### Positive

- Lower onboarding cost: fewer modules per skill to read.
- Smaller skill graph fan-out: faster ``skill-graph-audit``,
  fewer broken-target risks.
- Clearer ownership: each remaining module justifies its
  existence with usage data.

### Negative

- 30-day delay before any code change.
- External callers who depend on specific modules / modes need
  one release to migrate.

## Acceptance criteria

- [x] Decision recorded (this ADR)
- [ ] Phase 1: usage data collected for 30+ days; report posted
  to Discussion #449 follow-up
- [ ] Phase 2 PR for ``abstract:skills-eval``
- [ ] Phase 2 PR for ``imbue:feature-review``
- [ ] Phase 2 PR for ``attune:mission-orchestrator``
- [ ] Phase 2 PR for ``attune:war-room``
- [ ] All public slash commands continue to work
- [ ] ``abstract:skill-graph-audit`` confirms reduced fan-out

## Source

- Issue #455 (origin)
- Discussion #449 (April 2026 skill audit synthesis)
- Karpathy AP-3: Strategy Pattern for One Function
- ``plugins/imbue/skills/karpathy-principles/``
