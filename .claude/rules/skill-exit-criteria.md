---
description: Require Exit Criteria sections in SKILL.md files
alwaysApply: true
---

**Every new or modified SKILL.md must include an Exit Criteria
section!**

The April 2026 Karpathy-compliance audit found 125 of 183 SKILL.md
files (68%) lacked an Exit Criteria section. This is AP-7 (Vague
Success Criteria) at scale: a skill without exit criteria is a
skill the model cannot tell when to stop.

**Required format:**

```markdown
## Exit Criteria

- [ ] Concrete observable A
- [ ] Concrete observable B
- [ ] Failure mode N is detected and surfaced
```

Each criterion must be:

- **Concrete**: a state a reader can verify from outside the
  conversation (file exists, value parses, score above threshold)
- **Observable**: tied to a tool call, file path, or numeric
  threshold, not an internal feeling ("the skill feels complete")
- **Falsifiable**: removing the supporting code or doc must make
  at least one criterion fail

**When the rule applies:**

- Authoring a new SKILL.md
- Modifying an existing SKILL.md (add the section if missing)
- Reviewing a PR that touches SKILL.md files

**When it does not apply:**

- Module files (``modules/*.md``) inside a skill directory
- Reference documentation (``docs/``)
- Slash command files (``commands/*.md``); commands have their own
  argument and output contract conventions

**Backfill plan:**

The 125 existing files are tracked in issue #454. Backfill in
batches of 10-15 skills per PR, grouped by plugin. Plugins with
no Exit Criteria coverage today (conserve, cartograph,
memory-palace, tome, gauntlet) are highest priority.

**References:**

- Issue #454 (origin)
- Discussion #449 (April 2026 skill audit synthesis)
- Karpathy AP-7: Vague Success Criteria
- ``plugins/imbue/skills/karpathy-principles/SKILL.md``
