# Claude Code Compatibility Features: March 2026 (Recent)

Feature timeline for Claude Code versions 2.1.63 through 2.1.85,
released in March 2026.

> **See Also**:
> [Features Index](compatibility-features.md) |
> [March 2026 Early](compatibility-features-march2026-early.md) |
> [Plugin Compatibility](compatibility-features-plugin-compat.md)

## Feature Timeline

### Claude Code 2.1.85 (March 2026)

**New Features**:
- ✅ **Hook Conditional `if` Field**: Hooks now support
  an `if` field using permission rule syntax (e.g.,
  `"Bash(git *)"`, `"Edit(*.ts)"`) to filter when they
  run. Only evaluated on tool events (PreToolUse,
  PostToolUse, PostToolUseFailure, PermissionRequest).
  Reduces process spawning: without `if`, every Bash
  call spawns the hook process; with `if`, the condition
  is evaluated in-process before any subprocess.
  - **Impact**: Major performance improvement for hook-
    heavy ecosystems. Night-market's ~25 hooks can now
    filter more precisely, reducing per-tool-call
    overhead significantly.
  - **Affected**: abstract:hook-authoring hook-types
    module (updated), abstract:hooks-eval sdk-hook-types
    module (updated), capabilities-hooks reference
    (updated), hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference
    files updated

- ✅ **MCP Server Env Vars for headersHelper**: New
  `CLAUDE_CODE_MCP_SERVER_NAME` and
  `CLAUDE_CODE_MCP_SERVER_URL` env vars injected into
  `headersHelper` scripts. Allows one helper to serve
  multiple MCP servers by switching on the server name.
  - **Impact**: Simplifies MCP auth configuration
  - **Affected**: None
  - **Action Required**: None

- ✅ **PreToolUse Satisfies AskUserQuestion**: PreToolUse
  hooks can now match `AskUserQuestion` and return
  `updatedInput` alongside `permissionDecision: "allow"`
  to programmatically answer questions. Enables headless
  integrations that collect answers via custom UI (web
  dashboard, Slack bot, etc.).
  - **Impact**: Critical for headless/CI deployments.
    Sessions no longer block on terminal input when a
    PreToolUse hook provides the answer.
  - **Affected**: abstract:hook-authoring hook-types
    module (updated), abstract:hooks-eval sdk-hook-types
    module (updated)
  - **Action Required**: Done - hook reference files
    updated

- ✅ **Transcript Timestamp Markers**: Timestamps in
  transcripts when `/loop` and `CronCreate` tasks fire.
  - **Impact**: Observability improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **MCP OAuth RFC 9728**: MCP OAuth now follows RFC
  9728 Protected Resource Metadata discovery to locate
  authorization servers, replacing the older
  `.well-known/oauth-authorization-server` approach.
  - **Impact**: Better MCP OAuth interoperability with
    external identity providers (Entra ID, etc.)
  - **Affected**: None
  - **Action Required**: None

- ✅ **Organization Plugin Blocking**: Plugins blocked by
  managed-settings.json (`blockedMarketplaces`,
  `strictKnownMarketplaces`) can no longer be installed
  or enabled, and are hidden from marketplace views.
  - **Impact**: Enterprise governance improvement
  - **Affected**: leyline:update-all-plugins command
    (updated)
  - **Action Required**: Done

- ✅ **OTEL tool_parameters Gated**: `tool_parameters`
  in OpenTelemetry `tool_result` events gated behind
  `OTEL_LOG_TOOL_DETAILS=1`. Raw tool arguments (file
  paths, commands, URLs) are no longer logged by default.
  - **Impact**: Privacy improvement for enterprise OTEL
    deployments
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **`/compact` Context Exceeded**: Fixed `/compact`
  failing when the conversation is too large for the
  compact request itself to fit. Previously a deadlock:
  compaction was most needed when it could not run.
  - **Impact**: Critical compaction reliability fix
  - **Affected**: conserve:context-optimization
    mecw-principles module (updated)
  - **Action Required**: Done

- ✅ **MCP Step-Up Authorization**: Fixed re-
  authorization flow when a refresh token exists and the
  server requests elevated scopes via `403
  insufficient_scope`.
  - **Impact**: MCP OAuth reliability fix
  - **Affected**: None
  - **Action Required**: None

- ✅ **`deniedMcpServers` Fix**: Fixed setting not
  blocking claude.ai MCP servers.
  - **Impact**: Enterprise MCP governance fix
  - **Affected**: None
  - **Action Required**: None

- ✅ **Worktree in Non-Git Repos**: Fixed `--worktree`
  exiting with error in non-git repositories before
  WorktreeCreate hook could run.
  - **Impact**: Worktree reliability fix
  - **Affected**: conjure:agent-teams spawning-patterns
    module (updated)
  - **Action Required**: Done

- ✅ **Terminal Enhanced Keyboard Mode**: Fixed terminal
  left in enhanced keyboard mode after exit in Ghostty,
  Kitty, WezTerm (Kitty keyboard protocol). Ctrl+C and
  Ctrl+D now work correctly after quitting.
  - **Impact**: Critical terminal UX fix
  - **Affected**: None - automatic fix
  - **Action Required**: None

- ✅ **Various Fixes**: Plugin enable/disable location
  mismatch, switch_display multi-monitor, OTEL exporter
  crash, diff syntax highlighting, remote session memory
  leak, ECONNRESET on edge churn, prompts stuck in queue,
  Python SDK MCP servers dropped, raw key sequences over
  SSH, Remote Control stuck status, shift+enter newline,
  stale content during scroll.
  - **Impact**: Multiple reliability and UX fixes
  - **Affected**: None - automatic fixes
  - **Action Required**: None

**Improvements**:
- ✅ **@-mention Performance**: Improved file autocomplete
  on large repositories.
  - **Impact**: UX improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **PowerShell Detection**: Improved dangerous command
  detection for PowerShell.
  - **Impact**: Windows safety improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **Scroll Performance**: Replaced WASM yoga-layout
  with pure TypeScript. Reduced UI stutter during
  compaction on large sessions.
  - **Impact**: UI performance improvement
  - **Affected**: None
  - **Action Required**: None

### Claude Code 2.1.84 (March 2026)

**New Features**:
- ✅ **PowerShell Tool (Windows Preview)**: Opt-in
  preview via `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`.
  Auto-detects `pwsh.exe` (7+) with fallback to
  `powershell.exe` (5.1). No sandboxing yet.
  - **Impact**: Windows development workflow
  - **Affected**: abstract model-optimization-guide
    (updated)
  - **Action Required**: Done

- ✅ **Model Capability Env Vars**:
  `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL_SUPPORTED_CAPABILITIES`
  for third-party providers: `effort`, `max_effort`,
  `thinking`, `adaptive_thinking`,
  `interleaved_thinking`. Plus `_MODEL_NAME` and
  `_MODEL_DESCRIPTION` for `/model` picker labels.
  - **Impact**: Third-party provider model configuration
  - **Affected**: abstract model-optimization-guide
    (updated)
  - **Action Required**: Done

- ✅ **TaskCreated Hook**: Fires when a task is created
  via TaskCreate. **Blockable** (exit code 2). Input
  includes `task_id`, `task_subject`,
  `task_description`, `teammate_name`, `team_name`.
  - **Impact**: Enables task audit and policy enforcement
  - **Affected**: All 4 hook reference files (updated)
  - **Action Required**: Done

- ✅ **WorktreeCreate HTTP Hook Support**: HTTP hooks for
  WorktreeCreate can return worktree path via
  `hookSpecificOutput.worktreePath`. Enables remote
  worktree creation services.
  - **Impact**: Worktree automation
  - **Affected**: All 4 hook reference files (updated)
  - **Action Required**: Done

- ✅ **`allowedChannelPlugins` Managed Setting**: Team/
  enterprise admin setting for channel plugin allowlist.
  - **Impact**: Enterprise governance
  - **Affected**: None
  - **Action Required**: None

- ✅ **Idle-Return Prompt (75+ min)**: Nudges users
  returning after 75+ minutes to `/clear`, reducing
  token re-caching on stale sessions.
  - **Impact**: Token conservation
  - **Affected**: conserve:context-optimization
    mecw-principles module (updated)
  - **Action Required**: Done

- ✅ **MCP Tool Descriptions Capped at 2KB**: Prevents
  OpenAPI-generated servers from bloating context.
  Duplicate servers (local + claude.ai) deduplicated;
  local config wins.
  - **Impact**: Context conservation
  - **Affected**: conserve:context-optimization
    mecw-principles module (updated)
  - **Action Required**: Done

- ✅ **Rules/Skills Paths YAML Globs**: Frontmatter
  `paths` field now accepts a YAML list of globs with
  brace expansion. Skills auto-load only for matching
  files.
  - **Impact**: Skill activation precision
  - **Affected**: None
  - **Action Required**: None

- ✅ **Deep Links Open Preferred Terminal**: `claude-cli://`
  deep links now open in preferred terminal.
  - **Impact**: UX improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **Token Display**: Counts >=1M display as "1.5m"
  instead of "1512.6k".
  - **Impact**: Display improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **Global System-Prompt Caching**: Works when
  ToolSearch is enabled, including with MCP tools.
  - **Impact**: Token cost reduction
  - **Affected**: conserve:context-optimization
    mecw-principles module (updated)
  - **Action Required**: Done

### Claude Code 2.1.83 (March 2026)

**New Features**:
- ✅ **`managed-settings.d/` Drop-In Directory**: Separate
  teams deploy independent policy fragments that merge
  alphabetically. Arrays concatenated and deduplicated,
  objects deep-merged, scalars overridden. Use numeric
  prefixes for ordering (e.g., `10-telemetry.json`).
  - **Impact**: Enterprise deployment flexibility
  - **Affected**: leyline:update-all-plugins command
    (updated)
  - **Action Required**: Done

