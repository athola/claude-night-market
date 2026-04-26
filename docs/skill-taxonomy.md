# Skill Role Taxonomy

## Why this document exists

The 2026-04-25 audit (`docs/audit-2026-04-25-
comprehensive-skill-audit.md`) found that 85 of 195
skills (~43%) have **zero inbound `Skill()` references**.
That sounds alarming until you separate two distinct
populations:

1. Skills users invoke directly via slash commands or
   agent prompts -- they SHOULD have low Skill() inbound
   counts because the user is the caller.
2. Skills that exist solely to be loaded by other skills
   -- they SHOULD have high Skill() inbound counts because
   that's their entire purpose.

Without this distinction, "orphan" is a meaningless flag.
This document defines three formal roles and uses them
to classify the skills the previous audit flagged.

## The three roles

| Role | Inbound Skill() | User-facing | Examples |
|------|----------------|-------------|----------|
| `entrypoint` | low (0-3) | yes | `attune:mission-orchestrator`, `sanctum:do-issue` |
| `library` | high (4+) | rarely | `scribe:slop-detector`, `imbue:proof-of-work` |
| `hook-target` | varies | no | `imbue:vow-enforcement`, hook-implemented checks |

### Entrypoint skills

Invoked directly by users (via `/<plugin>:<skill>`
slash commands or by agents acting on user prompts).
Their value is end-to-end orchestration; they typically
call several library skills internally.

**Signature**:

- Has a corresponding `commands/<name>.md` file
- Is registered in `plugin.json` under `commands` (not
  just `skills`)
- Description follows the "Verb + domain. Use when..."
  trigger pattern
- Often a long SKILL.md with multiple modules

**Examples**:

- `attune:mission-orchestrator` (12 modules,
  user-invoked via `/attune:mission`)
- `sanctum:do-issue` (orchestrates issue resolution
  through analyze-specify-plan-implement phases)
- `spec-kit:speckit-orchestrator` (workflow router for
  spec-driven development)
- `egregore:summon` (autonomous mission processor)

### Library skills

Loaded by other skills via `Skill(<plugin>:<name>)`
during execution. Their value is reusable building
blocks; they don't ship a slash command of their own.

**Signature**:

- No corresponding `commands/<name>.md`
- Registered in `plugin.json` only under `skills`
- Description focuses on what the skill DOES, not on
  user triggers
- High inbound Skill() reference count

**Examples**:

- `scribe:slop-detector` -- 17+ inbound references; called
  by sanctum, scribe, abstract, memory-palace, hookify
- `imbue:proof-of-work` -- 17+ inbound references; called
  from quality-gate sequences
- `sanctum:git-workspace-review` -- 13+ inbound
  references; called as preflight by commit / PR / review
  flows
- `leyline:git-platform` -- utility loader for
  cross-platform git command mapping
- `archetypes:architecture-paradigm-*` (9 paradigm
  modules) -- referenced by `archetypes:architecture-
  paradigms` and `attune:architecture-aware-init`

### Hook-target skills

Invoked by hooks (PreToolUse / PostToolUse / SessionStart
/ Stop) rather than by other skills or users. Their value
is enforcement; the hook system reads the SKILL.md to
shape its own behaviour.

**Signature**:

- Plugin has hooks registered in `hooks/hooks.json` that
  reference the skill by name or read its body
- Description often mentions enforcement, validation, or
  classification
- Low or zero Skill() inbound count in skill prose, but
  active in hook execution paths

**Examples**:

- `imbue:vow-enforcement` -- read by `imbue/hooks/
  vow_*.py` to source the constraint classification
- `imbue:karpathy-principles` -- referenced by
  `imbue/hooks/proof_enforcement.py`
- `conserve:clear-context` -- triggered by SessionStart
  context-overflow detection

## Re-classifying the 85 audit "orphans"

A spot-check of 10 of the previously-flagged orphans:

| Skill | Audit verdict | Real role |
|-------|---------------|-----------|
| `archetypes:architecture-paradigm-hexagonal` | orphan | library (loaded by paradigms hub) |
| `archetypes:architecture-paradigm-microservices` | orphan | library (paradigms hub) |
| `pensive:api-review` | orphan | library (loaded via unified-review module) |
| `pensive:bug-review` | orphan | library (unified-review) |
| `pensive:blast-radius` | orphan | entrypoint (`/pensive:blast-radius`) |
| `tome:code-search` | orphan | library (loaded by `tome:research`) |
| `tome:discourse` | orphan | library (loaded by `tome:research`) |
| `scry:before-after` | orphan | hook-target (postlude script reads it) |
| `conserve:agent-expenditure` | orphan | library (loaded by parallel-dispatch) |
| `cartograph:call-chain` | orphan | entrypoint (slash command exists) |

Verdict: **8 of 10 are correctly populated libraries** that
the `Skill()` regex couldn't see because their callers load
them via `dependencies:` or `modules:` arrays in
frontmatter, not inline `Skill(...)` invocations. Two are
genuine entrypoints with slash commands.

This is a measurement bug in the audit, not a coverage
problem in the marketplace. The taxonomy needs to be the
basis for any future "orphan" detection: only skills with
**no entry path of any kind** (Skill() callers, slash
command, hook handle, dependency array, module reference)
qualify as orphans.

## Recommended frontmatter convention (proposal)

This is documented as a proposal -- no schema change is
made on this branch. The recommendation for new skills:

```yaml
---
name: <kebab-case>
description: '...'
role: entrypoint  # or library, or hook-target
...
---
```

Tooling implications if adopted:

- Audit scripts can filter by role before flagging
  orphans (current false-positive rate is high).
- Plugin validators can require role-appropriate fields
  (e.g., entrypoints must have a matching command file).
- `abstract:skills-eval` can apply different quality
  thresholds per role (entrypoints face higher
  description-budget pressure than libraries).

Adoption path: tag new skills with `role:` going forward;
backfill existing skills opportunistically during other
work.

## What this document does NOT change

This is a synthesis document, not a refactor. It does
not:

- Modify any skill frontmatter (no `role:` field added
  this branch).
- Reorganise skills into role-aware folders.
- Change the audit script's orphan-detection logic.
- Promote or retire any skill.

Those are follow-up items for a focused mission once the
convention is socialised.

## Cross-references

- `docs/audit-2026-04-25-comprehensive-skill-audit.md` --
  the audit that surfaced the orphan finding.
- `docs/quality-gates.md#skill-level-quality-gate-
  composition` -- gate-skill federation showing
  library-style composition.
- `plugins/abstract/scripts/validate_budget.py` --
  current budget validator (does not yet read role).
- `plugins/abstract/scripts/skill_analyzer.py` --
  candidate location for role-aware classification.
