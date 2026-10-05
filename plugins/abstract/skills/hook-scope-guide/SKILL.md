---
name: hook-scope-guide
description: 'Select hook scope (plugin, project, global) by audience. Use when authoring a hook.'
category: hook-development
---

# Hook Scope Decision Guide

## Overview

This skill helps you choose the right location for Claude Code hooks based on their purpose, audience, and persistence needs.

## When NOT To Use

- Writing the hook itself (use `abstract:hook-authoring`)
- Scoring an existing hook (use `abstract:hooks-eval`)

## Decision Framework

Three questions pick the scope: who needs this hook, should it be
version controlled, and how long should it persist. Plugin hooks
(`hooks/hooks.json` in the plugin) serve plugin users while the plugin
is enabled. Project hooks (`.claude/settings.json`) serve the team and
are committed. Global hooks (`~/.claude/settings.json`) serve only you,
in every session, and are never committed.

The question tree, per-scope configuration and examples, loading
precedence, security considerations, migration and troubleshooting are
written once, in
`plugins/abstract/skills/hook-authoring/modules/scope-selection.md`.
Read it before choosing. Agent-aware SessionStart hooks are covered in
`abstract:hook-authoring` under Hook Event Types.

## Related Skills

- **abstract:hook-authoring** - For hook rule syntax and patterns
- **abstract:validate-plugin** - For validating plugin structure including hooks

## References

- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Settings Configuration](https://docs.anthropic.com/en/docs/claude-code/settings)

## Exit Criteria

- [ ] A single scope (plugin / project / global) is selected and the rationale traces through at
  least two of the three decision questions (audience, version control, persistence).
- [ ] The selected scope's file location (`hooks/hooks.json`, `.claude/settings.json`, or
  `~/.claude/settings.json`) is confirmed to exist or is created at the correct path.
- [ ] Plugin hooks do not add `"hooks": "./hooks/hooks.json"` to `plugin.json` (duplicate-load
  guard); this absence is verified before the hook is deployed.
- [ ] Global hooks are flagged with a security note confirming they apply to all Claude sessions
  on this machine.
