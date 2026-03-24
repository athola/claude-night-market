# Claude Code Compatibility Features: February 2026 (Early)

Feature timeline for Claude Code versions 2.1.38 through 2.1.49,
released in February 2026.

> **See Also**:
> [Features Index](compatibility-features.md) |
> [March 2026](compatibility-features-march2026-recent.md) |
> [February 2026 Late](compatibility-features-feb2026-late.md) |
> [January 2026](compatibility-features-jan2026.md) |
> [Plugin Compatibility](compatibility-features-plugin-compat.md) |
> [Reference](compatibility-reference.md) |
> [2025 Archive](compatibility-features-2025.md)

## Feature Timeline

### Claude Code 2.1.49 (February 2026)

**New Features**:
- ✅ **Worktree Isolation for Subagents**: Introduced `isolation: "worktree"` parameter for the Task tool, enabling agents to run in temporary git worktrees with filesystem-level isolation
  - **Impact**: Parallel agents that modify files no longer risk merge conflicts or file-level races. Each agent gets its own working copy.
  - **Affected**: conjure:agent-teams (worktree alternative to inbox coordination), conserve:subagent-coordination (documented), sanctum:do-issue parallel-execution (documented)
  - **Action Required**: None - additive capability

- ✅ **Background Agent MCP Restriction**: Agents launched with `background: true` cannot use MCP tools
  - **Impact**: Subagents requiring MCP tool access (code execution servers, external connectors) must NOT be backgrounded
  - **Affected**: conserve:mcp-code-execution (mcp-subagents module documents this restriction)
  - **Action Required**: None - constraint documented in affected modules

### Claude Code 2.1.47 (February 2026)

**New Features**:
- ✅ **`last_assistant_message` in Stop/SubagentStop Hook Inputs**: New field added to Stop and SubagentStop hook inputs providing the final assistant response text
  - **Impact**: Hooks can now access the agent's final response directly without parsing transcript files
  - **Affected**: sanctum session-management (session_complete_notify.py hook can simplify transcript parsing), pensive code-refiner (Stop hook), sanctum pr-agent/commit-agent/git-workspace-agent (Stop hooks)
  - **Action Required**: None — additive feature. Existing hooks continue to work. Consider adopting for simpler transcript access.

