---
name: test-skill
description: Skill testing workflow powered by superpowers:test-driven-development
usage: /test-skill [skill-path] [--phase red|green|refactor]
extends: "superpowers:test-driven-development"
---

# Test Skill

Runs skill validation via superpowers:test-driven-development while keeping the familiar `/test-skill` interface.

## How It Works

- Executes RED/GREEN/REFACTOR phases through `superpowers:test-driven-development`.
- Accepts the same arguments as the previous `/test-skill` command.
- Adds superpowers' reporting and enforcement of TDD checkpoints.

## Notes

- Behavior is backward compatible with prior `/test-skill` usage.
- Use `--phase` to target a single stage or run the full cycle without flags.
