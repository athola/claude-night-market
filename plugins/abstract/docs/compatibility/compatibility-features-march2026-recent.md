# Claude Code Compatibility Features: March 2026 (Recent)

Feature timeline for Claude Code versions 2.1.63 through 2.1.71,
released in March 2026.

> **See Also**:
> [Features Index](compatibility-features.md) |
> [March 2026 Early](compatibility-features-march2026-early.md) |
> [Plugin Compatibility](compatibility-features-plugin-compat.md)

## Feature Timeline

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

### Claude Code 2.1.71 (March 2026)

**New Features**:
- ✅ **`/loop` Command and Cron Scheduling**: `/loop` runs prompts or
  slash commands on recurring intervals (e.g., `/loop 5m check the
  deploy`). Three new built-in tools: `CronCreate`, `CronList`,
  `CronDelete` for session-scoped scheduled tasks. Sessions hold up to
  50 tasks with 3-day auto-expiry. Disable with
  `CLAUDE_CODE_DISABLE_CRON=1`.
  - **Impact**: New scheduling capability. Hooks matching on tool names
    in PreToolUse/PostToolUse see these new tool names. The `/loop`
    command has no naming conflict with existing skills.
  - **Affected**: abstract:hook-authoring hook-types module (updated),
    abstract:hooks-eval sdk-hook-types module (updated),
    capabilities-hooks reference (updated),
    hook-types-comprehensive example (updated)
  - **Action Required**: Done - all 4 hook reference files updated with
    cron tools section

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
