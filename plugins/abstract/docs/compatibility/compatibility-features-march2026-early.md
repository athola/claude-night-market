# Claude Code Compatibility Features: March 2026 (Early)

Feature timeline for Claude Code versions 2.1.50 through 2.1.62,
released in March 2026.

> **See Also**:
> [Features Index](compatibility-features.md) |
> [March 2026 Recent](compatibility-features-march2026-recent.md) |
> [February 2026 Early](compatibility-features-feb2026-early.md) |
> [February 2026 Late](compatibility-features-feb2026-late.md) |
> [January 2026](compatibility-features-jan2026.md) |
> [Plugin Compatibility](compatibility-features-plugin-compat.md) |
> [Reference](compatibility-reference.md) |
> [2025 Archive](compatibility-features-2025.md)

## Feature Timeline

### Claude Code 2.1.62 (March 2026)

**Bug Fixes**:
- ✅ **Prompt Cache Regression Fix**: Fixed regression that reduced prompt
  suggestion cache hit rates
  - **Impact**: Internal API-level optimization; improved cache hit rates
    reduce latency and cost transparently
  - **Affected**: None - infrastructure-level fix, no plugin surface area
  - **Action Required**: None

### Claude Code 2.1.61 (March 2026)

**Bug Fixes**:
- ✅ **Config File Concurrent Write Fix (Windows)**: Fixed concurrent
  writes corrupting config file on Windows
  - **Impact**: Windows-specific follow-up to 2.1.59 config corruption
    fix; adds proper file locking for concurrent writes
  - **Affected**: None - Windows-specific, no multi-instance
    orchestration in this codebase
  - **Action Required**: None

### Claude Code 2.1.59 (March 2026)

**New Features**:
- ✅ **Auto-Memory with /memory Command**: Claude automatically saves
  useful context to persistent auto-memory. Managed via `/memory`
  command.
  - **Impact**: Built-in memory persistence for conversation context.
    This is the system backing
    `~/.claude/projects/*/memory/MEMORY.md`
  - **Affected**: memory-palace README (updated layer comparison table
    from "Native Memory 2.1.32+" to "Auto-Memory 2.1.59+")
  - **Action Required**: Done - memory-palace README updated to reference
    auto-memory and `/memory` command

- ✅ **/copy Command**: Interactive code block picker for copying
  individual blocks or full responses
  - **Impact**: New built-in slash command
  - **Affected**: None - no naming conflict with existing skills
  - **Action Required**: None

- ✅ **Smarter Bash "Always Allow" Prefixes**: Compound bash commands
  (e.g., `cd /tmp && git fetch && git push`) now compute
  per-subcommand prefixes instead of treating the whole command as one
  - **Impact**: More granular permission approval UX for chained commands
  - **Affected**: None - passive UX improvement
  - **Action Required**: None

**Bug Fixes**:
- ✅ **Multi-Agent Memory Release**: Releasing completed subagent task
  state improves memory in multi-agent sessions
  - **Impact**: Continuation of 2.1.50 memory leak fixes; further
    reduces RSS growth in Task-heavy workflows
  - **Affected**: conserve:context-optimization subagent-coordination
    module (updated)
  - **Action Required**: Done - subagent-coordination module updated
    with 2.1.59 task state release note

- ✅ **MCP OAuth Token Refresh Race**: Fixed race condition when running
  multiple Claude Code instances simultaneously
  - **Impact**: Multi-instance MCP reliability
  - **Affected**: None
  - **Action Required**: None

- ✅ **Config File Corruption Fix**: Fixed config corruption that could
  wipe authentication when multiple instances ran simultaneously
  - **Impact**: Critical reliability fix for users running parallel
    Claude Code sessions
  - **Affected**: None - no multi-instance orchestration in this
    codebase
  - **Action Required**: None

