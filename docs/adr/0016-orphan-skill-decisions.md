# ADR-0016: Wire-or-Archive Decisions for Three Orphan Skills

**Date**: 2026-05-06
**Status**: Accepted (decisions recorded; wire-up tracked)
**Deciders**: Claude Night Market maintainers
**Source**: Issue #456, Discussion #449 Wave-3 backlog item 4

## Context

Three skills have backing scripts and tests but **zero invocation
paths** as of the April 2026 audit:

1. ``gauntlet:gauntlet-curate``: intended to integrate with
   ``/update-plugins`` to research and refresh the problem bank.
   Wave 1 corrected the docstring but did not wire the skill.
2. ``memory-palace:palace-diagram``: intended to generate visual
   diagrams of palace structure and knowledge topology. Wave 1
   added a "Status: unwired" notice.
3. ``memory-palace:memory-palace-architect``: intended to design
   memory palace structures and spatial layouts. Wave 1 added a
   "Status: unwired" notice.

For each, a wire-or-archive decision is needed to remove the
ambiguity from the skill graph.

## Decisions

Per-skill decisions follow the issue's three criteria: demand
signal, wiring cost, reference value if archived.

### 1. ``gauntlet:gauntlet-curate``: WIRE

- **Demand signal**: ``/update-plugins`` already includes a
  "refresh problem bank" step in its workflow description; the
  skill exists to satisfy it.
- **Wiring cost**: small. ``sanctum:update-plugins`` SKILL.md
  needs one ``Skill(gauntlet:gauntlet-curate)`` invocation in the
  problem-bank refresh step.
- **Action**: Wire in the next ``/sanctum:update-plugins`` PR.

### 2. ``memory-palace:palace-diagram``: WIRE

- **Demand signal**: medium. Visual palace inspection has been
  asked for in two recent maintenance sessions; a slash command
  surface would lower the bar to use.
- **Wiring cost**: small. Add ``/palace diagram <id>`` slash
  command that delegates to the existing skill.
- **Action**: Wire as a slash command in a follow-up PR.

### 3. ``memory-palace:memory-palace-architect``: ARCHIVE

- **Demand signal**: low. The audit found no inbound consumers
  and no recent demand. The content is reference material
  (design patterns for spatial knowledge layouts).
- **Wiring cost**: large. A ``/palace create`` workflow does not
  exist and would require its own design.
- **Reference value**: high. The prose itself is a useful
  reference for anyone designing a palace.
- **Action**: Convert SKILL.md to ``docs/palace-design.md``;
  remove from active skill graph; preserve content as a static
  reference page.

## Consequences

### Positive

- Three orphan skills resolved: two wired into real workflows,
  one preserved as reference.
- Skill graph fan-out drops by one (``memory-palace-architect``
  removed from active set).
- Future ``skill-graph-audit`` runs flag fewer cold spots.

### Negative

- Two follow-up PRs (wire-up plus archive) needed to land all
  three decisions.

## Acceptance criteria

- [x] Each of the 3 skills has a documented decision (this ADR)
- [ ] ``gauntlet:gauntlet-curate`` wired into
  ``/sanctum:update-plugins``
- [ ] ``memory-palace:palace-diagram`` wired as
  ``/palace diagram <id>``
- [ ] ``memory-palace:memory-palace-architect`` archived; content
  preserved at ``docs/palace-design.md`` if useful
- [ ] ``abstract:skill-graph-audit`` confirms zero remaining
  orphans for these three skills

## Source

- Issue #456 (origin)
- Discussion #449 (April 2026 skill audit synthesis)
- Tier-2 orphan/cold-spot triage agent output