- ✅ **CwdChanged and FileChanged Hooks**: New hook events
  for reactive environment management (e.g., direnv).
  CwdChanged fires on directory change (non-blockable, no
  matcher). FileChanged fires on watched file change
  (non-blockable, matcher on filename).
  - **Impact**: Enables environment-reactive hooks
  - **Affected**: All 4 hook reference files (updated)
  - **Action Required**: Done

- ✅ **`sandbox.failIfUnavailable` Setting**: Exit with
  error when sandbox cannot start instead of running
  unsandboxed. For managed-settings deployments requiring
  sandbox as a hard gate.
  - **Impact**: Enterprise security
  - **Affected**: None
  - **Action Required**: None

- ✅ **`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`**: Strips
  Anthropic and cloud provider credentials from Bash
  tool, hooks, and MCP stdio server environments.
  - **Impact**: Credential leakage prevention
  - **Affected**: None
  - **Action Required**: None

- ✅ **Agent `initialPrompt` Frontmatter**: Agents can
  declare `initialPrompt` to auto-submit a first turn on
  spawn without parent providing initial message.
  - **Impact**: Agent automation improvement
  - **Affected**: conjure:agent-teams spawning-patterns
    module (updated)
  - **Action Required**: Done

- ✅ **Plugin Options (`manifest.userConfig`)**: Plugins
  can prompt for configuration at enable time.
  `sensitive: true` values stored in keychain (macOS) or
  protected credentials file. Available as
  `${user_config.KEY}` substitution and
  `CLAUDE_PLUGIN_OPTION_<KEY>` env vars.
  - **Impact**: Plugin configuration improvement
  - **Affected**: leyline:update-all-plugins command
    (updated)
  - **Action Required**: Done

- ✅ **Transcript Search**: Press `/` in transcript mode
  (`Ctrl+O`) to search, `n`/`N` to step through.
  - **Impact**: Observability improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **MEMORY.md 25KB Truncation**: First 200 lines or
  25KB (whichever first) loaded per session. Content
  beyond threshold not loaded.
  - **Impact**: Memory management change. Move detailed
    notes to separate files read on demand.
  - **Affected**: None (already following this pattern)
  - **Action Required**: None

- ✅ **TaskOutput Deprecated**: Use `Read` on background
  task output file path instead.
  - **Impact**: Tool usage change
  - **Affected**: None
  - **Action Required**: None

**Changes**:
- ✅ **Stop Agents Keybinding**: Changed from `Ctrl+F` to
  `Ctrl+X Ctrl+K` to stop shadowing readline
  forward-char.
  - **Impact**: Keybinding change
  - **Affected**: None
  - **Action Required**: None

**Fixes**: 30+ bug fixes including caffeinate process,
background subagent visibility after compaction, SDK
session history on resume, stale slash commands, tool
result file cleanup, voice mode Linux ALSA errors, and
many more.

### Claude Code 2.1.81 (March 2026)

**New Features**:
- ✅ **`--bare` Flag**: Skips hooks, LSP, plugin sync,
  skill walks, auto-memory, OAuth/keychain auth, CLAUDE.md
  and `.mcp.json` loading. Requires `ANTHROPIC_API_KEY` or
  `apiKeyHelper` via `--settings`. Fastest startup for
  CI/scripted use. Will become default for `-p` in future.
  - **Impact**: Significant for CI/CD and Agent SDK
    workflows. Deterministic, machine-independent
    execution.
  - **Affected**: conjure:agent-teams spawning-patterns
    module (updated)
  - **Action Required**: Done

- ✅ **`--channels` Permission Relay**: Channel servers
  with `permission` capability can forward tool approval
  prompts to remote devices (phone). First answer wins.
  - **Impact**: Remote approval workflows
  - **Affected**: None
  - **Action Required**: None

- ✅ **MCP OAuth CIMD (SEP-991)**: Support for Client ID
  Metadata Document for servers without Dynamic Client
  Registration.
  - **Impact**: MCP OAuth interoperability
  - **Affected**: None
  - **Action Required**: None

**Fixes**: OAuth token refresh, voice mode, Node.js 18
crash, plugin hook persistence, Remote Control title/exit,
tmux clipboard race.

### Claude Code 2.1.80 (March 2026)

**New Features**:
- ✅ **`rate_limits` Statusline Field**: Displays 5-hour
  and 7-day rate limit usage with `used_percentage` and
  `resets_at`.
  - **Impact**: Rate limit visibility
  - **Affected**: egregore:summon budget module (updated)
  - **Action Required**: Done

- ✅ **`effort` Frontmatter for Skills/Commands**:
  Overrides session effort level when skill is active.
  Options: `low`, `medium`, `high`, `max`.
  - **Impact**: Skill-level effort control. Replaces
    `model_hint` pattern for effort routing.
  - **Affected**: abstract model-optimization-guide
    (updated)
  - **Action Required**: Done

- ✅ **`--channels` (Research Preview)**: MCP servers
  push messages into sessions. Ships with Telegram,
  Discord, iMessage, fakechat. Requires claude.ai login.
  Enterprise: `channelsEnabled` managed setting.
  - **Impact**: New interaction paradigm
  - **Affected**: None
  - **Action Required**: None

- ✅ **`source: 'settings'` Plugin Source**: Declare
  plugin entries inline in settings.json.
  - **Impact**: Plugin configuration simplification
  - **Affected**: leyline:update-all-plugins command
    (updated)
  - **Action Required**: Done

**Fixes**: `--resume` dropping parallel tool results,
voice mode WebSocket, `/sandbox` tab switching, managed
settings startup. **Performance**: ~80MB startup savings
on large repos.

### Claude Code 2.1.79 (March 2026)

**New Features**:
- ✅ **`--console` Auth Flag**: `claude auth login
  --console` for Anthropic Console (API billing) auth.
  - **Impact**: Authentication option
  - **Affected**: None
  - **Action Required**: None

- ✅ **Multi-Directory `CLAUDE_CODE_PLUGIN_SEED_DIR`**:
  Supports platform path delimiter (`:` Unix, `;`
  Windows) for multiple seed directories.
  - **Impact**: CI/container deployment
  - **Affected**: leyline:update-all-plugins command
    (updated)
  - **Action Required**: Done

**Fixes**: `-p` hanging without stdin, Ctrl+C in print
mode, SessionEnd hooks on `/resume`. **Performance**:
~18MB startup savings, 2-minute non-streaming timeout.

### Claude Code 2.1.78 (March 2026)

**New Features**:
- ✅ **StopFailure Hook**: Fires on API error (rate
  limit, auth failure, etc.). Non-blockable. Matcher on
  error type: `rate_limit`, `authentication_failed`,
  `billing_error`, `invalid_request`, `server_error`,
  `max_output_tokens`, `unknown`.
  - **Impact**: Error monitoring and alerting
  - **Affected**: All 4 hook reference files (updated)
  - **Action Required**: Done

- ✅ **`${CLAUDE_PLUGIN_DATA}` Variable**: Persistent
  directory for plugin state surviving updates. Resolves
  to `~/.claude/plugins/data/{id}/`. `/plugin uninstall`
  prompts before deletion; `--keep-data` preserves it.
  - **Impact**: Plugin state persistence
  - **Affected**: leyline:update-all-plugins command
    (updated)
  - **Action Required**: Done

- ✅ **Agent Frontmatter: `effort`, `maxTurns`,
  `disallowedTools`**: Plugin-shipped agents support
  effort level, turn limits, and tool restrictions.
  Security: `hooks`, `mcpServers`, `permissionMode`
  NOT supported for plugin agents.
  - **Impact**: Agent configuration improvement
  - **Affected**: conjure:agent-teams spawning-patterns
    module (updated), abstract model-optimization-guide
    (updated)
  - **Action Required**: Done

**Fixes**: Sandbox git log, `--resume` truncation on
large sessions, infinite stop hook loop, MCP deny rules,
sandbox allowWrite paths, vim keybinding, voice mode WSL2,
worktree skills loading. **Security**: Sandbox silent
disable warning, protected directories in bypassPermissions
mode.

### Claude Code 2.1.77 (March 2026)

**New Features**:
- ✅ **Output Token Limit Increase**: Opus 4.6 default
  64k (was 32k), upper bound 128k for Opus/Sonnet 4.6.
  Override via `CLAUDE_CODE_MAX_OUTPUT_TOKENS`.
  - **Affected**: model-optimization-guide, mecw-principles
- ✅ **`allowRead` Sandbox Setting**: Re-allows reads
  within `denyRead` regions. Enterprise:
  `allowManagedReadPathsOnly`.
- ✅ **`/copy N`**: Copies Nth-latest assistant response.

**Bug Fixes (Security)**:
- ✅ **PreToolUse "allow" Bypassing Deny Rules**: Hook
  allow no longer bypasses deny rules. Precedence:
  managed deny > hook deny > perm deny > hook allow.
  - **Affected**: all 4 hook reference files (updated)

**Bug Fixes**:
- ✅ **Compound Bash "Always Allow"**: Now saves per-
  subcommand rules instead of full compound string.
- ✅ **Auto-Updater Memory Leak**: Overlapping downloads
  accumulated ~27GB/hour. Response bodies now consumed.
- ✅ **`--resume` Transcript Truncation**: Race between
  memory-extraction writes and transcript read.
- ✅ **Write Tool CRLF**: Now preserves line endings.
- ✅ **Progress Messages Memory Growth**: Survived
  compaction causing unbounded growth in long sessions.
  - **Affected**: mecw-principles (updated)
- ✅ **Stale Worktree Race**: Cleanup could delete
  worktrees being actively resumed from crash.
  - **Affected**: spawning-patterns (updated)
- ✅ **Teammate Panes**: Not closing when leader exits.
  - **Affected**: health-monitoring (updated)
- ✅ `DISABLE_EXPERIMENTAL_BETAS` beta fields, cost
  tracking non-streaming, bash temp spaces, git-subdir
  plugin cache, Desktop OAuth, 20+ UI/UX fixes (paste,
  vim, tmux, iTerm2, CJK, hyperlinks, etc.).

