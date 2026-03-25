# Claude Code Compatibility Features

Feature timeline and version-specific capabilities, organized by
release period.

> **See Also**: [Reference](compatibility-reference.md) |
> [Patterns](compatibility-patterns.md) |
> [Issues](compatibility-issues.md)

## Timeline Index

| Period | Versions | File |
|--------|----------|------|
| March 2026 (Recent) | 2.1.63 – 2.1.71 | [March 2026 Recent](compatibility-features-march2026-recent.md) |
| March 2026 (Early) | 2.1.50 – 2.1.62 | [March 2026 Early](compatibility-features-march2026-early.md) |

## Plugin-Specific Compatibility

Per-plugin minimum version requirements and version-specific notes:
[Plugin Compatibility](compatibility-features-plugin-compat.md)

## Quick Reference: Recent Highlights

### March 2026 (2.1.63-2.1.71)

- **2.1.71**: `/loop` + cron scheduling (`CronCreate`/`CronList`/
  `CronDelete`), bash auto-approval expansion, stdin freeze fix
- **2.1.70**: Compaction image preservation, resume token savings
- **2.1.69**: `${CLAUDE_SKILL_DIR}` variable, HTTP hooks plugin fix,
  Sonnet 4.5 to 4.6 migration
- **2.1.68**: Opus 4.6 defaults to medium effort, "ultrathink" keyword,
  Opus 4/4.1 removed
- **2.1.63**: HTTP hooks, `/clear` skill cache fix, 12+ memory leak fixes

### March 2026 (2.1.50-2.1.62)

- **2.1.59**: Auto-memory with `/memory` command, config corruption fix
- **2.1.51**: `claude remote-control`, managed settings via
  plist/registry, tool result persistence threshold 50K
- **2.1.50**: `WorktreeCreate`/`WorktreeRemove` hooks,
  `isolation: worktree` in agent frontmatter,
  `CLAUDE_CODE_SIMPLE` enhancement

### February 2026 (2.1.38-2.1.49)

- **2.1.49**: Worktree isolation for subagents, background agent MCP
  restriction
- **2.1.47**: `last_assistant_message` in Stop hook, background agent
  transcript fix, parallel file write resilience
- **2.1.45**: Claude Sonnet 4.6, plugin settings from `--add-dir`
- **2.1.39**: Nested session guard, hook exit code 2 stderr displayed
- **2.1.38**: Heredoc security fix, sandbox hardening

### February 2026 (2.1.21-2.1.34)

- **2.1.34**: Sandbox permission bypass fix (security)
- **2.1.33**: TeammateIdle/TaskCompleted hooks, agent memory
  frontmatter, `Task(agent_type)` restrictions
- **2.1.32**: Claude Opus 4.6, agent teams research preview,
  automatic memory recording
- **2.1.30**: Read tool PDF pages parameter, Task tool metrics
- **2.1.21-2.1.27**: PR-linked sessions, auto-compact threshold fix,
  Task ID reuse fix

### January 2026 (2.1.0-2.1.18)

- **2.1.18**: Customizable keyboard shortcuts via `keybindings.json`
- **2.1.9**: PreToolUse `additionalContext`, `${CLAUDE_SESSION_ID}`
  substitution, MCP tool search threshold config
- **2.1.7**: MCP tool search auto mode (default), wildcard permission
  compound command fix (security)
- **2.1.6**: Nested skills discovery, status line context percentage
- **2.1.3**: Skills/commands unified, hook timeout extended (60s to
  10min), subagent model fix during compaction
- **2.1.0**: Automatic skill hot-reload, `context: fork` support,
  hooks in agent/skill/command frontmatter, context window percentage
  fields

> **Older releases**: Archived compatibility data for Jan 2026 and
> earlier is available in git history.
