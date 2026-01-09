---
name: test-skill
description: Test skills through RED/GREEN/REFACTOR TDD phases
usage: /test-skill [skill-path] [--phase red|green|refactor]
extends: "superpowers:test-driven-development"
---

# Test Skill

<identification>
triggers: test skill, skill test, validate skill, skill validation, RED GREEN REFACTOR, TDD skill, skill quality

use_when:
- Testing a skill through RED/GREEN/REFACTOR phases
- Validating skill behavior before deployment
- Running TDD checkpoints on skill development

do_not_use_when:
- Evaluating skill quality metrics - use /skills-eval instead
- Creating new skills - use /create-skill instead
- Hardening against rationalization - use /bulletproof-skill
</identification>

Runs skill validation via superpowers:test-driven-development while keeping the familiar `/test-skill` interface.

## How It Works

- Executes RED/GREEN/REFACTOR phases through `superpowers:test-driven-development`.
- Accepts the same arguments as the previous `/test-skill` command.
- Adds superpowers' reporting and enforcement of TDD checkpoints.

## Notes

- Behavior is backward compatible with prior `/test-skill` usage.
- Use `--phase` to target a single stage or run the full cycle without flags.