**Improvements**:
- ✅ **macOS Startup ~60ms**: Parallel keychain reads.
- ✅ **`--resume` 45% Faster**: ~100-150MB less memory.
- ✅ **Esc Aborts Non-Streaming**: Works in both modes.
- ✅ **`plugin validate`**: Checks frontmatter + hooks.
  - **Affected**: update-all-plugins (updated)
- ✅ **Background Bash 5GB Limit**: Kills runaway tasks.
  - **Affected**: health-monitoring (updated)
- ✅ Sessions auto-named from plans, apiKeyHelper >10s
  notice, headless plugin seed dir fix.

**Changes**:
- ✅ **Agent `resume` Removed**: Use
  `SendMessage({to: agentId})`.
  - **Affected**: spawning-patterns, health-monitoring
- ✅ **SendMessage Auto-Resumes**: Stopped agents resume
  in background.
  - **Affected**: health-monitoring (updated)
- ✅ **`/fork` Renamed to `/branch`**: Alias preserved.

### Claude Code 2.1.76 (March 2026)

**New Features**:
- ✅ **MCP Elicitation Support**: Form mode (inline
  fields) and URL mode (external URL for OAuth/creds).
  Three-action response: `accept`/`decline`/`cancel`.
  - **Affected**: all 4 hook reference files (updated)
- ✅ **Elicitation/ElicitationResult Hooks**: Both
  blockable. Matcher on `mcp_server_name`. Support
  `hookSpecificOutput` for auto-fill/override.
  - **Affected**: all 4 hook reference files (updated)
- ✅ **PostCompact Hook**: Non-blockable. Input includes
  `trigger` and `compact_summary`. Matcher on trigger.
  Re-inject instructions post-compaction (PreCompact
  content gets summarized; PostCompact is verbatim).
  - **Affected**: all 4 hook reference files (updated)
- ✅ **`-n` / `--name` CLI Flag**: Session display name
  at startup. Appears on prompt bar and Remote Control.
  - **Affected**: spawning-patterns (updated)
- ✅ **`worktree.sparsePaths`**: Sparse-checkout for
  monorepos. `"worktree": {"sparsePaths": [...]}`.
  - **Affected**: spawning-patterns (updated)
- ✅ **`/effort` Slash Command**: Direct effort control.
  - **Affected**: model-optimization-guide (updated)
- ✅ **`feedbackSurveyRate` Setting**: Enterprise session
  quality survey (float 0.0-1.0).

**Bug Fixes**:
- ✅ **Deferred Tools Schema Loss**: Schemas lost after
  compaction. Now persisted in registry.
  - **Affected**: mecw-principles (updated)
- ✅ **Auto-Compaction Circuit Breaker**: Stops after 3
  consecutive failures.
  - **Affected**: mecw-principles (updated)
- ✅ **"Context limit reached" with `model:` Frontmatter**:
  Used frontmatter model's 200K window instead of
  session's actual 1M window.
  - **Affected**: mecw-principles, model-optimization-guide
- ✅ **Adaptive Thinking Error**: Non-standard model
  strings now fall back to standard thinking.
  - **Affected**: model-optimization-guide (updated)
- ✅ Bash `#` permission, "Don't Ask Again" pipes, slash
  commands "Unknown Skill", plan re-approval, voice mode
  keypresses/Windows, MCP reconnect spinner, LSP
  registration, clipboard tmux SSH, `/export` path,
  transcript scroll, Escape login, Remote Control fixes,
  soft-hidden commands, VSCode gitignore commas.

**Improvements**:
- ✅ **Worktree Startup Performance**: Direct git ref
  reads, skip redundant fetch.
  - **Affected**: spawning-patterns (updated)
- ✅ **Background Agent Partial Results**: Killing
  preserves partial output in context.
  - **Affected**: health-monitoring (updated)
- ✅ **Model Fallback Visible**: Always shown with
  human-friendly names.
  - **Affected**: model-optimization-guide (updated)
- ✅ **Stale Worktree Cleanup**: Auto-cleaned after
  interrupted parallel runs.
  - **Affected**: spawning-patterns (updated)
- ✅ Remote Control titles, `/voice` language display,
  blockquote readability.

**Changes**:
- ✅ **`--plugin-dir` Single Path**: Use repeated flags.
  - **Affected**: update-all-plugins (updated)

### Claude Code 2.1.75 (March 2026)

**New Features**:
- ✅ **1M Context Window Default for Max/Team/Enterprise**:
  No extra usage required. Opt out with
  `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`.
  - **Affected**: mecw-principles, model-optimization-guide,
    egregore budget, clear-context (all updated)
- ✅ **`/color` Command**: Session prompt-bar border color.
  Does not persist across resume.
  - **Affected**: spawning-patterns (updated)
- ✅ **Session Name on Prompt Bar**: `/rename` displays on
  prompt bar and terminal title via OSC 0/2 sequences.
  - **Affected**: spawning-patterns (updated)
- ✅ **Last-Modified Timestamps on Memory Files**: Auto-
  injected into context for freshness reasoning.
- ✅ **Hook Source Display**: Permission prompts show
  `settings`/`plugin`/`skill` source.
  - **Affected**: all 4 hook reference files (updated)

**Bug Fixes**:
- ✅ **Bash Tool `!` in Piped Commands**: `jq 'select(.x
  != .y)'` now works. Escaping injected `< /dev/null`.
- ✅ **Token Estimation Over-Counting**: `thinking` and
  `tool_use` blocks triggered premature compaction.
  - **Affected**: mecw-principles, egregore budget (updated)
- ✅ **Managed-Disabled Plugins Hidden**: No longer shown
  in `/plugin` Installed tab.
  - **Affected**: update-all-plugins (updated)
- ✅ Voice mode fresh install, header model name, attachment
  crash, corrupted marketplace path, `/resume` session
  names, `/status` Esc key, plan input handling, agent
  teams footer hint fixes.

**Changes**:
- ✅ **macOS Startup ~60ms Faster**: Skips unnecessary
  subprocess spawns on non-MDM machines.
- ✅ **Async Hook Messages Suppressed**: Visible via
  `--verbose`, transcript mode, or `Ctrl+O`.
  - **Affected**: all 4 hook reference files (updated)

