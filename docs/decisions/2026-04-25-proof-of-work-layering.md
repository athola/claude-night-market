# Disposition: imbue:proof-of-work hook/skill layering

**Date**: 2026-04-25
**Status**: deferred -- no code change this branch
**Owner**: skill audit follow-up session

## Finding

`imbue:proof-of-work` is invoked from two layers
simultaneously:

- **Skill layer**: 13 inbound `Skill(imbue:proof-of-work)`
  callers across sanctum, attune, scribe, abstract, and
  imbue's own commands.
- **Hook layer**: `plugins/imbue/hooks/proof_enforcement.py`
  reads the skill body to enforce evidence requirements
  mechanically.

The codebase's three-layer contract (skills are discursive,
hooks are mechanical, commands are entrypoints) treats this
overlap as a smell: the same logic should not be invoked
through two different layers of the abstraction stack.

## Why this happened

Both invocation paths grew organically. The skill came
first as discursive guidance ("show your work, cite
evidence"). The hook came later as enforcement ("block
commits that claim work without evidence"). Neither
deletion nor consolidation happened; the skill stayed
authoritative in prose while the hook started reading it.

## Proposed split

Two skills, one hook:

- **`imbue:proof-citation`** (skill, library role): the
  narrative content -- evidence formats, `[E1]`/`[E2]`
  references, status taxonomy (PASS / FAIL / BLOCKED),
  examples. Loaded by skills when constructing
  proof-of-work entries.
- **`imbue:proof-enforcement`** (hook target, hook-target
  role): the mechanical content -- what the hook reads to
  decide whether to block. Terse, machine-friendly,
  not invoked from prose.
- **`imbue/hooks/proof_enforcement.py`** (existing): reads
  `proof-enforcement` only; ignores `proof-citation`.

`imbue:proof-of-work` becomes a thin shim that re-exports
both for one release cycle to avoid breaking the 13
existing callers. After that release the shim is removed
and callers migrate to the appropriate sub-skill.

## Why this branch does NOT do it

The previous audit estimated 17 inbound references at the
time; this audit verifies 13 active `Skill()` callers plus
hook-side reads. Either way, the migration touches:

- 13 skill files that import the current shim.
- 1 hook file that reads the body.
- All command files referencing `Skill(imbue:proof-of-
  work)` (8+ commands).

That blast radius makes it focused-mission territory --
the change needs a caller-by-caller migration plan and a
deprecation window. Doing it inline in this audit
follow-up would expand the branch beyond its declared
scope (the user already waived scope-guard for the audit;
expanding further is the wrong direction).

## What this branch does

Records the finding so the next person who tries to fix
it has the analysis already done. The four artifacts that
make the migration safe:

1. The 13 caller list (run `rg -l "Skill\\(imbue:proof-of-
   work\\)" plugins/`).
2. The hook's read pattern (`plugins/imbue/hooks/
   proof_enforcement.py`).
3. The skill body's split points (the prose that's
   hook-readable vs the prose that's narrative).
4. `docs/skill-taxonomy.md` -- the role classification
   that justifies why two skills are clearer than one.

## Cross-references

- `plugins/imbue/skills/proof-of-work/SKILL.md`
- `plugins/imbue/hooks/proof_enforcement.py`
- `docs/skill-taxonomy.md`
- `docs/quality-gate-orchestration.md` -- proof-of-work
  is step 5 of the canonical gate sequence.
- `docs/audit-2026-04-25-comprehensive-skill-audit.md`
