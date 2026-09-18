# ADR-0014: Pensive Review-Skill Consolidation

**Date**: 2026-05-06
**Status**: Proposed. Accepted 2026-05-06 as sequencing only; no
implementation as of 2026-09-03, and the premise has moved: pensive has
10 review-named skills, not 9.
**Deciders**: Claude Night Market maintainers
**Source**: Issue #453, Discussion #449 Wave-3 backlog item 1

## Context

The ``pensive`` plugin has 9 review-named skills, of which 5
reinvent the same "Approve / Approve with actions / Block"
scaffold verbatim. Two of them, ``pensive:shell-review`` and
``pensive:makefile-review``, already appear in
``pensive:unified-review``'s dispatch table, so they are prime
candidates to fold into unified-review as modules.

## Decision

Adopt the consolidation plan with **separate PRs per skill** and
**alias stubs** for one release.

### Sequence

1. **PR-A: shell-review**: move content into
   ``pensive:unified-review/modules/shell-review.md``; replace
   the public ``/shell-review`` slash command with a thin alias
   that invokes unified-review with the shell selector. Migrate
   tests.
2. **PR-B: makefile-review**: identical pattern, separate PR
   so review surface stays small.

### Compatibility

External users may rely on the skill names directly via
``Skill(...)`` calls. Keep ``pensive:shell-review`` and
``pensive:makefile-review`` as redirect stubs for one release
(emit a one-line deprecation note pointing at unified-review).
Remove the stubs in the release after.

### Verification

Before deleting the old SKILL.md files:

```bash
rg "pensive:shell-review|pensive:makefile-review" \
   plugins/ tests/ docs/
```

Any remaining external references convert to
``pensive:unified-review/modules/<name>``.

## Consequences

### Positive

- Two fewer top-level skills in pensive (9 to 7), reducing the
  "9 review skills, all named alike" cognitive load.
- Single ownership of the review scaffold inside unified-review.
- Future review-domain additions land as modules, not new skills.

### Negative

- One release of stub maintenance overhead.
- Documentation in external repos may need updating (best-effort).

## Acceptance criteria

- [x] Decision recorded (this ADR)
- [ ] PR-A merged: shell-review folded; alias stub in place;
  CHANGELOG entry under deprecations
- [ ] PR-B merged: makefile-review folded; alias stub in place;
  CHANGELOG entry under deprecations
- [ ] One release elapses; deprecation removal PR queued

## Source

- Issue #453 (origin)
- Discussion #449 (April 2026 skill audit), Wave-3 backlog item 1
- Pensive review-skill scaffold reuse confirmed via Tier-2 audit
