# ADR-0016: Wire-or-Archive Decisions for Three Orphan Skills

**Date**: 2026-05-06
**Status**: Accepted. Decisions recorded 2026-05-06. Decisions 1 and
3 amended 2026-10-27 (#618), and all three are now carried out.
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

### 1. ``gauntlet:gauntlet-curate``: RENAME to ``gauntlet:problem-bank`` (amended 2026-10-27)

The original decision was to wire the skill into ``/update-plugins``,
on the premise that the command already had a problem-bank refresh
step. It has none. ``/update-plugins`` audits plugin.json
registrations, and no ``sanctum:update-plugins`` skill exists to edit.

The orphaning had a different cause. The ``/gauntlet-curate`` command
shares the skill's name and invokes ``gauntlet:curate``, the annotation
skill. The command shadowed the skill, and nothing could reach it by
name.

- **Action**: rename the skill to ``problem-bank`` (#618). A test in
  ``plugins/gauntlet/tests/unit/skills/test_problem_bank.py`` fails if
  any gauntlet skill shares a command's name again.

### 2. ``memory-palace:palace-diagram``: WIRE

- **Demand signal**: medium. Visual palace inspection has been
  asked for in two recent maintenance sessions; a slash command
  surface would lower the bar to use.
- **Wiring cost**: small. Add ``/palace diagram <id>`` slash
  command that delegates to the existing skill.
- **Action**: Wire as a slash command in a follow-up PR.

### 3. ``memory-palace:memory-palace-architect``: WIRE (amended 2026-10-27)

The original decision was ARCHIVE, on a wiring cost judged large
because no ``/palace create`` workflow routes through the skill. That
missed the ``palace-architect`` agent, which exists to design palaces
and restated the skill's five-step method without loading it. Five
sibling skills also route readers to this one by name. Archiving it
would have broken their routing.

- **Wiring cost**: one line. The agent loads
  ``Skill(memory-palace:memory-palace-architect)`` (#618).
- **Also fixed**: the skill and the agent both told the reader to run
  ``palace_manager.py``, which has no CLI entry point. Both now cite
  ``scripts/memory_palace_cli.py create``.

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
- [x] ``gauntlet:gauntlet-curate`` renamed to ``gauntlet:problem-bank``
  so the ``/gauntlet-curate`` command no longer shadows it (#618)
- [x] ``memory-palace:palace-diagram`` wired as
  ``/palace diagram <id>`` (#582)
- [x] ``memory-palace:memory-palace-architect`` wired through the
  ``palace-architect`` agent (#618, amended from archive)
- [ ] ``abstract:skill-graph-audit`` confirms zero remaining
  orphans for these three skills

## Source

- Issue #456 (origin)
- Discussion #449 (April 2026 skill audit synthesis)
- Tier-2 orphan/cold-spot triage agent output