- ✅ **`chat:newline` Keybinding Action**: New keybinding action for configurable multi-line input (#26075)
  - **Impact**: Users can customize how multi-line input works
  - **Affected**: None directly — user preference feature
  - **Action Required**: None

- ✅ **`added_dirs` in Status Line JSON**: Exposes directories added via /add-dir in the statusline workspace section (#26096)
  - **Impact**: External scripts and status line consumers can see added directories
  - **Affected**: conserve context-optimization (workspace awareness), abstract (status line parsing if any)
  - **Action Required**: None — informational

**Bug Fixes**:
- ✅ **Background Agent Transcript Fix**: Fixed background agent results returning raw transcript data instead of the agent's final answer (#26012)
  - **Impact**: `run_in_background: true` agents now return clean final answers — significant reliability improvement for background agent workflows
  - **Affected**: conserve:context-optimization (subagent-coordination module documents background agent workarounds), conjure:delegation-core (background delegation patterns)
  - **Action Required**: Remove any workarounds for raw transcript parsing from background agents

- ✅ **Parallel File Write/Edit Resilience**: Fixed an issue where a single file write/edit error would abort all other parallel file write/edit operations (#independent sibling fix)
  - **Impact**: Independent file mutations now complete even when a sibling fails — improves reliability of parallel agent workflows
  - **Affected**: superpowers:dispatching-parallel-agents, superpowers:subagent-driven-development
  - **Action Required**: None — passive improvement

- ✅ **Plan Mode Compaction Resilience**: Fixed plan mode being lost after context compaction (#26061)
  - **Impact**: Plan mode now survives context compaction — previously would silently switch to implementation mode
  - **Affected**: superpowers:writing-plans, superpowers:executing-plans, attune planning workflows
  - **Action Required**: None — removes a known pain point

- ✅ **Bash Permission Classifier Validation**: Fixed the bash permission classifier to validate that returned match descriptions correspond to actual input rules, preventing hallucinated descriptions from incorrectly granting permissions
  - **Impact**: Security improvement — prevents false permission grants from hallucinated rule descriptions
  - **Affected**: abstract:hook-authoring (security context), imbue:proof-of-work (validation integrity)
  - **Action Required**: None — internal security fix

- ✅ **Plugin Agent Skill Loading Fix**: Fixed plugin agent skills silently failing to load when referenced by bare name instead of fully-qualified plugin name (#25834)
  - **Impact**: Skills must use fully-qualified names (e.g., `plugin:skill-name` not just `skill-name`) — our ecosystem already follows this convention
  - **Affected**: All plugins with Skill() references (verified clean)
  - **Action Required**: None — our ecosystem already uses fully-qualified names

- ✅ **SKILL.md Frontmatter Robustness**: Fixed crashes when skill name/description is a bare number (#25837) or argument-hint uses YAML sequence syntax (#25826)
  - **Impact**: More resilient SKILL.md parsing
  - **Affected**: abstract:skill-authoring (authoring guidance), plugin-dev:skill-development
  - **Action Required**: None — our skills don't use these patterns, but good to know

- ✅ **Concurrent Agent Streaming Fix**: Fixed API 400 errors ("thinking blocks cannot be modified") in sessions with concurrent agents (#interleaved streaming blocks)
  - **Impact**: Concurrent agent sessions more stable — reduces intermittent API errors
  - **Affected**: conjure:agent-teams, superpowers:dispatching-parallel-agents
  - **Action Required**: None — passive stability improvement

- ✅ **Worktree Agent/Skill Discovery**: Fixed custom agents and skills not being discovered when running from a git worktree (#25816)
  - **Impact**: `.claude/agents/` and `.claude/skills/` from main repo now available in worktrees
  - **Affected**: superpowers:using-git-worktrees
  - **Action Required**: None — removes a limitation

- ✅ **Background Agent Lifecycle Change**: Use ctrl+f to kill all background agents instead of double-pressing ESC. ESC now only cancels the main thread.
  - **Impact**: Changed keyboard shortcut for killing background agents
  - **Affected**: Documentation only — no programmatic impact
  - **Action Required**: Update any documentation referencing ESC for background agent cancellation

- ✅ **SessionStart Hook Deferral**: Improved startup by deferring SessionStart hook execution (~500ms improvement)
  - **Impact**: SessionStart hooks now execute slightly after interactive prompt appears rather than blocking startup
  - **Affected**: imbue session-start.sh (governance injection), leyline git-platform (auto-detection)
  - **Action Required**: None — hooks still execute, just deferred. Governance injection may briefly lag behind prompt availability.

- ✅ **Memory Improvements**: Released API stream buffers, agent context, and skill state after use; eliminated O(n²) message accumulation in progress updates; trimmed agent task message history after completion
  - **Impact**: Long-running sessions and heavy agent workflows use significantly less memory
  - **Affected**: conserve:context-optimization (can update memory management guidance)
  - **Action Required**: None — passive improvement

- ✅ **Edit Tool Unicode Fix**: Fixed Edit tool silently corrupting Unicode curly quotes by replacing them with straight quotes (#26141)
  - **Impact**: Curly quotes in files are now preserved during edits — previously silently corrupted
  - **Affected**: scribe plugin (skills contain curly quotes in SKILL.md files)
  - **Action Required**: None — fix protects existing content

- ✅ **LSP gitignore Filter**: Fixed LSP findReferences returning results from gitignored files (e.g., node_modules/, venv/) (#26051)
  - **Impact**: LSP results now respect .gitignore — cleaner semantic search results
  - **Affected**: pensive (LSP-based reviews), sanctum (LSP documentation)
  - **Action Required**: None — quality improvement for LSP users

### Claude Code 2.1.46 (February 2026)

**New Features**:
- ✅ **Claude.ai MCP Connectors in Claude Code**: MCP servers configured at claude.ai/settings/connectors are now automatically available in Claude Code for users logged in with a claude.ai account
  - **Impact**: New source of MCP tools beyond local/project/user scopes — tools appear in `/mcp` with claude.ai indicators
  - **Affected**: conserve:mcp-code-execution (tool count inflation, tool search threshold), abstract:escalation-governance (haiku MCP context), conjure:delegation-core (alternative auth path)
  - **Action Required**: None — additive feature. Be aware that users may have additional MCP tools loaded from claude.ai connectors, increasing likelihood of hitting the 10% tool search threshold
  - **Known Issue**: Connectors can silently disappear (GitHub issue #21817) — do not assume connector availability is stable

**Bug Fixes**:
- ✅ **macOS Orphaned Process Fix**: Fixed orphaned Claude Code processes after terminal disconnect on macOS
  - **Impact**: Internal CC process lifecycle fix — no impact on plugin process management
  - **Affected**: sanctum session-management (troubleshooting context)
  - **Action Required**: None — internal fix

### Claude Code 2.1.45 (February 2026)

**New Features**:
- ✅ **Claude Sonnet 4.6 Support**: Added support for Claude Sonnet 4.6 model
  - **Impact**: Model shorthand `sonnet` in agent/subagent configs now resolves to Sonnet 4.6
  - **Affected**: conjure agent-teams spawning patterns, any Task tool calls using `model: "sonnet"`
  - **Action Required**: None — shorthand model names are version-agnostic

- ✅ **Plugin Settings from --add-dir**: `enabledPlugins` and `extraKnownMarketplaces` settings now read from `--add-dir` directories
  - **Impact**: Plugin discovery can be configured in shared team directories, not just user-level settings
  - **Affected**: Multi-plugin setups using `--add-dir` for shared configuration
  - **Action Required**: None — new capability, no breaking changes

- ✅ **Spinner Tips Customization**: New `spinnerTipsOverride` setting to customize spinner tips
  - **Impact**: Plugins can customize the tips shown during spinner animations
  - **Affected**: None currently — potential future enhancement for plugin UX
  - **Action Required**: None — opt-in feature

- ✅ **SDK Rate Limit Types**: New `SDKRateLimitInfo` and `SDKRateLimitEvent` types in the SDK
  - **Impact**: SDK consumers can now receive rate limit status including utilization, reset times, and overage info
  - **Affected**: leyline quota-management — could adopt SDK-native rate limit events in future
  - **Action Required**: None — existing quota tracking continues to work, SDK types are additive

**Bug Fixes**:
- ✅ **Agent Teams Bedrock/Vertex/Foundry Fix**: API provider environment variables now propagated to tmux-spawned processes
  - **Previous Bug**: Agent Teams teammates failed on Bedrock, Vertex, and Foundry because environment variables were not passed through to tmux sessions
  - **Now Fixed**: Environment variables properly propagated to tmux-spawned Claude instances
  - **Affected**: conjure agent-teams — tmux spawning patterns already correct, but teammates on enterprise providers now work reliably
  - **Action Required**: None — passive reliability fix for enterprise provider users

- ✅ **macOS Sandbox Temp Directory Fix**: Sandbox "operation not permitted" errors resolved on macOS
  - **Previous Bug**: Writing temporary files failed on macOS due to incorrect temp directory path
  - **Now Fixed**: Uses correct per-user temp directory
  - **Affected**: None — ecosystem code doesn't manage sandbox temp directories
  - **Action Required**: None

- ✅ **Background Agent Crash Fix**: Task tool (backgrounded agents) no longer crashes with ReferenceError on completion
  - **Previous Bug**: Backgrounded agents (`run_in_background: true`) could crash with a ReferenceError when completing their work
  - **Now Fixed**: Background agent completion handled cleanly
  - **Affected**: All plugins using parallel dispatch patterns (`superpowers:dispatching-parallel-agents`, conserve subagent coordination)
  - **Action Required**: None — passive reliability fix. Remove any retry-on-crash workarounds if present

- ✅ **Subagent Skill Compaction Fix**: Skills invoked by subagents no longer incorrectly appear in main session context after compaction
  - **Previous Bug**: When a subagent invoked a skill and the main session later compacted, the skill content leaked into the main session's context
  - **Now Fixed**: Subagent skill invocations properly scoped to the subagent's context
  - **Affected**: All subagent-heavy workflows — conserve context-optimization, superpowers parallel dispatch
  - **Action Required**: None — passive fix that improves context hygiene in long sessions

- ✅ **Plugin Hot-Loading**: Plugin-provided commands, agents, and hooks now available immediately after installation without restart
  - **Previous Bug**: Newly installed plugins required a Claude Code restart before their commands, agents, and hooks became available
  - **Now Fixed**: Plugin assets load immediately on installation
  - **Affected**: Installation documentation — remove restart advice from docs
  - **Action Required**: Update docs that tell users to restart after plugin installation

- ✅ **Autocomplete + Image Paste Fix**: Autocomplete suggestions now properly accepted on Enter when images are pasted
  - **Previous Bug**: Pasting images into input broke Enter-key autocomplete acceptance
  - **Now Fixed**: Autocomplete works correctly with pasted images
  - **Affected**: None — UI fix, no ecosystem code impact
  - **Action Required**: None

- ✅ **Excessive Backup Files Fix**: `.claude.json.backup` files no longer accumulate on every startup
  - **Previous Bug**: A new backup file was created on each startup, filling up the directory over time
  - **Now Fixed**: Backup file management is now clean
  - **Affected**: None — internal cleanup
  - **Action Required**: None

**Performance**:
- ✅ **Startup Performance**: Removed eager loading of session history for stats caching — faster startup
- ✅ **Memory Usage**: Shell commands with large output no longer cause unbounded RSS growth
- ✅ **UI Improvement**: Collapsed read/search groups now show current file/pattern being processed
- ✅ **VSCode**: Permission destination choice (project/user/session) persists across sessions

**Notes**:
- The subagent skill compaction fix and background agent crash fix together significantly improve reliability for subagent-heavy plugin workflows
- Plugin hot-loading removes a long-standing friction point in the plugin installation experience
- Sonnet 4.6 availability gives another model tier option for cost-sensitive subagent dispatch

### Claude Code 2.1.44 (February 2026)

**Bug Fixes**:
- ✅ **ENAMETOOLONG Fix for Deeply-Nested Paths**: File operations no longer fail with ENAMETOOLONG errors in deeply-nested directory structures
  - **Previous Bug**: Certain internal operations (likely temp file creation or path resolution) could exceed OS filename limits when working in deeply-nested directories
  - **Now Fixed**: Path handling uses truncation or hashing to stay within OS limits
  - **Affected**: None — longest ecosystem path is 165 chars, well within limits
  - **Action Required**: None

- ✅ **Auth Refresh Errors Fixed**: Follow-up to the 2.1.43 AWS auth timeout fix — auth refresh errors now handled gracefully
  - **Previous Bug**: Auth token refresh could produce errors even with the 2.1.43 timeout in place
  - **Now Fixed**: Refresh errors handled with proper retry/fallback
  - **Affected**: None — auth is handled by Claude Code internals
  - **Action Required**: None

**Notes**:
- Both fixes are internal reliability improvements with no ecosystem impact
- The ENAMETOOLONG fix is relevant for monorepos with deep `node_modules` or vendored dependency trees

### Claude Code 2.1.43 (February 2026)

**Bug Fixes**:
- ✅ **AWS Auth Refresh Timeout**: AWS auth refresh no longer hangs indefinitely — a 3-minute timeout has been added
  - **Previous Bug**: Bedrock auth token refresh could hang forever if the credentials endpoint was unresponsive
  - **Now Fixed**: 3-minute timeout with graceful failure
  - **Affected**: None — Bedrock auth is handled by Claude Code internals, not plugin code
  - **Action Required**: None — passive reliability fix for Bedrock users

- ✅ **Spurious Warnings for Non-Agent Markdown in `.claude/agents/`**: Non-agent markdown files in `.claude/agents/` no longer trigger validation warnings
  - **Previous Bug**: Any `.md` file in `.claude/agents/` was validated as an agent definition, producing warnings for README files or documentation placed there
  - **Now Fixed**: Only files with valid agent frontmatter are validated
  - **Affected**: None — all ecosystem agent directories contain only valid agent files
  - **Action Required**: None — but users who place documentation files in `.claude/agents/` will no longer see warnings

- ✅ **Structured-Outputs Beta Header Fix (Vertex/Bedrock)**: The `anthropic-beta: structured-outputs` header is no longer sent unconditionally on enterprise providers
  - **Previous Bug**: Beta header sent on all requests to Vertex/Bedrock, even when structured outputs weren't being used — some provider configurations rejected unknown beta headers
  - **Now Fixed**: Header only sent when structured outputs are actively requested
  - **Affected**: `imbue:structured-output` uses structured output patterns but doesn't control API headers — no ecosystem changes needed
  - **Action Required**: None — passive fix for enterprise provider compatibility

**Notes**:
- All three fixes target enterprise/Bedrock/Vertex reliability — no impact on first-party Anthropic API usage
- The agents directory warning fix is a quality-of-life improvement for users who store non-agent documentation alongside agents

### Claude Code 2.1.42 (February 2026)

**Improvements**:
- ✅ **Deferred Zod Schema Construction (Startup Performance)**: Tool schemas are now lazily constructed, improving startup time
  - **Impact**: Faster session initialization, especially noticeable with many plugins/MCP servers loaded
  - **Affected**: None — internal optimization, no ecosystem changes needed
  - **Action Required**: None — passive performance improvement

- ✅ **Date Moved Out of System Prompt (Prompt Cache Hit Rates)**: The current date is no longer injected into the static system prompt, improving prompt cache stability
  - **Previous**: `currentDate` embedded in system prompt caused daily cache invalidation (prompt hash changed every day)
  - **Now**: Date injected via ephemeral context (system-reminder), keeping the base system prompt stable across days
  - **Impact**: Better prompt cache hit rates for all sessions — particularly beneficial for skill-heavy plugin ecosystems where the system prompt is large
  - **Affected**: None — passive improvement; no ecosystem code parses `currentDate` from the system prompt
  - **Action Required**: None — automatic benefit

- ✅ **One-Time Opus 4.6 Effort Callout**: Eligible users see a one-time notification about Opus 4.6 effort settings
  - **Impact**: Informational UI notification only
  - **Affected**: None
  - **Action Required**: None

**Bug Fixes**:
- ✅ **`/resume` Interrupt Message Titles Fix (Follow-up)**: Session titles derived from interrupt messages no longer appear in the resume list
  - **Previous**: Partially fixed in 2.1.39 — some interrupt-derived titles still leaked through
  - **Now**: Complete fix — interrupt messages fully filtered from session title derivation
  - **Affected**: `sanctum:session-management` — improved resume experience
  - **Action Required**: None — completes the 2.1.39 fix

- ✅ **Image Dimension Limit Errors Suggest `/compact`**: When multiple images exceed dimension limits, error messages now suggest using `/compact` to reduce context
  - **Previous**: Generic dimension limit error with no actionable guidance
  - **Now**: Clear suggestion to use `/compact` as a resolution
  - **Affected**: None — no ecosystem code handles image dimensions
  - **Action Required**: None — UX improvement

**Notes**:
- The prompt cache improvement is the most significant change for plugin ecosystems — large system prompts with many skills benefit from stable caching across sessions
- The `/resume` interrupt title fix completes the partial 2.1.39 fix
- No breaking changes or ecosystem code modifications required

### Claude Code 2.1.41 (February 2026)

**New Features**:
- ✅ **`claude auth` CLI Subcommands**: `claude auth login`, `claude auth status`, and `claude auth logout` for managing Claude API authentication
  - **Distinct From**: Git platform auth commands (`gh auth login`, `glab auth login`) — these manage Claude API keys specifically
  - **Affected**: `leyline:authentication-patterns` — added note distinguishing Claude API auth from service auth
  - **Action Required**: None — progressive enhancement for API key management

- ✅ **Windows ARM64 Native Binary**: Claude Code now ships a native ARM64 binary for Windows on ARM
  - **Impact**: Better performance on ARM-based Windows devices (e.g., Surface Pro X, Snapdragon laptops)
  - **Action Required**: None — automatic platform detection

- ✅ **`/rename` Auto-Generates Session Names**: `/rename` without arguments now auto-generates a descriptive session name based on conversation content
  - **Previous**: `/rename` required a name argument
  - **Now**: No-argument invocation generates a name automatically
  - **Affected**: `sanctum:session-management` — updated `/rename` description
  - **Action Required**: None — progressive enhancement

**Bug Fixes**:
- ✅ **Background Task Notifications in Streaming Agent SDK Mode**: Background task notifications now fire correctly when using streaming mode with the Agent SDK
  - **Previous Bug**: Notifications were silently dropped in streaming SDK mode
  - **Now Fixed**: Notifications delivered reliably
  - **Affected**: `sanctum:do-issue`, `pensive:pr-review`, `sanctum:fix-pr` background agents
  - **Action Required**: None — passive fix

- ✅ **Proactive Ticks No Longer Fire in Plan Mode**: Proactive tick events are suppressed while in plan mode
  - **Previous Bug**: Proactive ticks could interrupt planning workflows
  - **Now Fixed**: Ticks suppressed during plan mode
  - **Affected**: `attune:blueprint`, `spec-kit` planning workflows — cleaner planning experience
  - **Action Required**: None — passive fix

- ✅ **Stale Permission Rules Cleared on Settings Change**: Permission rules now refresh immediately when settings files change on disk
  - **Previous Bug**: Stale permission rules persisted until session restart after editing settings
  - **Now Fixed**: Rules cleared and reloaded when settings change
  - **Affected**: `hookify` rules — changes take effect immediately without session restart
  - **Action Required**: None — passive fix

- ✅ **Permission Wait Time Excluded from Subagent Elapsed Time**: Time spent waiting for permission prompts no longer inflates subagent elapsed time display
  - **Previous Bug**: Subagent duration included time blocked on permission prompts, giving misleading timing
  - **Now Fixed**: Only actual execution time counted
  - **Action Required**: None — passive UX fix

- ✅ **@-Mention Anchor Fragment Resolution Fixed**: File references with anchor fragments (e.g., `@README.md#installation`) now resolve correctly
  - **Previous Bug**: Anchor fragments were ignored or caused resolution failures
  - **Now Fixed**: Fragment anchors properly resolved
  - **Action Required**: None — passive fix

- ✅ **FileReadTool No Longer Blocks on FIFOs/stdin/Large Files**: Read tool handles special files gracefully instead of hanging
  - **Previous Bug**: Attempting to read FIFOs, stdin, or extremely large files could block indefinitely
  - **Now Fixed**: Graceful handling with appropriate error messages
  - **Action Required**: None — passive reliability fix

- ✅ **Hook Blocking Stderr Rendered in UI**: Stderr output from hooks that block operations (exit code 2) is now displayed in the UI
  - **Completes**: 2.1.39 exit code 2 stderr fix — stderr is now rendered visually, not just preserved
  - **Affected**: All ecosystem hooks using exit code 2 blocking (conserve, sanctum, imbue, hookify)
  - **Action Required**: None — completes the 2.1.39 fix

**Notes**:
- `claude auth` CLI is distinct from git platform auth — it manages Claude API keys, not GitHub/GitLab tokens
- The `/rename` auto-name feature reduces friction in session management workflows
- Background task notification fix is significant for Agent SDK streaming workflows
- Plan mode tick suppression improves the planning experience for attune and spec-kit
- Permission rule refresh eliminates the need to restart sessions after editing hookify rules
- Recommended version bumped to 2.1.41+ due to streaming notification fix and permission rule refresh

### Claude Code 2.1.39 (February 2026)

**New Features**:
- ✅ **Nested Session Guard**: Claude Code now detects and prevents launching inside another Claude Code session
  - **Behavior**: If `CLAUDECODE=1` is already set in the environment (indicating an active session), launching `claude` will warn or block
  - **Impact**: Prevents accidental recursive session spawning that could cause confusion, resource waste, or context corruption
  - **Affected**: `conjure:agent-teams` spawning patterns — teammate sessions launched via tmux are unaffected because tmux creates independent shell environments
  - **Action Required**: Workflows that intentionally nest `claude` invocations (e.g., `claude -p` inside a `claude` session for quick queries) should be aware of this guard
  - **Note**: Agent teams set `CLAUDECODE=1` automatically — the guard distinguishes between intentional team spawning (via tmux panes) and accidental recursive invocation

- ✅ **OTel Speed Attribute**: Fast mode now tagged in OpenTelemetry events and trace spans via a `speed` attribute
  - **Impact**: Observability integrations can distinguish between fast mode and normal mode requests
  - **Affected**: Monitoring and observability documentation
  - **Action Required**: None — progressive enhancement for users with OTel tracing configured

**Bug Fixes**:
- ✅ **Agent Teams Model Fix for Bedrock/Vertex/Foundry**: Teammate agents now use correct model identifiers on non-Anthropic-API providers
  - **Previous Bug**: Agent teams on Bedrock, Vertex AI, or Foundry would use wrong model identifiers (e.g., non-qualified model IDs), causing 400 errors or falling back to wrong models ([#23499](https://github.com/anthropics/claude-code/issues/23499), [#5108](https://github.com/anthropics/claude-code/issues/5108))
  - **Now Fixed**: Model identifiers correctly qualified for each provider (e.g., `us.anthropic.claude-opus-4-6-v1` for Bedrock)
  - **Impact**: Agent teams now usable on enterprise cloud providers
  - **Affected**: `conjure:agent-teams` — added provider compatibility note to spawning patterns
  - **Action Required**: None — passive fix, existing `--model` flags work correctly

- ✅ **MCP Image Content Streaming Crash Fixed**: MCP tools returning image content during streaming no longer crash
  - **Previous Bug**: If an MCP tool returned image data while streaming was active, the response parser crashed
  - **Now Fixed**: Image content blocks handled correctly in streaming mode
  - **Impact**: MCP integrations with visual content (screenshots, diagrams) now work reliably
  - **Affected**: `scry:browser-recording` and any MCP-based image workflows
  - **Action Required**: None

- ✅ **Hook Exit Code 2 Stderr Now Displayed**: Hook blocking errors (exit code 2) now correctly show stderr output to the user
  - **Previous Bug**: When hooks returned exit code 2 (block decision), the stderr message explaining why the action was blocked was silently swallowed — users saw generic "hook error" instead of the hook's explanation ([#10964](https://github.com/anthropics/claude-code/issues/10964), [#10412](https://github.com/anthropics/claude-code/issues/10412))
  - **Now Fixed**: Stderr from exit code 2 hooks is properly displayed to the user, including from plugin-installed hooks
  - **Impact**: Hook developers can now rely on exit code 2 blocking with informative user-facing messages
  - **Affected**: `abstract:hook-authoring` — updated with exit code 2 blocking documentation
  - **Affected**: All ecosystem hooks that use blocking decisions (conserve, sanctum, imbue, hookify rules)
  - **Action Required**: None — existing hooks that use exit code 2 will now have their messages properly displayed

- ✅ **Improved Model Error Messages for Bedrock/Vertex/Foundry**: Error messages now include fallback suggestions when model requests fail on enterprise providers
  - **Previous**: Generic error messages without actionable guidance
  - **Now**: Specific error with fallback model suggestions (e.g., "Try using `us.anthropic.claude-sonnet-4-5-v1` instead")
  - **Impact**: Better debugging experience for enterprise users
  - **Action Required**: None

- ✅ **`/resume` Session Previews Show Clean Command Names**: Session preview no longer displays raw XML tags
  - **Previous Bug**: Session previews in `/resume` showed raw `<command-name>` XML tags instead of readable skill/command names
  - **Now Fixed**: Clean, readable command names displayed
  - **Impact**: Better session management UX — previously documented in 2.1.33 for a similar XML rendering issue
  - **Affected**: `sanctum:session-management` — improved resume experience
  - **Action Required**: None

- ✅ **`/resume` No Longer Shows Interrupt Messages as Titles**: Session titles derived from interrupts no longer pollute the resume list
  - **Previous Bug**: If a session was interrupted mid-execution, the interrupt message could become the session title shown in `/resume`
  - **Now Fixed**: Interrupt messages filtered from session title derivation
  - **Impact**: Cleaner session list in `/resume`
  - **Action Required**: None

- ✅ **Plugin Browse "Space to Toggle" Hint Fixed**: Already-installed plugins no longer show misleading toggle hint
  - **Previous Bug**: Browsing plugins showed "Space to Toggle" for plugins that were already installed, implying they could be toggled off (they need to be uninstalled)
  - **Now Fixed**: Correct action hint shown based on plugin state
  - **Impact**: Plugin management UX improvement
  - **Action Required**: None

- ✅ **Fatal Errors Now Displayed**: Fatal errors are no longer silently swallowed
  - **Previous Bug**: Some fatal errors were caught and discarded, leaving users with no indication of what went wrong
  - **Now Fixed**: Fatal errors properly surfaced to the user
  - **Impact**: Better debugging experience for all users
  - **Action Required**: None

- ✅ **Process No Longer Hangs After Session Close**: Fixed process remaining alive after session terminates
  - **Previous Bug**: Under certain conditions, the Claude Code process would hang after the session was closed, requiring manual termination
  - **Now Fixed**: Clean process exit on session close
  - **Impact**: Improved reliability for CI/CD pipelines and scripted workflows
  - **Action Required**: None

- ✅ **Terminal Rendering Improvements**: Multiple rendering fixes in this release
  - **Character loss at screen boundary**: Characters at the edge of the terminal screen are no longer lost during rendering
  - **Blank lines in verbose transcript**: Verbose transcript view no longer shows spurious blank lines
  - **General performance**: Terminal rendering performance improved across the board
  - **Impact**: Better visual experience, especially during long-running sessions
  - **Action Required**: None

**Notes**:
- The nested session guard is an important safety feature — but it does not affect agent teams or subagent workflows since those use tmux-based or Task tool-based isolation
- The hook exit code 2 stderr fix is significant for plugin developers — blocking hooks can now provide meaningful user-facing messages reliably
- The Agent Teams model fix makes multi-agent workflows viable on Bedrock, Vertex, and Foundry for the first time
- Terminal rendering improvements continue from 2.1.38's VS Code scroll fix
- Recommended version bumped to 2.1.39+ due to hook stderr fix and agent teams reliability


> **Next**: See [February 2026 Late](compatibility-features-feb2026-late.md) for versions 2.1.21-2.1.34.
