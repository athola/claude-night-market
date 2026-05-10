# Claude Code Compatibility Features

Feature timeline and version-specific capabilities, organized by
release period.

> **See Also**: [Patterns](compatibility-patterns.md)

## Timeline Index

| Period | Versions | File |
|--------|----------|------|
| April–May 2026 | 2.1.97 – 2.1.138 | (this file, Quick Reference below) |
| March 2026 (Recent) | 2.1.63 – 2.1.85 | [March 2026 Recent](compatibility-features-march2026-recent.md) |
| March 2026 (Early) | 2.1.50 – 2.1.62 | [March 2026 Early](compatibility-features-march2026-early.md) |

## Plugin-Specific Compatibility

Per-plugin minimum version requirements and version-specific notes:
[Plugin Compatibility](compatibility-features-plugin-compat.md)

## Quick Reference: Recent Highlights

### April–May 2026 (2.1.97-2.1.138)

Plugin-author-relevant changes only; UI, IDE, and CLI-internal
fixes are omitted. See `~/.claude/release-notes` for the full log.

- **2.1.136**: `skills` entry in `plugin.json` listing a file path
  now errors instead of failing silently — must be a directory;
  `AskUserQuestion` array multi-select fix; plugin uninstall and
  enable/disable now slug-matched case-insensitively; `CronList`
  output includes qualifiers and scheduled prompt; plugin slash
  commands with spaces (e.g. `/myplugin review`) resolve to
  namespaced form
- **2.1.133**: `worktree.baseRef` setting (`fresh` | `head`) —
  default `fresh` reverts the 2.1.128 default of local HEAD;
  hooks now receive `effort.level` JSON field and `$CLAUDE_EFFORT`
  env var; Bash tool subprocesses also get `$CLAUDE_EFFORT`;
  `parentSettingsBehavior` admin-tier key (`first-wins`/`merge`);
  `sandbox.bwrapPath`/`sandbox.socatPath` managed settings;
  subagents now discover project/user/plugin skills via Skill tool
- **2.1.132**: `CLAUDE_CODE_SESSION_ID` env var for Bash tool
  subprocesses (matches `session_id` in hook JSON);
  `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1` opt-out for fullscreen
  renderer
- **2.1.129**: Plugin manifest `themes` and `monitors` should be
  declared under `"experimental": { ... }` (top-level still works
  but `claude plugin validate` warns); `--plugin-url <url>` to
  fetch plugin .zip; `skillOverrides` setting now functional
  (`off` / `user-invocable-only` / `name-only`); gateway
  `/v1/models` discovery opt-in via env var
- **2.1.128**: `workspace` is now a reserved MCP server name;
  `--plugin-dir` accepts .zip archives; subprocesses (Bash, hooks,
  MCP, LSP) no longer inherit `OTEL_*` env vars; SDK hosts get
  persistent `localSettings` suggestion for Bash permission
  prompts; `EnterWorktree` branches from local HEAD (later
  reverted in 2.1.133); `init.plugin_errors` includes
  `--plugin-dir` load failures
- **2.1.126**: `claude project purge [path]` to delete all state
  for a project; `--dangerously-skip-permissions` now bypasses
  writes to `.claude/`, `.git/`, `.vscode/`, shell config files;
  `claude_code.skill_activated` OTEL event includes
  `invocation_trigger` (`user-slash`/`claude-proactive`/
  `nested-skill`); `/model` picker reads gateway `/v1/models`;
  Read tool's per-file malware reminder removed
- **2.1.122**: `ANTHROPIC_BEDROCK_SERVICE_TIER` env var
  (`default`/`flex`/`priority`); `/resume` search box accepts PR
  URLs (GitHub, GitHub Enterprise, GitLab, Bitbucket); OTEL
  `claude_code.at_mention` log event; OTEL numeric attrs are now
  numbers, not strings
- **2.1.121**: MCP server `alwaysLoad: true` opt-in to skip
  tool-search deferral; `claude plugin prune` for orphaned
  auto-installed dependencies; PostToolUse hooks can replace tool
  output for any tool via `hookSpecificOutput.updatedToolOutput`
  (was MCP-only); `--dangerously-skip-permissions` no longer
  prompts for `.claude/skills/`, `.claude/agents/`,
  `.claude/commands/`; OTEL adds `stop_reason`,
  `gen_ai.response.finish_reasons`, gated `user_system_prompt`
- **2.1.120**: `claude ultrareview [target]` non-interactive
  subcommand (`--json` for CI); skills can use `${CLAUDE_EFFORT}`
  in content; PowerShell-as-shell on Windows when Git Bash absent;
  `AI_AGENT` env var set for subprocesses (gh attribution);
  `claude plugin validate` accepts top-level `$schema`,
  `version`, `description` in `marketplace.json` and `$schema`
  in `plugin.json`
