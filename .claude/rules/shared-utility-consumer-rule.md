---
description: Shared-utility skills require >=2 inbound consumers within 30 days
alwaysApply: true
---

**Utility-named skills must earn their consumers!**

Skills that claim a utility or scaffolding role
(``*-core``, ``*-shared``, ``shared-*``, ``*-patterns``) must have
**at least 2 inbound consumers within 30 days of authoring**, or
be folded back into their first consumer.

This rule prevents AP-3 (Strategy Pattern for One Function) at the
skill-graph level: scaffolding for hypothetical future composition
that never materializes.

**Detection** (``detect_unearned_utilities`` in
``plugins/abstract/scripts/skill_graph.py``, reported by
``abstract:skill-graph-audit``):

```
inbound_refs = skills naming it in Skill() or frontmatter dependencies
             + plugins/*/commands/*.md and plugins/*/agents/*.md
               mentioning <plugin>:<name>
age_days     = days since git first added its SKILL.md
if is_utility_named and inbound_refs < 2 and age_days >= 30
   and no fold_back_exception:
    flag for fold-back
```

archetypes' ``architecture-paradigm-*`` skills are skipped: "Functional
Core" names a paradigm, not a utility role. The check reports nothing
when PyYAML is missing, because frontmatter edges would be invisible.

**Why this rule exists:**

The April 2026 audit found that the most-referenced skills are
also the most-modular (``imbue:proof-of-work``,
``imbue:scope-guard``, ``superpowers:test-driven-development``,
``leyline:git-platform``). Unreferenced "shared utility" skills
tend to be invented in advance of need rather than extracted from
working code.

**Compliance:**

| Inbound refs | Age | Action |
|--------------|-----|--------|
| 0           | <30 days | OK, grace period |
| 0           | >=30 days | Fold back into a consumer or delete |
| 1           | <30 days | OK, grace period |
| 1           | >=30 days | Document the second-consumer plan or fold back |
| >=2         | any | OK |

**Exceptions:**

A utility skill may exceed the grace period without being folded
if it has a documented second-consumer plan with a target date.
The exception belongs in the skill's frontmatter as
``fold_back_exception: <issue-or-discussion-link>``.

**References:**

- Issue #457 (origin)
- Discussion #449 (April 2026 skill audit synthesis)
- Karpathy AP-3: Strategy Pattern for One Function
- Examples: abstract's former shared-patterns skill (the audit found
  near-zero consumers, and it was deleted under this rule on
  2026-09-02); ``imbue:review-core`` (Wave 1 found and wired the
  consumers that justify keeping it)
