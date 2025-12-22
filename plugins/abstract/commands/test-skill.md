---
name: test-skill
description: |
  Skill testing workflow powered by superpowers:test-driven-development.

  Triggers: test skill, skill test, validate skill, skill validation,
  RED GREEN REFACTOR, TDD skill, skill quality

  Use when: testing a skill through RED/GREEN/REFACTOR phases, validating skill
  behavior before deployment, running TDD checkpoints on skill development

  DO NOT use when: evaluating skill quality metrics - use /skills-eval instead.
  DO NOT use when: creating new skills - use /create-skill instead.
  DO NOT use when: hardening against rationalization - use /bulletproof-skill.

  Use this command to test skills with TDD enforcement.
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