**Breaking Change**:
- ✅ **Windows Managed Settings Path**: Removed
  `C:\ProgramData\ClaudeCode\` fallback. Use
  `C:\Program Files\ClaudeCode\managed-settings.json`.
  - **Affected**: update-all-plugins (updated)

### Claude Code 2.1.74 (March 2026)

**New Features**:
- ✅ **`/context` Actionable Suggestions**: The `/context`
  command now identifies context-heavy tools, memory bloat,
  and capacity warnings with specific optimization tips.
  Previously it showed a breakdown; now it recommends
  actions (e.g., "compact to reclaim X tokens", "disable
  unused MCP server Y").
  - **Impact**: Directly supports conserve:context-optimization
    workflows. The `/context` command becomes a diagnostic
    tool rather than just a display.
  - **Affected**: conserve:context-optimization mecw-principles
    module (updated)
  - **Action Required**: Done - mecw-principles module updated

- ✅ **`autoMemoryDirectory` Setting**: Configure a custom
  directory for auto-memory storage in settings.json. Default
  remains per-working-tree under `.claude/`. Accepted from
  policy, local, and user settings only (NOT project settings,
  to prevent a shared repo from redirecting memory writes to
  sensitive locations). Supports tilde expansion.
  - **Impact**: Informational for users wanting custom memory
    paths. No impact on night-market's memory-palace plugin
    which uses its own storage.
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **Streaming API Memory Leak**: Fixed memory leak where
  streaming API response buffers were not released when the
  generator was terminated early, causing unbounded RSS
  growth on the Node.js/npm code path. Does not affect the
  native binary.
  - **Impact**: Long-running sessions on the npm install path
    no longer leak memory. Critical for CI/automation
    workflows using `--print` or Agent SDK on Node.js.
  - **Affected**: None - automatic fix
  - **Action Required**: None

- ✅ **Managed Policy Ask Rules Bypass**: Fixed managed policy
  `ask` rules being bypassed by user `allow` rules or skill
  `allowed-tools`. Previously, a user-level allow rule could
  override an organization's managed ask policy, defeating
  the compliance purpose.
  - **Impact**: Enterprise governance fix. Organizations using
    managed settings to enforce `ask` policies for sensitive
    tools now get correct enforcement. Skills declaring
    `allowed-tools` can no longer bypass managed ask rules.
  - **Affected**: None - no managed settings in our ecosystem
  - **Action Required**: None

- ✅ **Full Model IDs in Agent Frontmatter**: Fixed full model
  IDs (e.g., `claude-opus-4-5`) being silently ignored in
  agent frontmatter `model:` field and `--agents` JSON config.
  Agents now accept the same model values as `--model`:
  aliases (`opus`, `sonnet`, `haiku`), full model IDs
  (`claude-opus-4-6`), and provider-specific strings (Bedrock
  ARNs, Vertex version names, Foundry deployment names).
  - **Impact**: Agent definitions can now pin specific model
    versions via full model IDs. Previously only aliases
    worked in frontmatter; full IDs were silently ignored,
    falling back to the default model.
  - **Affected**: abstract model-optimization-guide (updated),
    abstract:escalation-governance (updated),
    conjure:agent-teams spawning-patterns module (updated)
  - **Action Required**: Done - all 3 files updated

- ✅ **MCP OAuth Port Conflict**: Fixed MCP OAuth
  authentication hanging when the callback port is already
  in use
  - **Impact**: MCP OAuth reliability improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **MCP OAuth Refresh with HTTP 200 Errors**: Fixed MCP
  OAuth refresh never prompting for re-auth after the refresh
  token expires, for OAuth servers that return errors with
  HTTP 200 (e.g., Slack)
  - **Impact**: MCP integrations with Slack and similar servers
    now correctly prompt for re-authentication
  - **Affected**: None
  - **Action Required**: None

- ✅ **SessionEnd Hooks Timeout**: Fixed SessionEnd hooks
  being killed after 1.5 seconds on exit regardless of
  `hook.timeout` setting. Now configurable via
  `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` env var.
  - **Impact**: Plugins with SessionEnd hooks that need more
    than 1.5s (e.g., metrics upload, state persistence,
    notification) now complete reliably. Previously, hooks
    with `timeout: 30` were still killed at 1.5s.
  - **Affected**: abstract:hook-authoring hook-types module
    (updated), abstract:hooks-eval sdk-hook-types module
    (updated), capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files
    updated

- ✅ **Voice Mode macOS Entitlement**: Fixed voice mode
  silently failing on macOS native binary for users whose
  terminal had never been granted microphone permission.
  Binary now includes the `audio-input` entitlement.
  - **Impact**: macOS voice mode reliability
  - **Affected**: None
  - **Action Required**: None

- ✅ **Plugin Install REPL Fix**: Fixed `/plugin install`
  failing inside the REPL for marketplace plugins with
  local sources
  - **Impact**: Plugin installation reliability
  - **Affected**: None
  - **Action Required**: None

- ✅ **Marketplace Git Submodules**: Fixed marketplace update
  not syncing git submodules. Plugin sources in submodules no
  longer break after update.
  - **Impact**: Plugin update reliability for marketplace
    plugins that use git submodules
  - **Affected**: leyline:update-all-plugins command (updated)
  - **Action Required**: Done - update-all-plugins.md updated

- ✅ **Unknown Slash Command Input**: Fixed unknown slash
  commands with arguments silently dropping input. Now shows
  input as a warning.
  - **Impact**: UX improvement; prevents silent data loss
    from typos in slash command names
  - **Affected**: None
  - **Action Required**: None

- ✅ **RTL Text Rendering**: Fixed Hebrew, Arabic, and other
  RTL text not rendering correctly in Windows Terminal,
  conhost, and VS Code integrated terminal
  - **Impact**: Platform fix for RTL language users
  - **Affected**: None
  - **Action Required**: None

- ✅ **LSP Servers on Windows**: Fixed LSP servers not working
  on Windows due to malformed file URIs
  - **Impact**: Windows platform fix
  - **Affected**: None
  - **Action Required**: None

**Changes**:
- ✅ **`--plugin-dir` Override Behavior**: Local dev copies
  now override installed marketplace plugins with the same
  name, unless that plugin is force-enabled by managed
  settings. Previously, marketplace installs took precedence
  over `--plugin-dir` local copies.
  - **Impact**: Plugin development workflow improvement.
    Developers using `--plugin-dir` for local testing no
    longer need to uninstall the marketplace version first.
  - **Affected**: leyline:update-all-plugins command (updated)
  - **Action Required**: Done - update-all-plugins.md updated

**New Hook Events Discovered (documentation refresh)**:
- ✅ **New Hook Events**: The 2.1.74 hooks documentation
  reveals several hook events not previously tracked:
  `CwdChanged` (working directory changes), `FileChanged`
  (watched file changes), `PostCompact` (after compaction),
  `TaskCreated` (task created, blockable), `StopFailure`
  (API error, no decision control), `Elicitation` (MCP
  server requests user input), `ElicitationResult` (user
  responds to elicitation)
  - **Impact**: Expands the hook event surface significantly.
    These events enable new plugin capabilities: directory
    change tracking, file watch integration, compaction
    response, MCP elicitation interception.
  - **Affected**: abstract:hook-authoring hook-types module
    (updated), abstract:hooks-eval sdk-hook-types module
    (updated), capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files
    updated with new events

**Platform Fixes** (no plugin impact):
- ✅ VS Code delete button fix for Untitled sessions
- ✅ VS Code scroll wheel responsiveness improvement

### Claude Code 2.1.73 (March 2026)

**New Features**:
- ✅ **`modelOverrides` Setting**: Maps model picker entries to
  custom provider model IDs (Bedrock inference profile ARNs,
  Vertex version names, Foundry deployment names). Configured
  in settings.json as a key-value map from Anthropic model IDs
  to provider-specific strings. When a user selects a model in
  `/model`, Claude Code sends the mapped provider ID instead.
  Versions without an override fall back to the built-in
  provider model ID or startup-discovered inference profiles.
  - **Impact**: Enterprise teams on Bedrock/Vertex/Foundry can
    now route model picker selections to specific inference
    profiles without relying solely on environment variables.
    Complements `ANTHROPIC_DEFAULT_OPUS_MODEL` and similar
    env vars for multi-version routing.
  - **Affected**: abstract model-optimization-guide (updated
    with modelOverrides section), abstract:escalation-governance
    (updated with provider model routing note)
  - **Action Required**: Done - both files updated

- ✅ **SSL Certificate Error Guidance**: OAuth login and
  connectivity checks now surface actionable guidance when
  failing due to SSL certificate errors (corporate proxies,
  `NODE_EXTRA_CA_CERTS` misconfiguration)
  - **Impact**: Enterprise users behind corporate proxies get
    clear error messages pointing to root causes instead of
    opaque TLS failures
  - **Affected**: None - UX improvement, no plugin impact
  - **Action Required**: None

- ✅ **`/effort` Works While Responding**: `/effort` now works
  while Claude is responding, matching `/model` behavior.
  Allows dynamic effort adjustment mid-turn.
  - **Impact**: UX improvement for effort control workflows
  - **Affected**: None
  - **Action Required**: None

- ✅ **Up Arrow Interrupted Prompt Restore**: Up arrow after
  interrupting Claude now restores the interrupted prompt and
  rewinds the conversation in one step
  - **Impact**: UX improvement for iterative workflows
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **CPU Freeze on Permission Prompts**: Fixed freezes and
  100% CPU loops triggered by permission prompts for complex
  bash commands
  - **Impact**: Critical stability fix. Permission-heavy
    workflows (hook validation, sandbox enforcement) no longer
    risk hanging the session.
  - **Affected**: None - automatic fix
  - **Action Required**: None

- ✅ **Skill File Change Deadlock**: Fixed a deadlock that
  froze Claude Code when many skill files changed at once
  (e.g., during `git pull` in a repo with a large
  `.claude/skills/` directory)
  - **Impact**: Critical fix for plugin development and update
    workflows. Night-market's 200+ skill files made this
    deadlock likely during `git pull` or branch switches.
  - **Affected**: None - automatic fix
  - **Action Required**: None

- ✅ **Concurrent Session Bash Output Loss**: Fixed Bash tool
  output being lost when running multiple Claude Code sessions
  in the same project directory
  - **Impact**: Multi-session workflows (e.g., egregore + manual
    session in same repo) no longer lose bash output
  - **Affected**: None - automatic fix
  - **Action Required**: None

- ✅ **Subagent Model Downgrade on Providers**: Fixed subagents
  with `model: opus`/`sonnet`/`haiku` being silently downgraded
  to older model versions on Bedrock, Vertex, and Microsoft
  Foundry. Previously, the model alias in agent frontmatter
  resolved to an older version (e.g., Opus 4.1) instead of the
  current version (Opus 4.6) on these providers.
  - **Impact**: All agent dispatch workflows on Bedrock/Vertex/
    Foundry now get the correct model version. Previously,
    agents dispatched with `model: opus` could silently run on
    Opus 4.1 instead of 4.6.
  - **Affected**: conjure:agent-teams spawning-patterns module
    (updated with fix note), conjure:agent-teams
    health-monitoring module (updated), abstract:escalation-
    governance (updated)
  - **Action Required**: Done - all 3 files updated

- ✅ **Background Bash Process Cleanup**: Fixed background bash
  processes spawned by subagents not being cleaned up when the
  agent exits. Previously, orphaned processes accumulated in
  long sessions.
  - **Impact**: Long-running agent workflows (egregore, do-issue
    parallel dispatch) no longer leak bash processes
  - **Affected**: conjure:agent-teams health-monitoring module
    (updated)
  - **Action Required**: Done - health-monitoring module updated

- ✅ **SessionStart Hooks Double-Fire on Resume**: Fixed
  SessionStart hooks firing twice when resuming a session via
  `--resume` or `--continue`. Hooks now fire exactly once per
  session start.
  - **Impact**: Plugins with SessionStart hooks (conserve,
    imbue, egregore, tome) no longer produce duplicate
    initialization when sessions are resumed. Metrics and
    logging hooks show correct counts.
  - **Affected**: abstract:hook-authoring hook-types module
    (updated), abstract:hooks-eval sdk-hook-types module
    (updated), capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files
    updated

- ✅ **JSON-Output Hooks System-Reminder Injection**: Fixed
  JSON-output hooks injecting no-op system-reminder messages
  into the model's context on every turn. This caused token
  waste and context pollution.
  - **Impact**: Hooks using JSON output format no longer
    inject spurious system-reminder messages. Reduces token
    waste per turn for any workflow using JSON-output hooks.
  - **Affected**: abstract:hook-authoring hook-types module
    (updated), abstract:hooks-eval sdk-hook-types module
    (updated), capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files
    updated

- ✅ **`/loop` Available on All Providers**: Fixed `/loop`
  not being available on Bedrock/Vertex/Foundry and when
  telemetry was disabled
  - **Impact**: Egregore's `CronCreate`-based scheduling and
    `/loop` command now work on all provider configurations.
    Previously limited to first-party API users.
  - **Affected**: egregore:orchestrator agent (updated),
    egregore:summon budget module (updated)
  - **Action Required**: Done - both egregore files updated

- ✅ **`/resume` Self-Reference**: Fixed `/resume` showing
  the current session in the picker
  - **Impact**: UX fix for session management
  - **Affected**: None
  - **Action Required**: None

- ✅ **`/ide` Install Crash**: Fixed `/ide` crashing with
  `onInstall is not defined` when auto-installing the extension
  - **Impact**: IDE integration reliability
  - **Affected**: None
  - **Action Required**: None

- ✅ **Voice Mode Session Corruption**: Fixed voice mode
  session corruption when a slow connection overlaps a new
  recording
  - **Impact**: Voice mode reliability
  - **Affected**: None
  - **Action Required**: None

- ✅ **Linux Sandbox ripgrep**: Fixed Linux sandbox failing to
  start with "ripgrep (rg) not found" on native builds
  - **Impact**: Linux platform fix
  - **Affected**: None
  - **Action Required**: None

- ✅ **Linux glibc 2.26 Compatibility**: Fixed Linux native
  modules not loading on Amazon Linux 2 and other glibc 2.26
  systems
  - **Impact**: Broader Linux distribution support
  - **Affected**: None
  - **Action Required**: None

- ✅ **Remote Control Image Error**: Fixed "media_type: Field
  required" API error when receiving images via Remote Control
  - **Impact**: Remote control reliability
  - **Affected**: None
  - **Action Required**: None

**Improvements**:
- ✅ **IDE Detection Speed**: Improved IDE detection speed at
  startup
  - **Impact**: Faster session initialization
  - **Affected**: None
  - **Action Required**: None

- ✅ **macOS Clipboard Performance**: Improved clipboard image
  pasting performance on macOS
  - **Impact**: Faster image workflows
  - **Affected**: None
  - **Action Required**: None

- ✅ **Voice Mode Retry**: Improved voice mode to automatically
  retry transient connection failures during rapid push-to-talk
  re-press
  - **Impact**: Voice mode reliability
  - **Affected**: None
  - **Action Required**: None

**Changes**:
- ✅ **Default Opus 4.6 on Third-Party Providers**: Changed
  default Opus model on Bedrock, Vertex, and Microsoft Foundry
  to Opus 4.6 (was Opus 4.1)
  - **Impact**: Agents and subagents on these providers now
    default to Opus 4.6 instead of 4.1. Combined with the
    subagent model downgrade fix, model aliases now resolve
    correctly on all providers.
  - **Affected**: abstract model-optimization-guide (updated),
    abstract:escalation-governance (updated),
    conjure:agent-teams spawning-patterns module (updated)
  - **Action Required**: Done - all 3 files updated

- ✅ **`/output-style` Deprecated**: Deprecated in favor of
  `/config`. Output style is now fixed at session start for
  better prompt caching. Mid-session style changes no longer
  invalidate the prompt cache.
  - **Impact**: Sessions benefit from better prompt cache
    reuse. Workflows that changed output style mid-session
    should use `/config` before starting work instead.
  - **Affected**: conserve:context-optimization mecw-principles
    module (updated with prompt caching note)
  - **Action Required**: Done - mecw-principles module updated

**Platform Fixes** (no plugin impact):
- ✅ `/heapdump` EEXIST fix on Windows
- ✅ VS Code HTTP 400 fix for proxy/Bedrock/Vertex users
  with Claude 4.5 models

### Claude Code 2.1.69 (March 2026)

**New Features**:
- ✅ **`${CLAUDE_SKILL_DIR}` Variable**: Skills can reference their own
  directory using `${CLAUDE_SKILL_DIR}` in SKILL.md content, resolving
  to the absolute path of the containing directory
  - **Impact**: Enables portable path references for skills that ship
    alongside scripts, data files, or modules. No more hardcoded
    absolute paths.
  - **Affected**: abstract:skill-authoring (updated with CLAUDE_SKILL_DIR
    section and usage examples), leyline:supply-chain-advisory (adopted
    for `known-bad-versions.json` path reference)
  - **Action Required**: Done - skill-authoring and
    supply-chain-advisory updated

- ✅ **Skill Description Colon Fix**: Skill descriptions containing colons
  (e.g., `"Triggers include: X, Y, Z"`) no longer fail to load. Skills
  without a `description:` field now appear in the available skills list.
  - **Impact**: Removes a frontmatter parsing limitation. Skills with
    complex descriptions using colons work correctly.
  - **Affected**: abstract:skill-authoring (updated troubleshooting section)
  - **Action Required**: Done - skill-authoring SKILL.md updated

- ✅ **Hook Event Fields: agent_id and agent_type**: All hook events now
  include `agent_id` (for subagent sessions) and `agent_type` (for both
  subagent and `--agent` sessions)
  - **Impact**: Hooks can now distinguish which agent triggered them and
    implement agent-specific logic. Previously only SessionStart had
    `agent_type`.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated

- ✅ **Status Line worktree Field**: Status line hook commands gain a
  `worktree` field with `name`, `path`, `branch`, and `originalRepoDir`
  in worktree sessions
  - **Impact**: Status line hooks can now display worktree-aware context
  - **Affected**: abstract:hook-authoring hook-types module (updated in
    agent_id/agent_type section)
  - **Action Required**: Done - included in hook-types module update

- ✅ **TeammateIdle/TaskCompleted: continue: false**: These hooks now
  support returning `{"continue": false, "stopReason": "..."}` to stop
  a teammate, matching Stop hook behavior
  - **Impact**: Enables graceful teammate shutdown from hook logic
    (budget-based, idle timeout, post-task shutdown)
  - **Affected**: conjure:agent-teams health-monitoring module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated),
    abstract:hook-authoring hook-types module (updated)
  - **Action Required**: Done - all 5 files updated

- ✅ **WorktreeCreate/WorktreeRemove Plugin Hook Fix**: Plugin-registered
  WorktreeCreate and WorktreeRemove hooks were silently ignored before
  2.1.69; they now fire correctly
  - **Impact**: Plugins can now reliably use worktree lifecycle hooks.
    Previously only user/project-level hooks worked.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 files updated with plugin fix note

- ✅ **`/reload-plugins` Command**: Activates pending plugin changes
  without restarting Claude Code
  - **Impact**: Eliminates restart requirement for plugin development
    and updates
  - **Affected**: leyline:update-all-plugins command (updated Notes
    section)
  - **Action Required**: Done - update-all-plugins.md updated

- ✅ **`includeGitInstructions` Setting**: New setting and
  `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS` env var to remove built-in
  commit and PR workflow instructions
  - **Impact**: Organizations using custom commit/PR workflows (like our
    sanctum skills) can disable the built-in git instructions to reduce
    context and avoid conflicts
  - **Affected**: None - sanctum commit/PR skills already provide their
    own instructions
  - **Action Required**: None

- ✅ **Sonnet 4.5 → 4.6 Migration**: Pro/Max/Team Premium users
  automatically migrated from Sonnet 4.5 to Sonnet 4.6
  - **Impact**: Model upgrade is transparent. Agent `model` frontmatter
    referencing Sonnet resolves correctly. `--model claude-opus-4-0` and
    `--model claude-opus-4-1` now resolve to Opus 4.6 instead of
    deprecated versions.
  - **Affected**: abstract model-optimization-guide (updated),
    abstract:escalation-governance (updated)
  - **Action Required**: Done - both files updated with Sonnet 4.6
    migration note

- ✅ **Plugin Source Type `git-subdir`**: Plugins can now point to
  subdirectories within git repos
  - **Impact**: Enables monorepo-style plugin hosting
  - **Affected**: None - informational for plugin developers
  - **Action Required**: None

- ✅ **`pluginTrustMessage` Managed Setting**: Organizations can append
  custom context to plugin trust warnings
  - **Impact**: Enterprise governance improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **Effort Level Display**: Active effort level shown in logo and
  spinner (e.g., "with low effort")
  - **Impact**: UX visibility improvement
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **Nested Skill Discovery Security Fix**: Fixed nested skill discovery
  loading from gitignored directories like `node_modules`
  - **Impact**: Security fix preventing unintended skill loading from
    dependency directories
  - **Affected**: None - our skills are not in gitignored directories
  - **Action Required**: None

- ✅ **Deprecated Model Resolution Fix**: `--model claude-opus-4-0` and
  `--model claude-opus-4-1` now resolve to current Opus 4.6 instead of
  deprecated versions
  - **Impact**: Users with legacy model pins no longer get API errors
  - **Affected**: abstract model-optimization-guide (noted in Sonnet
    migration section)
  - **Action Required**: Done - included in model migration note

- ✅ **Hook Template Collision Fix**: Plugin hooks were silently
  dropped when two plugins used the same `${CLAUDE_PLUGIN_ROOT}/...`
  command template string. Now both fire correctly.
  - **Impact**: Two collisions exist in our ecosystem:
    (1) conserve + memory-palace both use
    `${CLAUDE_PLUGIN_ROOT}/hooks/setup.sh` for Setup events;
    (2) conserve + imbue both use
    `${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh` for
    SessionStart events. Before 2.1.69, one hook from each
    pair was silently dropped. Both now run.
  - **Affected**: conserve, memory-palace, imbue hooks
  - **Action Required**: None needed on 2.1.69+. Users on
    older versions may experience missing hook behavior.

- ✅ **`InstructionsLoaded` Hook Event**: New hook event that fires
  when CLAUDE.md or `.claude/rules/*.md` files load into context
  - **Impact**: Enables plugins to react to instruction loading
    (logging, validation, context-aware setup)
  - **Affected**: None - no current use case, documented for
    future adoption
  - **Action Required**: None

- ✅ **Plugin Stop/SessionEnd Hook Fix**: These hooks were not firing
  after `/plugin` operations (install, uninstall, update)
  - **Impact**: Lifecycle cleanup hooks now run reliably
  - **Affected**: memory-palace (Stop hook for session_lifecycle.py),
    egregore (Stop hook)
  - **Action Required**: None - hooks now fire correctly

- ✅ **`/clear` Session Cache Fix**: `/clear` now fully clears all
  session caches, reducing memory retention
  - **Impact**: conserve:clear-context workflow benefits; less stale
    state after `/clear` invocations
  - **Affected**: conserve clear-context skill
  - **Action Required**: None - automatic improvement

- ✅ **Concise Subagent Reports**: Multi-agent tasks produce more
  concise final reports, reducing token usage
  - **Impact**: All parallel agent dispatch workflows (do-issue,
    execute-plan, dispatching-parallel-agents) benefit from
    reduced token consumption on agent results
  - **Affected**: All agent-dispatching skills
  - **Action Required**: None - automatic improvement

### Claude Code 2.1.72 (March 2026)

**New Features**:
- ✅ **ExitWorktree Tool**: New built-in tool to leave an
  `EnterWorktree` session mid-conversation. Actions: `"keep"` (leave
  worktree on disk) or `"remove"` (delete worktree and branch).
  `discard_changes: true` required for remove with uncommitted work.
  - **Impact**: New tool name in PreToolUse/PostToolUse events. Hooks
    matching on tool names may need to handle worktree exit.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated

- ✅ **Effort Levels Simplified**: Reduced from 4 levels (`low`,
  `medium`, `high`, `max`) to 3 (`low`, `medium`, `high`). New
  symbols: ○ (low) ◐ (medium) ● (high). `/effort auto` resets to
  default. Brief notification replaces persistent icon.
  - **Impact**: Skills referencing `max` effort need updating.
    `model_hint: deep` skills that assumed `max` effort now map to
    `high`.
  - **Affected**: abstract:escalation-governance (updated),
    abstract model-optimization-guide (updated)
  - **Action Required**: Done - both files updated with 3-level system

- ✅ **Bash Auto-Approval Expansion**: Added `lsof`, `pgrep`, `tput`,
  `ss`, `fd`, `fdfind` to the default bash auto-approval allowlist
  - **Impact**: These read-only utilities no longer trigger permission
    prompts or PermissionRequest hook events
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 3 hook reference files updated

- ✅ **Agent Tool Model Parameter Restored**: Per-invocation model
  overrides via the `model` parameter on the Agent tool. Allows
  dispatching agents with specific model selections.
  - **Impact**: Agent dispatch can now explicitly set model per
    invocation, complementing agent definition `model` frontmatter
  - **Affected**: None - already supported in agent definitions
  - **Action Required**: None

- ✅ **CLAUDE_CODE_DISABLE_CRON Mid-Session Stop**: The env var now
  immediately stops scheduled cron jobs mid-session, not just prevents
  new ones at startup.
  - **Impact**: Provides an emergency stop for runaway cron tasks
  - **Affected**: abstract:hook-authoring hook-types module (updated)
  - **Action Required**: Done - hook-types module cron section updated

- ✅ **`/plan` Description Argument**: Optional description argument
  (e.g., `/plan fix the auth bug`) enters plan mode and immediately
  starts planning.
  - **Impact**: UX improvement for plan-based workflows
  - **Affected**: None
  - **Action Required**: None

- ✅ **`/copy` Write-to-File**: `w` key in `/copy` writes the focused
  selection directly to a file, bypassing the clipboard. Useful over
  SSH.
  - **Impact**: UX improvement
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **Skill Hook Double-Fire**: Fixed skill hooks firing twice per
  event when a hooks-enabled skill is invoked by the model
  - **Impact**: Hooks no longer produce duplicate events for skill
    invocations. Metrics and logging hooks may show reduced counts.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated

- ✅ **Hooks Fixes Bundle**: transcript_path correct for resumed/forked
  sessions, agent prompt no longer deleted from settings.json on every
  write, PostToolUse block reason no longer doubled, async hooks
  receive stdin with `bash read -r`
  - **Impact**: Multiple hook reliability improvements
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated

- ✅ **CLAUDE.md Comment Hiding**: HTML comments (`<!-- ... -->`) in
  CLAUDE.md files hidden from Claude when auto-injected. Visible via
  Read tool only.
  - **Impact**: Comments no longer consume context tokens. Human-only
    notes in CLAUDE.md stay invisible to the model.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated

- ✅ **`/clear` Foreground-Only**: `/clear` only clears foreground
  tasks now. Background agent and bash tasks continue running.
  - **Impact**: Background agents survive `/clear`. The auto-clear
    workflow no longer kills background work.
  - **Affected**: conserve:clear-context (updated with fix note)
  - **Action Required**: Done - clear-context SKILL.md updated

- ✅ **Team Agent Model Inheritance**: Team agents now inherit the
  leader's model instead of using their own default.
  - **Impact**: Consistent model behavior across agent teams
  - **Affected**: conjure:agent-teams health-monitoring module
    (updated)
  - **Action Required**: Done - health-monitoring module updated

- ✅ **Parallel Tool Call Cascade**: Failed Read/WebFetch/Glob no
  longer cancels sibling tool calls. Only Bash errors cascade.
  - **Impact**: Multi-file reads and parallel agent dispatch more
    reliable. A single file-not-found no longer aborts all siblings.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated

- ✅ **Prompt Cache Fix**: Fixed prompt cache invalidation in SDK
  `query()` calls, reducing input token costs up to 12x
  - **Impact**: Major cost reduction for Agent SDK and programmatic
    Claude Code invocations
  - **Affected**: conserve:context-optimization mecw-principles module
    (updated)
  - **Action Required**: Done - mecw-principles module updated

- ✅ **Worktree Isolation Fixes**: Task tool resume now restores CWD
  in worktree sessions. Background task notifications include
  `worktreePath` and `worktreeBranch` fields.
  - **Impact**: Worktree-based agent dispatch workflows more reliable
  - **Affected**: abstract:hook-authoring hook-types module (updated)
  - **Action Required**: Done - hook-types module ExitWorktree section

- ✅ **Permission Rule Matching Fixes**: Wildcard rules now match
  commands with heredocs/newlines/no args, sandbox.excludedCommands
  works with env var prefixes, deny rules apply to all command forms
  - **Impact**: Permission hooks and rules behave more predictably
  - **Affected**: abstract:hook-authoring hook-types module (updated)
  - **Action Required**: Done - hook-types module updated

- ✅ **Plugin Marketplace Fixes**: Git URLs without .git suffix
  supported (Azure DevOps, CodeCommit), improved clone failure
  diagnostics, Windows EEXIST fix, user-scope install fix,
  CLAUDE_CODE_PLUGIN_CACHE_DIR tilde expansion fix, plugin.json
  marketplace-only fields fix
  - **Impact**: Plugin installation and update reliability
  - **Affected**: leyline:update-all-plugins command (updated)
  - **Action Required**: Done - update-all-plugins.md updated

**Improvements**:
- ✅ **`--continue` Resume Fix**: Fixed not resuming from the most
  recent point after `--compact`
  - **Impact**: Session management reliability
  - **Affected**: None
  - **Action Required**: None

- ✅ **Tool Search ANTHROPIC_BASE_URL Fix**: Tool search activates
  even with ANTHROPIC_BASE_URL when ENABLE_TOOL_SEARCH is set
  - **Impact**: Proxy/gateway users can now use deferred tool loading
  - **Affected**: None
  - **Action Required**: None

- ✅ **Improved Bash Parsing**: Switched to native module for faster
  initialization, no memory leak
  - **Impact**: Performance and stability improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **Bundle Size Reduction**: ~510 KB smaller
  - **Impact**: Faster install and startup
  - **Affected**: None
  - **Action Required**: None

**Platform Fixes** (no plugin impact):
- ✅ Stdin freeze in long sessions fix
- ✅ Voice mode: input lag, false "No speech detected", stale transcripts
- ✅ Slow exits with background tasks/hooks
- ✅ Agent task progress stuck on "Initializing..."
- ✅ /config UX: Escape cancels, Enter saves, Space toggles
- ✅ Up-arrow history for concurrent sessions
- ✅ Voice transcription accuracy for dev terms
- ✅ Feedback survey frequency in long sessions
- ✅ --effort CLI flag reset on startup
- ✅ Ctrl+B backgrounded queries losing transcript
- ✅ /model display while Claude is working
- ✅ Digit keys in plan mode permission prompt
- ✅ Sandbox permission edge cases
- ✅ CPU utilization in long sessions
- ✅ Escape key after cancelling
- ✅ Double Ctrl+C with background tasks
- ✅ "Always Allow" saving non-matching rules
- ✅ Desktop/SDK crash with U+2028/U+2029 characters
- ✅ Terminal title cleared despite DISABLE_TERMINAL_TITLE
- ✅ Oversized images from Bash data-URL output
- ✅ Bedrock API error session resume crash
- ✅ Intermittent validation errors on tool inputs
- ✅ Multi-line session titles from fork
- ✅ Queued message image handling
- ✅ VS Code scroll speed, Shift+Enter, effort indicator, URI handler

### Claude Code 2.1.71 (March 2026)

**New Features**:
- ✅ **`/loop` Command and Cron Scheduling**: `/loop` runs prompts or
  slash commands on recurring intervals (e.g., `/loop 5m check the
  deploy`). Three new built-in tools: `CronCreate`, `CronList`,
  `CronDelete` for scheduled tasks. `CronCreate` accepts `cron`
  (5-field expression in local timezone), `prompt`, `recurring`
  (default true), and `durable` (default false; true persists to
  `.claude/scheduled_tasks.json` across restarts). Sessions hold up
  to 50 tasks with 7-day auto-expiry for recurring tasks. Tasks fire
  only while the REPL is idle, with deterministic jitter (recurring:
  up to 10% of period late, max 15 min; one-shot at :00/:30: up to
  90s early). Disable with `CLAUDE_CODE_DISABLE_CRON=1`.
  - **Impact**: New scheduling capability. Hooks matching on tool names
    in PreToolUse/PostToolUse see these new tool names. The `/loop`
    command has no naming conflict with existing skills. The `durable`
    parameter enables persistent scheduling across session restarts.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated),
    egregore:orchestrator agent (updated with `durable: true` and
    corrected `cron` parameter name)
  - **Action Required**: Done - all 4 hook reference files updated with
    full cron tools schema; egregore agent updated with durable
    heartbeat and corrected parameter names

- ✅ **Bash Auto-Approval Expansion**: Added `fmt`, `comm`, `cmp`,
  `numfmt`, `expr`, `test`, `printf`, `getconf`, `seq`, `tsort`, `pr`
  to the default bash auto-approval allowlist
  - **Impact**: These POSIX utilities no longer trigger permission prompts
    or PermissionRequest hook events
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 3 hook reference files updated

- ✅ **Voice Push-to-Talk Keybinding**: `voice:pushToTalk` keybinding
  rebindable in `keybindings.json` (default: space); modifier+letter
  combos like `meta+k` have zero typing interference. Voice STT expanded
  to 20 languages.
  - **Impact**: UX improvement for voice users
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **Stdin Freeze Fix**: Fixed stdin freeze in long-running sessions
  where keystrokes stop being processed but the process stays alive
  - **Impact**: Critical reliability fix for long sessions
  - **Affected**: None
  - **Action Required**: None

- ✅ **CoreAudio Startup Freeze**: Fixed 5-8 second startup freeze for
  users with voice mode enabled, caused by CoreAudio initialization
  blocking the main thread after system wake
  - **Impact**: Startup performance fix for macOS voice users
  - **Affected**: None
  - **Action Required**: None

- ✅ **OAuth Startup UI Freeze**: Fixed startup UI freeze when many
  claude.ai proxy connectors refresh an expired OAuth token
  simultaneously
  - **Impact**: Startup reliability for enterprise users with multiple
    connectors
  - **Affected**: None
  - **Action Required**: None

- ✅ **Fork Plan File Isolation**: Fixed `/fork` sharing the same plan
  file, which caused plan edits in one fork to overwrite the other
  - **Impact**: Forked conversations now have independent plan state
  - **Affected**: None
  - **Action Required**: None

- ✅ **Read Tool Image Overflow Fix**: Fixed the Read tool putting
  oversized images into context when image processing failed, breaking
  subsequent turns in long image-heavy sessions
  - **Impact**: Context protection for image-heavy workflows. Prevents
    MECW violations from failed image processing.
  - **Affected**: conserve:context-optimization mecw-principles module
    (updated)
  - **Action Required**: Done - mecw-principles module updated with Read
    Tool Image Safety section

- ✅ **Heredoc Permission Fix**: Fixed false-positive permission prompts
  for compound bash commands containing heredoc commit messages
  - **Impact**: The `git commit -m "$(cat <<'EOF' ... EOF)"` pattern used
    by sanctum commit workflows no longer triggers unexpected permission
    prompts
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated

- ✅ **Plugin Installation Persistence Fix**: Fixed plugin installations
  being lost when running multiple Claude Code instances
  - **Impact**: Multi-instance reliability fix
  - **Affected**: None
  - **Action Required**: None

- ✅ **claude.ai Connector Reconnection**: Fixed connectors failing to
  reconnect after OAuth token refresh
  - **Impact**: Session stability for claude.ai connector users
  - **Affected**: None
  - **Action Required**: None

- ✅ **MCP Connector Notification Spam**: Fixed startup notifications
  appearing for every org-configured connector instead of only previously
  connected ones
  - **Impact**: Reduced startup noise for enterprise users
  - **Affected**: None
  - **Action Required**: None

- ✅ **Background Agent Notification Fix**: Fixed completion
  notifications missing the output file path, making it difficult for
  parent agents to recover agent results after context compaction
  - **Impact**: Critical fix for agent team workflows. Parent agents can
    now reliably retrieve background agent output after compaction.
  - **Affected**: conjure:agent-teams health-monitoring module (updated)
  - **Action Required**: Done - health-monitoring module updated

- ✅ **Duplicate Bash Error Output**: Fixed duplicate output in Bash tool
  error messages when commands exit with non-zero status
  - **Impact**: Cleaner error output, less context waste on error messages
  - **Affected**: None
  - **Action Required**: None

- ✅ **Chrome Extension Detection**: Fixed auto-detection getting
  permanently stuck on "not installed" after running on a machine without
  local Chrome
  - **Impact**: UX fix for VS Code users
  - **Affected**: None
  - **Action Required**: None

- ✅ **Plugin Marketplace Update Fix**: Fixed `/plugin marketplace update`
  failing with merge conflicts when the marketplace is pinned to a
  branch/tag ref
  - **Impact**: Plugin update reliability improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **Plugin Marketplace Add @ref Parsing**: Fixed
  `/plugin marketplace add owner/repo@ref` incorrectly parsing `@`;
  previously only `#` worked as a ref separator
  - **Impact**: Users can now use the standard `@ref` syntax
  - **Affected**: None
  - **Action Required**: None

- ✅ **Permissions Duplicate Entries**: Fixed duplicate entries in
  `/permissions` Workspace tab when the same directory is added with
  and without a trailing slash
  - **Impact**: UX cleanup
  - **Affected**: None
  - **Action Required**: None

- ✅ **`--print` Team Agent Hang**: Fixed `--print` hanging forever when
  team agents are configured; the exit loop no longer waits on
  long-lived `in_process_teammate` tasks
  - **Impact**: Critical fix for CI/automation workflows using `--print`
    with team configurations
  - **Affected**: conjure:agent-teams health-monitoring module (updated)
  - **Action Required**: Done - health-monitoring module updated

- ✅ **ToolSearch Display Fix**: Fixed "❯ Tool loaded." appearing in the
  REPL after every ToolSearch call
  - **Impact**: Cosmetic fix reducing REPL noise
  - **Affected**: None
  - **Action Required**: None

- ✅ **Windows Path Prompting**: Fixed prompting for
  `cd <cwd> && git ...` on Windows when the model uses a mingw-style
  path
  - **Impact**: Windows UX fix
  - **Affected**: None
  - **Action Required**: None

**Improvements**:
- ✅ **Startup Image Processor Deferral**: Deferred native image processor
  loading to first use
  - **Impact**: Faster startup for sessions that don't use images
  - **Affected**: None
  - **Action Required**: None

- ✅ **Bridge Reconnection Speed**: Bridge session reconnection completes
  within seconds after laptop wake from sleep, instead of waiting up to
  10 minutes
  - **Impact**: Major usability improvement for laptop users
  - **Affected**: None
  - **Action Required**: None

- ✅ **`/plugin uninstall` Team Safety**: Now disables project-scoped
  plugins in `.claude/settings.local.json` instead of modifying
  `.claude/settings.json`, so changes don't affect teammates via version
  control
  - **Impact**: Team-safe plugin management
  - **Affected**: leyline:update-all-plugins command (updated Notes
    section)
  - **Action Required**: Done - update-all-plugins.md updated

- ✅ **Plugin MCP Server Deduplication**: Plugin-provided MCP servers
  duplicating manually-configured servers (same command/URL) are now
  skipped, preventing duplicate connections and tool sets. Suppressions
  shown in `/plugin` menu.
  - **Impact**: Prevents duplicate MCP connections
  - **Affected**: None
  - **Action Required**: None

**Changes**:
- ✅ **`/debug` Toggle**: Updated to toggle debug logging on mid-session,
  since debug logs are no longer written by default
  - **Impact**: Debugging workflow change
  - **Affected**: None
  - **Action Required**: None

- ✅ **Removed Connector Notification Noise**: Removed startup
  notification noise for unauthenticated org-registered claude.ai
  connectors
  - **Impact**: Cleaner startup for enterprise users
  - **Affected**: None
  - **Action Required**: None

### Claude Code 2.1.70 (March 2026)

**New Features**:
- ✅ **Compaction Image Preservation**: Compaction now preserves images
  in the summarizer request, allowing prompt cache reuse across
  compaction boundaries
  - **Impact**: Compaction is faster and cheaper for image-heavy sessions
    (screenshots, diagrams). Previously images were dropped during
    compaction, busting the prompt cache.
  - **Affected**: conserve:context-optimization mecw-principles module
    (updated)
  - **Action Required**: Done - mecw-principles module updated

- ✅ **Resume Token Savings**: Skill listings are no longer re-injected
  on every `--resume` invocation, saving ~600 tokens per resume
  - **Impact**: Improved context efficiency for workflows that frequently
    resume sessions
  - **Affected**: conserve:context-optimization mecw-principles module
    (updated)
  - **Action Required**: Done - mecw-principles module updated

**Bug Fixes**:
- ✅ **ToolSearch Proxy Fix**: Fixed API 400 errors when using
  ANTHROPIC_BASE_URL with a third-party gateway. Tool search now
  correctly detects proxy endpoints and disables tool_reference blocks.
  - **Impact**: Proxy/gateway users no longer hit 400 errors from
    tool_reference blocks that proxy endpoints don't support
  - **Affected**: None - no proxy-specific guidance in our skills
  - **Action Required**: None

- ✅ **ToolSearch Empty Response Fix**: Fixed empty model responses
  immediately after ToolSearch. The server rendered tool schemas with
  system-prompt-style tags at the prompt tail, confusing models into
  stopping early.
  - **Impact**: Significant reliability fix for any workflow triggering
    deferred tool loading via ToolSearch. All agent dispatches and MCP
    tool discovery benefit automatically.
  - **Affected**: conserve:mcp-code-execution (updated with fix note)
  - **Action Required**: Done - mcp-code-execution SKILL.md updated

- ✅ **MCP Prompt Cache Bust Fix**: Fixed prompt-cache bust when an MCP
  server with instructions connects after the first turn
  - **Impact**: MCP-heavy sessions maintain prompt cache reuse even when
    servers connect late. Reduces token costs for workflows that trigger
    MCP connections mid-session.
  - **Affected**: conserve:mcp-code-execution (updated with fix note)
  - **Action Required**: Done - mcp-code-execution SKILL.md updated

- ✅ **Effort Parameter Fix**: Fixed API 400 error
  `This model does not support the effort parameter` when using custom
  Bedrock inference profiles or non-standard Claude model identifiers
  - **Impact**: Effort controls now work reliably across all deployment
    configurations
  - **Affected**: abstract:escalation-governance (updated with fix note)
  - **Action Required**: Done - escalation-governance SKILL.md updated

- ✅ **Plugin Installation Status Accuracy**: Plugin installation status
  is now accurate in `/plugin` menu. Previous versions could show plugins
  as inaccurately installed or report "not found in marketplace" on fresh
  startup.
  - **Impact**: Reliable plugin status reporting in the CLI
  - **Affected**: leyline:update-all-plugins command (updated Notes
    section)
  - **Action Required**: Done - update-all-plugins.md updated

- ✅ **AskUserQuestion Performance Fix**: Fixed a performance regression
  in the AskUserQuestion preview dialog that re-ran markdown rendering
  on every keystroke in the notes input
  - **Impact**: Skills using AskUserQuestion (minister:close-issue,
    minister:create-issue, interactive commands) are snappier
  - **Affected**: None - automatic performance improvement
  - **Action Required**: None

- ✅ **permissions.defaultMode Remote Fix**: Fixed defaultMode settings
  values other than acceptEdits or plan being applied in Claude Code
  Remote environments (now ignored)
  - **Impact**: Remote environment permission behavior is now consistent
  - **Affected**: None - no remote-specific permission guidance
  - **Action Required**: None

- ✅ **Feature Flags Disk Cache Fix**: Fixed feature flags read during
  early startup never refreshing their disk cache, causing stale values
  to persist across sessions
  - **Impact**: Plugin feature flag state is now fresh on each session
  - **Affected**: None - automatic fix
  - **Action Required**: None

- ✅ **/security-review merge-base Fix**: Fixed /security-review command
  failing with `unknown option merge-base` on older git versions
  - **Impact**: /security-review now works on older git installations
  - **Affected**: None - we reference /security-review in examples only
  - **Action Required**: None

**Improvements**:
- ✅ **74% Prompt Re-render Reduction**: Reduced prompt input re-renders
  during turns by ~74%
  - **Impact**: Passive performance improvement for all workflows.
    Reduces CPU overhead during long agent turns.
  - **Affected**: None - automatic improvement
  - **Action Required**: None

- ✅ **Remote Control Poll Rate**: Reduced /poll rate to once per 10
  minutes while connected (was 1-2s), cutting server load ~300x
  - **Impact**: Infrastructure efficiency for remote control users
  - **Affected**: None
  - **Action Required**: None

**Platform Fixes** (no plugin impact):
- ✅ SSH enter key fix for slow connections
- ✅ Windows/WSL clipboard non-ASCII corruption fix
- ✅ Extra VS Code windows on Windows startup fix
- ✅ Windows voice mode native binary fix
- ✅ Push-to-talk activation on session start fix
- ✅ Markdown #NNN link resolution fix
- ✅ Repeated "Model updated to Opus 4.6" notification fix
- ✅ /color reset command (new: /color default, gray, reset, none)
- ✅ /rename works while Claude is processing
- ✅ VS Code teleport marker rendering fix
- ✅ Startup memory reduced ~426KB
- ✅ Microphone silence error message improved

**VS Code Features** (no plugin impact):
- ✅ Spark icon in activity bar listing all sessions
- ✅ Full markdown plan view with comment support
- ✅ Native MCP server management dialog via /mcp

### Claude Code 2.1.68 (March 2026)

**Changes**:
- ✅ **Opus 4.6 Default Medium Effort**: Opus 4.6 now defaults to medium
  effort for Max and Team subscribers. Medium effort is the sweet spot
  between speed and thoroughness.
  - **Impact**: Changes the default reasoning depth for Opus 4.6. Agents
    and skills using Opus 4.6 will produce faster but potentially less
    thorough responses by default. Use `/model` to adjust or "ultrathink"
    keyword for high effort on the next turn.
  - **Affected**: abstract:escalation-governance (updated effort control
    table and default), abstract model-optimization-guide (updated effort
    documentation)
  - **Action Required**: Done - escalation-governance and
    model-optimization-guide updated with medium default and ultrathink
    keyword

- ✅ **"ultrathink" Keyword Re-introduced**: Typing "ultrathink" in a
  prompt enables high effort for the next turn
  - **Impact**: Quick way to request deeper reasoning without navigating
    `/model` menu
  - **Affected**: abstract:escalation-governance (updated with ultrathink
    reference)
  - **Action Required**: Done - escalation-governance updated

- ✅ **Opus 4 and 4.1 Removed**: Removed from Claude Code on the
  first-party API. Users with these models pinned are automatically
  moved to Opus 4.6.
  - **Impact**: No more Opus 4/4.1 model selection. Automatic migration
    to Opus 4.6 is transparent. Agent `model` frontmatter referencing
    Opus 4/4.1 will resolve to Opus 4.6.
  - **Affected**: abstract:escalation-governance (updated with removal
    note), abstract model-optimization-guide (updated)
  - **Action Required**: Done - both files updated with deprecation notes

### Claude Code 2.1.63 (March 2026)

**New Features**:
- ✅ **`/simplify` and `/batch` Bundled Slash Commands**: New built-in
  slash commands for code simplification and batch operations
  - **Impact**: New built-in commands
  - **Affected**: None - no naming conflicts with existing skills or
    commands
  - **Action Required**: None

- ✅ **HTTP Hooks**: Hooks can now POST JSON to a URL and receive JSON
  responses, as an alternative to shell commands
  - **Impact**: New hook execution model for enterprise/sandboxed
    environments. Complements existing shell-based hooks.
  - **Affected**: abstract:hook-authoring (updated with HTTP hook
    documentation), hookify plugin (new hook type to consider)
  - **Action Required**: Done - hook-authoring SKILL.md updated with
    HTTP hooks section

- ✅ **Project Configs and Auto-Memory Shared Across Worktrees**:
  `.claude/` configs and auto-memory are now shared across git worktrees
  of the same repository
  - **Impact**: Agents with `isolation: worktree` now inherit the parent
    repo's project configs and memory instead of starting with a blank
    slate
  - **Affected**: superpowers:using-git-worktrees,
    conserve:subagent-coordination (updated), conjure:agent-teams
  - **Action Required**: Done - subagent-coordination module updated

- ✅ **`ENABLE_CLAUDEAI_MCP_SERVERS=false` Env Var**: Opt out of
  claude.ai MCP servers being available in Claude Code
  - **Impact**: Opt-out for the claude.ai MCP connector feature
    introduced in 2.1.46
  - **Affected**: conserve:mcp-code-execution mcp-subagents module
    (updated)
  - **Action Required**: Done - mcp-subagents module updated with opt-out
    documentation

- ✅ **`/copy` "Always Copy Full Response" Option**: Skips code block
  picker for future `/copy` invocations
  - **Impact**: UX convenience improvement
  - **Affected**: None
  - **Action Required**: None

- ✅ **Improved `/model` Display**: Shows currently active model in slash
  command menu
  - **Impact**: UX improvement
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **`/clear` Skill Cache Reset**: Fixed `/clear` not resetting cached
  skills, causing stale skill content to persist in new conversations
  - **Impact**: `/clear` + `/catchup` pattern is now fully reliable;
    skills refresh properly after clear
  - **Affected**: conserve:clear-context (updated with fix note),
    sanctum:session-management
  - **Action Required**: Done - clear-context SKILL.md updated

- ✅ **Memory Leak Fixes (12+ sites)**: Fixed leaks in bridge polling,
  MCP OAuth cleanup, hooks config menu, permission handler
  auto-approvals, bash prefix cache, MCP tool/resource cache on
  reconnect, IDE host IP cache, WebSocket transport reconnect, git root
  detection cache, JSON parsing cache, long-running teammate messages in
  AppState, and MCP server fetch caches on disconnect
  - **Impact**: Massive quality pass on memory leaks. Long-running
    sessions and heavy agent workflows are significantly more stable.
  - **Affected**: conserve:context-optimization subagent-coordination
    (updated), conjure:agent-teams health-monitoring (updated)
  - **Action Required**: Done - subagent-coordination and
    health-monitoring modules updated with memory fix notes

- ✅ **Subagent Context Compaction**: Heavy progress message payloads
  stripped during compaction in subagent sessions
  - **Impact**: Subagent compaction is leaner; less noise retained after
    compaction
  - **Affected**: conserve:context-optimization subagent-coordination
    (updated in memory leak fixes entry above)
  - **Action Required**: Done - included in 2.1.63 memory leak fixes
    section

- ✅ **Local Slash Command Output Fix**: `/cost` and similar local
  commands now appear as system messages instead of user-sent messages
  - **Impact**: UI correctness for built-in commands
  - **Affected**: None
  - **Action Required**: None

- ✅ **REPL Bridge Race Condition**: Fixed message ordering issues during
  initial connection flush
  - **Impact**: Reliability fix for bridge-based integrations
  - **Affected**: None
  - **Action Required**: None

- ✅ **File Count Cache Glob Fix**: File count cache now respects glob
  ignore patterns
  - **Impact**: More accurate file counting in repos with ignore patterns
  - **Affected**: None
  - **Action Required**: None

- ✅ **MCP OAuth Manual URL Fallback**: Added paste fallback when
  localhost redirect fails during MCP OAuth
  - **Impact**: Improved MCP authentication reliability
  - **Affected**: None
  - **Action Required**: None

- ✅ **Config File Corruption (Follow-up)**: Fixed config corruption when
  multiple instances run simultaneously (related to 2.1.59 fix)
  - **Impact**: Multi-instance reliability
  - **Affected**: None
  - **Action Required**: None


> **Earlier**: See [March 2026 Early](compatibility-features-march2026-early.md) for versions 2.1.50-2.1.62.