- ✅ **Shell Error on Deleted Working Directory**: Clear error message
  when cwd has been deleted
  - **Impact**: UX improvement
  - **Affected**: None
  - **Action Required**: None

### Claude Code 2.1.58 (March 2026)

**Features**:
- ✅ **Remote Control Wider Rollout**: Expanded `claude remote-control`
  availability to more users
  - **Impact**: Feature flag expansion, no API or behavioral changes
    (see 2.1.51 for feature details)
  - **Affected**: None
  - **Action Required**: None

### Claude Code 2.1.56 (March 2026)

**Bug Fixes**:
- ✅ **VS Code Extension Crash (Follow-up)**: Fixed another cause of
  "command 'claude-vscode.editor.openLast' not found" crashes
  - **Impact**: VS Code extension stability on Windows (follow-up to
    2.1.52 fix)
  - **Affected**: None - IDE extension fix, not relevant to CLI plugin
    ecosystem
  - **Action Required**: None

### Claude Code 2.1.55 (March 2026)

**Bug Fixes**:
- ✅ **BashTool EINVAL on Windows**: Fixed BashTool failing with EINVAL
  error on Windows
  - **Impact**: Windows-specific Bash tool reliability fix
  - **Affected**: None - no Windows-specific workarounds in this codebase
  - **Action Required**: None

### Claude Code 2.1.53 (March 2026)

**Bug Fixes**:
- ✅ **UI Flicker on Input Submission**: Fixed user input briefly
  disappearing after submission before the message rendered
  - **Impact**: Pure UI rendering fix
  - **Affected**: None
  - **Action Required**: None

- ✅ **Bulk Agent Kill (ctrl+f) Aggregate Notification**: ctrl+f now
  sends a single aggregate notification instead of one per agent, and
  properly clears the command queue
  - **Impact**: Cleaner shutdown of parallel agent sessions; no more
    notification storms when killing N background agents
  - **Affected**: conjure:agent-teams spawning-patterns (updated with
    bulk kill section)
  - **Action Required**: Done - spawning-patterns module updated with
    ctrl+f bulk kill behavior

- ✅ **Remote Control Stale Sessions on Shutdown**: Parallelized teardown
  network calls to prevent graceful shutdown from leaving stale sessions
  - **Impact**: `claude remote-control` sessions now clean up reliably
    on shutdown
  - **Affected**: sanctum:session-management (session cleanup
    reliability)
  - **Action Required**: None - passive fix for remote control users

- ✅ **`--worktree` Ignored on First Launch**: Fixed `--worktree` flag
  sometimes being silently ignored on first launch
  - **Impact**: Worktree isolation now activates reliably on initial
    invocation
  - **Affected**: superpowers:using-git-worktrees, agents with
    `isolation: worktree` frontmatter
  - **Action Required**: None - passive fix. Worktree isolation was
    intermittently not activating.

- ✅ **Windows Stability (4 fixes)**: Fixed panic on corrupted value,
  crash spawning many processes, WebAssembly interpreter crash (Linux
  x64 and Windows x64), and ARM64 crash after 2 minutes
  - **Impact**: Platform stability improvements for Windows and Linux
    x64 WebAssembly users
  - **Affected**: None - no platform-specific workarounds in this
    codebase
  - **Action Required**: None

### Claude Code 2.1.52 (March 2026)

**Bug Fixes**:
- ✅ **VS Code Extension Crash on Windows**: Fixed extension crash with
  error "command 'claude-vscode.editor.openLast' not found"
  - **Impact**: VS Code extension stability on Windows
  - **Affected**: None - IDE extension fix, not relevant to CLI plugin
    ecosystem
  - **Action Required**: None

### Claude Code 2.1.51 (March 2026)

**New Features**:
- ✅ **`claude remote-control` Subcommand**: New subcommand for external
  builds, enabling local environment serving for all users
  - **Impact**: Enables external IDEs and tools to connect to a local
    Claude Code session
  - **Affected**: None - new capability, no existing plugins reference
    this
  - **Action Required**: None - additive feature