- **2.1.119**: PostToolUse and PostToolUseFailure hook inputs
  include `duration_ms`; `prUrlTemplate` setting for custom code
  review URLs; `--from-pr` accepts GitLab/Bitbucket/GH-Enterprise
  URLs; `--print` mode honors agent `tools:`/`disallowedTools:`
  frontmatter; `--agent <name>` honors built-in agent
  `permissionMode`; PowerShell tool auto-approval; OTEL
  `tool_result` adds `tool_use_id` and `tool_input_size_bytes`;
  status line stdin includes `effort.level` and `thinking.enabled`
- **2.1.118**: Hooks can invoke MCP tools directly via
  `type: "mcp_tool"`; `claude plugin tag` for release tags;
  `DISABLE_UPDATES` blocks all update paths (stricter than
  `DISABLE_AUTOUPDATER`); `wslInheritsWindowsSettings` policy
  key; `autoMode.allow`/`soft_deny`/`environment` accept
  `"$defaults"` to extend the built-in list; `/cost` and `/stats`
  merged into `/usage`; named custom themes via `/theme` and
  plugin `themes/` directory
- **2.1.117**: `CLAUDE_CODE_FORK_SUBAGENT=1` works on external
  builds; agent `mcpServers` frontmatter loaded for `--agent`
  main-thread sessions; native macOS/Linux builds embed `bfs`/
  `ugrep` (Glob/Grep replaced by Bash tool); `cleanupPeriodDays`
  now sweeps `~/.claude/tasks/`, `shell-snapshots/`, `backups/`;
  Opus 4.7 sessions now use 1M context window for `/context`
- **2.1.111**: `xhigh` effort level for Opus 4.7 (between `high`
  and `max`; falls back to `high` on other models); `max` level
  reintroduced for Opus 4.7 (was removed in 2.1.72); `/effort`
  opens interactive slider; `/less-permission-prompts` skill;
  `/ultrareview` for cloud parallel multi-agent code review;
  PowerShell tool opt-in via `CLAUDE_CODE_USE_POWERSHELL_TOOL`;
  `OTEL_LOG_RAW_API_BODIES` env var; auto mode no longer requires
  `--enable-auto-mode` flag
- **2.1.110**: `/tui [fullscreen]` command and `tui` setting;
  push notification tool (Remote Control); `/focus` command (was
  bundled with Ctrl+O verbose toggle); `autoScrollEnabled`
  config; PreCompact hooks can block compaction by exit code 2
  or `{"decision":"block"}`; `disableBypassPermissionsMode`
  enforced for `setMode:'bypassPermissions'` updates from hooks;
  hardened "Open in editor" against command injection
- **2.1.108**: `ENABLE_PROMPT_CACHING_1H` env var (replaces
  Bedrock-specific variant); `/recap` command and session-recap
  feature; `/undo` aliases `/rewind`; built-in slash commands
  (`/init`, `/review`, `/security-review`) discoverable via Skill
  tool
- **2.1.105**: PreCompact hook event support added; `monitors`
  manifest key for plugin background monitors (auto-armed at
  session start or skill invoke); `/proactive` aliases `/loop`;
  `WebFetch` strips `<style>`/`<script>` before HTML→md;
  stale-worktree cleanup handles squash-merged PRs;
  PreCompact/PostToolUse contracts: `additionalContext` now
  preserved on tool failure
- **2.1.101**: `/team-onboarding` command for ramp-up guides;
  OS CA cert store trusted by default
  (`CLAUDE_CODE_CERT_STORE=bundled` to revert); `permissions.deny`
  rules now correctly override PreToolUse hook
  `permissionDecision: "ask"`; OTEL beta tracing honors
  `OTEL_LOG_USER_PROMPTS`/`OTEL_LOG_TOOL_DETAILS`/
  `OTEL_LOG_TOOL_CONTENT` (sensitive attrs no longer emitted by
  default); SDK `query()` cleans up subprocess on `break`/
  `await using`
- **2.1.98**: Vertex AI interactive setup wizard from login
  screen; `CLAUDE_CODE_PERFORCE_MODE` for read-only file Edit/
  Write hint; **Monitor tool** for streaming events from
  background scripts; subprocess sandboxing with PID namespace
  isolation on Linux (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`,
  `CLAUDE_CODE_SCRIPT_CAPS`); `--exclude-dynamic-system-prompt-sections`
  for cross-user prompt caching; W3C `TRACEPARENT` propagated to
  Bash subprocesses; multiple Bash permission hardening fixes
  (compound commands, env-var prefixes, `/dev/tcp`/`/dev/udp`
  redirects, network-pattern files); `Bash(find:*)` no longer
  auto-approves `find -exec`/`-delete`
- **2.1.97**: `refreshInterval` status line setting; status line
  JSON gains `workspace.git_worktree`; `● N running` indicator
  in `/agents`; image handling unifies pasted/attached images
  with Read tool token budget; auto and bypass-permissions modes
  auto-approve sandbox network access prompts

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
  removed for Opus 4.6 — `max` was reintroduced for Opus 4.7 in
  2.1.111, alongside `xhigh`), CLAUDE.md HTML comments hidden,
  skill hook double-fire
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
