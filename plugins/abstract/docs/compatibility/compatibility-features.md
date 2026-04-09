# Claude Code Compatibility Features

Feature timeline and version-specific capabilities, organized by
release period.

> **See Also**: [Patterns](compatibility-patterns.md)

## Timeline Index

| Period | Versions | File |
|--------|----------|------|
| March 2026 (Recent) | 2.1.63 – 2.1.85 | [March 2026 Recent](../archive/compatibility-features-march2026-recent.md) |
| March 2026 (Early) | 2.1.50 – 2.1.62 | [March 2026 Early](../archive/compatibility-features-march2026-early.md) |

## Plugin-Specific Compatibility

Per-plugin minimum version requirements and version-specific notes:
[Plugin Compatibility](compatibility-features-plugin-compat.md)

## Quick Reference: Recent Highlights

### March 2026 (2.1.63-2.1.85)

- **2.1.85**: Hook conditional `if` field (permission rule
  syntax), MCP headersHelper server env vars, PreToolUse
  satisfies AskUserQuestion, MCP OAuth RFC 9728, org plugin
  blocking, OTEL tool_parameters gated, `/compact` context
  exceeded fix, terminal enhanced keyboard mode fix
- **2.1.84**: PowerShell tool (Windows preview), model
  capability env vars (`_MODEL_SUPPORTED_CAPABILITIES`),
  TaskCreated hook (blockable), WorktreeCreate HTTP hooks,
  idle-return prompt (75+ min), MCP tool desc 2KB cap,
  rules/skills YAML glob paths, system-prompt caching fix
- **2.1.83**: `managed-settings.d/` drop-in directory,
  CwdChanged/FileChanged hooks, `sandbox.failIfUnavailable`,
  subprocess env scrub, agent `initialPrompt`, plugin
  `userConfig` with keychain storage, MEMORY.md 25KB limit,
  TaskOutput deprecated, transcript search
- **2.1.81**: `--bare` flag (skip hooks/LSP/plugins/memory),
  `--channels` permission relay, MCP OAuth CIMD
- **2.1.80**: `rate_limits` statusline field, `effort`
  frontmatter for skills/commands, `--channels` preview,
  `source: 'settings'` plugin source, 80MB startup savings
- **2.1.79**: `--console` auth, multi-dir plugin seed dir,
  18MB startup savings, non-streaming 2-min timeout
- **2.1.78**: StopFailure hook, `${CLAUDE_PLUGIN_DATA}`,
  agent `effort`/`maxTurns`/`disallowedTools` frontmatter,
  sandbox security fixes
- **2.1.77**: Opus 4.6 output tokens default 64k (upper bound
  128k), `allowRead` sandbox setting, `/copy N`, PreToolUse
  "allow" bypass deny fix (security), compound bash "Always
  Allow" fix, auto-updater memory leak, `--resume` truncation
  race, Write tool CRLF fix, progress message memory growth
  fix, Agent `resume` parameter removed (use SendMessage),
  SendMessage auto-resumes stopped agents, `/fork` renamed to
  `/branch`, background bash 5GB limit, `plugin validate`
  improvements, macOS startup 60ms faster, `--resume` 45%
  faster, stale worktree cleanup race fix
- **2.1.76**: MCP elicitation support (form fields and URL mode),
  Elicitation/ElicitationResult hooks (blockable), PostCompact
  hook, `-n`/`--name` CLI flag, `worktree.sparsePaths` for
  monorepos, `/effort` slash command, `feedbackSurveyRate`
  setting, deferred tools schema fix (post-compaction), auto-
  compaction circuit breaker (3 attempts), spurious "Context
  limit reached" fix with `model:` frontmatter on 1M sessions,
  adaptive thinking error fix for non-standard models, Bash `#`
  permission fix, worktree startup performance, background agent
  partial results preserved, model fallback always visible, stale
  worktree cleanup, `--plugin-dir` single path change, Remote
  Control fixes (session reaping, message batching, JWT refresh,
  WebSocket recovery)
- **2.1.75**: 1M context window default for Max/Team/Enterprise
  (Opus 4.6), `/color` command for session identification,
  session name on prompt bar with `/rename`, last-modified
  timestamps on memory files, hook source display in permission
  prompts, token estimation over-counting fix (premature
  compaction), Bash `!` pipe fix, async hook messages suppressed,
  macOS startup performance, Windows managed settings path
  removal (breaking change)
- **2.1.74**: `/context` actionable suggestions, `autoMemoryDirectory`
  setting, streaming memory leak fix, managed policy ask bypass fix,
  full model IDs in agent frontmatter, SessionEnd hooks timeout fix
  (`CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`), `--plugin-dir` overrides
  marketplace, new hook events (CwdChanged, FileChanged, PostCompact,
  TaskCreated, StopFailure, Elicitation, ElicitationResult)
- **2.1.73**: `modelOverrides` setting for Bedrock/Vertex/Foundry
  inference profiles, SSL certificate error guidance, subagent
  model downgrade fix on third-party providers, default Opus 4.6
  on Bedrock/Vertex/Foundry, SessionStart resume double-fire fix,
  JSON-output hooks system-reminder fix, `/output-style` deprecated,
  `/loop` available on all providers, skill file deadlock fix,
  background bash process cleanup
- **2.1.72**: ExitWorktree tool, effort simplified to 3 levels (max
  removed), CLAUDE.md HTML comments hidden, skill hook double-fire
  fix, parallel tool call cascade fix (only Bash cascades), prompt
  cache 12x savings, team agents inherit leader model, 6 plugin
  marketplace fixes
- **2.1.71**: `/loop` + cron scheduling (`CronCreate`/`CronList`/
  `CronDelete` with `durable` persistence), bash auto-approval
  expansion (11 POSIX utilities), background agent notification fix,
  plugin marketplace @ref parsing fix, MCP server deduplication
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