- ✅ **Plugin Marketplace Git Timeout Increase**: Default git timeout
  increased from 30s to 120s; configurable via
  `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS`
  - **Impact**: Plugin installations from slow networks or large repos
    are less likely to time out
  - **Affected**: leyline:reinstall-all-plugins, leyline:update-all-plugins
    (both updated with troubleshooting notes)
  - **Action Required**: Done - leyline commands updated with
    `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` documentation

- ✅ **Custom npm Registries and Version Pinning**: Plugins installed from
  npm sources now support custom registries and specific version pins
  - **Impact**: Enterprise environments with private npm registries can
    now host and install plugins
  - **Affected**: leyline:reinstall-all-plugins (updated with npm
    registry notes)
  - **Action Required**: Done - reinstall command updated with npm
    registry section

- ✅ **BashTool Skips Login Shell by Default**: BashTool no longer uses
  `-l` flag when a shell snapshot is available, improving command
  execution performance
  - **Impact**: Faster command execution; previously required setting
    `CLAUDE_BASH_NO_LOGIN=true`
  - **Affected**: All agents using Bash tool, hook-types-comprehensive
    (updated with login shell guidance for hook developers)
  - **Action Required**: Done - hook development docs updated with login
    shell behavior note

- ✅ **Managed Settings via macOS plist / Windows Registry**: Settings
  can now be configured through OS-native management tools
  - **Impact**: Enterprise IT can deploy Claude Code settings via MDM
    (macOS) or Group Policy (Windows). Precedence: server-managed >
    MDM/plist/HKLM > managed-settings.json file > CLI args > project >
    user settings. Only one managed source is used (no merging across
    managed tiers). Array settings (permissions, sandbox paths) merge
    across non-managed scopes.
  - **Managed-Only Settings**: `allowManagedPermissionRulesOnly`,
    `allowManagedHooksOnly`, `allowManagedMcpServersOnly`,
    `strictKnownMarketplaces`, `blockedMarketplaces`,
    `disableBypassPermissionsMode`, `allowedHttpHookUrls`,
    `httpHookAllowedEnvVars`, `pluginTrustMessage`
  - **macOS**: `com.anthropic.claudecode` plist domain via MDM (Jamf,
    Kandji)
  - **Windows**: `HKLM\SOFTWARE\Policies\ClaudeCode` (admin) or
    `HKCU\SOFTWARE\Policies\ClaudeCode` (user, lowest policy priority)
  - **File paths**: macOS `/Library/Application Support/ClaudeCode/`,
    Linux `/etc/claude-code/`, Windows `C:\Program Files\ClaudeCode\`
  - **Affected**: docs/api-overview.md (updated with managed settings
    section)
  - **Action Required**: Done - API overview updated with enterprise
    configuration reference

- ✅ **New Account Environment Variables**: `CLAUDE_CODE_ACCOUNT_UUID`,
  `CLAUDE_CODE_USER_EMAIL`, and `CLAUDE_CODE_ORGANIZATION_UUID` for SDK
  callers
  - **Impact**: Eliminates race condition where early telemetry events
    lacked account metadata
  - **Affected**: conjure delegation-core troubleshooting (updated with
    SDK env var guidance)
  - **Action Required**: None - relevant for external SDK integrations
    only

- ✅ **Human-Readable `/model` Picker Labels**: Shows "Sonnet 4.5"
  instead of raw model IDs, with upgrade hints for newer versions
  - **Impact**: Better UX when switching models; stale model IDs in
    agent frontmatter still resolve correctly
  - **Affected**: scribe agents (updated from `claude-sonnet-4-20250514`
    to `claude-sonnet-4-6`)
  - **Action Required**: Done - scribe agent model IDs updated

**Bug Fixes**:
- ✅ **statusLine/fileSuggestion Security Fix**: Hook commands now require
  workspace trust acceptance in interactive mode
  - **Impact**: Prevents untrusted hooks from executing status line or
    file suggestion commands
  - **Affected**: hook-authoring hook-types, sdk-hook-types,
    capabilities-hooks reference, hook-types-comprehensive (all updated
    with workspace trust security notes)
  - **Action Required**: Done - four hook reference files updated with
    workspace trust security section

- ✅ **Tool Result Persistence Threshold Lowered**: Results larger than
  50K chars now persisted to disk (previously 100K)
  - **Impact**: Reduces context window usage; improves conversation
    longevity for subagent-heavy workflows
  - **Affected**: conjure bridge hook (already uses 50K threshold -
    aligned), conserve:context-optimization (mecw-principles and
    subagent-coordination updated)
  - **Action Required**: Done - conserve MECW principles and subagent
    coordination modules updated with 50K threshold documentation

- ✅ **Duplicate `control_response` Fix**: WebSocket reconnects no longer
  cause API 400 errors from duplicate assistant messages
  - **Impact**: Improved reliability for long-running sessions with
    network interruptions
  - **Affected**: None - no WebSocket or SDK caller code in codebase
  - **Action Required**: None

- ✅ **Slash Command Autocomplete Fix**: No longer crashes when a skill
  description is a YAML array or non-string type
  - **Impact**: Plugin marketplace stability improvement
  - **Affected**: None - all 121 SKILL.md files in this codebase use
    string descriptions (verified)
  - **Action Required**: None

### Claude Code 2.1.50 (March 2026)

**New Features**:
- ✅ **WorktreeCreate/WorktreeRemove Hook Events**: New hook events that
  fire when agent worktree isolation creates or removes worktrees
  - **Impact**: Custom VCS setup and teardown (symlink creation, cache
    pre-population) can now run as lifecycle hooks for isolated agents
  - **Affected**: sanctum session-management (potential worktree setup
    hooks), superpowers:using-git-worktrees (documentation update),
    conjure agent-teams (agents with `isolation: worktree` can now have
    setup/teardown)
  - **Action Required**: None — additive. Evaluate whether existing
    worktree setup scripts should migrate to hook events

- ✅ **`claude agents` CLI Command**: New subcommand listing all
  configured agents in the workspace
  - **Impact**: Debugging agent configurations and verifying plugin agent
    registrations no longer requires manual directory inspection
  - **Affected**: All plugins registering agents — useful for verifying
    agent discovery during development
  - **Action Required**: None — informational tool

- ✅ **LSP `startupTimeout` Configuration**: New `startupTimeout` field
  in LSP server configuration controls how long Claude Code waits for
  an LSP server to initialize before falling back
  - **Impact**: Slow LSP servers (e.g., Rust Analyzer on large
    codebases) can be given more time rather than causing silent fallback
    to non-LSP operation
  - **Affected**: pensive (LSP-based code review), sanctum (LSP
    documentation)
  - **Action Required**: None — defaults unchanged. Consider setting
    `startupTimeout` if LSP initialization is flaky on large repos

- ✅ **`isolation: worktree` in Agent Definitions**: Agents can now
  declaratively specify `isolation: worktree` in their frontmatter to
  request worktree-based isolation
  - **Impact**: Seven agents in the night-market ecosystem already
    adopted this field prior to official support — those definitions now
    activate official isolation behavior
  - **Affected**: Any agent definitions using `isolation: worktree` in
    frontmatter — verify all seven are correctly isolated now that the
    field is official
  - **Action Required**: Audit agents with `isolation: worktree` to
    confirm isolation behavior matches intent

- ✅ **`CLAUDE_CODE_DISABLE_1M_CONTEXT` Environment Variable**: New env
  var to disable 1M context window support
  - **Impact**: Constrained systems or workflows that prefer shorter
    context windows can opt out of 1M context
  - **Affected**: conserve:context-optimization (document as a tuning
    option)
  - **Action Required**: None — opt-in flag, no behavior change without
    setting it

- ✅ **Opus 4.6 Fast Mode 1M Context**: Fast mode now includes the full
  1M context window (previously limited)
  - **Impact**: Fast mode sessions on Opus 4.6 now have the same context
    capacity as standard mode
  - **Affected**: conjure agent-teams (Opus 4.6 fast mode users get
    longer context), conserve:context-optimization (update fast mode
    guidance)
  - **Action Required**: None — passive capability expansion

- ✅ **`CLAUDE_CODE_SIMPLE` Enhancement**: Now also disables MCP tools,
  attachments, hooks, and CLAUDE.md file loading
  - **Impact**: `CLAUDE_CODE_SIMPLE=1` now provides a fully
    stripped-down session — useful for benchmarking or constrained
    environments
  - **Affected**: abstract:escalation-governance (document SIMPLE mode
    implications), imbue:governance (CLAUDE.md loading disabled in
    SIMPLE mode — governance will not load)
  - **Action Required**: Ensure governance-critical workflows never run
    with `CLAUDE_CODE_SIMPLE=1`

**Bug Fixes**:
- ✅ **Memory Leaks Fixed (6+ sites)**: Fixed leaks in TaskOutput
  retained lines, CircularBuffer cleared items, shell command
  ChildProcess/AbortController references, LSP diagnostic data,
  completed task state objects, and agent teams completed teammate tasks
  - **Impact**: Long sessions with heavy Task tool spawning benefit
    significantly — RSS growth over time is reduced
  - **Affected**: conserve:context-optimization (update memory
    management guidance), conjure agent-teams (teammate task cleanup now
    automatic)
  - **Action Required**: None — passive improvement. Remove any manual
    workarounds for memory pressure in long sessions

- ✅ **Resumed Sessions with Symlinked Working Directories**: Fixed
  resumed sessions being invisible when the working directory involved
  symlinks
  - **Previous Bug**: `claude --resume` or `claude --continue` failed to
    find the session when cwd resolved through symlinks
  - **Now Fixed**: Session lookup now resolves symlinks before matching
  - **Affected**: sanctum session-management (resume patterns), conserve
    (session restart guidance)
  - **Action Required**: None — passive fix. Remove any workarounds that
    avoided symlinked working directories

- ✅ **Session Data Loss on SSH Disconnect**: Fixed session state loss on
  SSH disconnect by flushing before hooks and analytics in the shutdown
  sequence
  - **Previous Bug**: SSH disconnect triggered shutdown but hooks/
    analytics ran before flush, causing in-progress session state to be
    lost
  - **Now Fixed**: Flush happens first in shutdown sequence
  - **Affected**: sanctum session-management (session persistence
    reliability improves)
  - **Action Required**: None — passive reliability fix for SSH users

**Performance**:
- ✅ **Memory Reduction After Compaction**: Internal caches cleared after
  compaction, large tool results freed after processing, file history
  snapshots capped to prevent unbounded growth
  - **Impact**: Post-compaction memory footprint is lower; file history
    no longer grows without bound in very long sessions
  - **Affected**: conserve:context-optimization (update compaction
    guidance to note memory benefit)
  - **Action Required**: None — passive improvement

**Notes**:
- The worktree lifecycle hooks and `isolation: worktree` frontmatter
  together complete the agent isolation story for worktree-based
  workflows
- Memory leak fixes across 6+ sites plus post-compaction cache clearing
  make this a meaningful quality release for long sessions
- `CLAUDE_CODE_SIMPLE` now fully disables governance loading — ensure
  imbue/leyline governance is not expected to run in SIMPLE mode

> **Next**: See
> [February 2026 Early](compatibility-features-feb2026-early.md)

> **Next**: See [February 2026 Early](compatibility-features-feb2026-early.md) for versions 2.1.38-2.1.49.
