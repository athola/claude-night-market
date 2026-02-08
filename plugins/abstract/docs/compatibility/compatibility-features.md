# Claude Code Compatibility Features

Feature timeline and version-specific capabilities.

> **See Also**: [Reference](compatibility-reference.md) | [Patterns](compatibility-patterns.md) | [Issues](compatibility-issues.md)

## Feature Timeline

### Claude Code 2.1.34 (February 2026)

**Bug Fixes**:
- ✅ **Agent Teams Render Crash Fix**: Changing agent teams setting mid-session no longer crashes Claude Code
  - **Previous Bug**: Toggling `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` or `teammateMode` between renders caused a crash
  - **Now Fixed**: Settings changes handled gracefully during render cycles
  - **Impact**: Passive stability fix — no ecosystem changes needed
  - **Action Required**: None

- 🔒 **Sandbox Permission Bypass Fix**: Commands excluded from sandboxing no longer bypass permission prompts in auto-allow mode
  - **Previous Bug**: When `autoAllowBashIfSandboxed` was enabled, commands running outside the sandbox (via `sandbox.excludedCommands` or `dangerouslyDisableSandbox`) were auto-allowed without permission prompts
  - **Now Fixed**: Unsandboxed commands always go through normal permission flow, regardless of auto-allow mode
  - **Security Impact**: Commands like `docker` (commonly in `excludedCommands`) now properly prompt before running unsandboxed
  - **Affected**: `hookify:block-destructive-git` example — updated rationale text (previously described buggy behavior as expected)
  - **Action Required**: None for production workflows — the fix makes sandbox auto-allow mode safer by default

**Notes**:
- The sandbox permission fix is a security-relevant behavioral change — users relying on auto-allow mode now have proper permission gates for unsandboxed commands
- Agent teams render crash was an internal UI stability issue with no impact on coordination patterns
- Recommended version bumped to 2.1.34+ due to the security fix

### Claude Code 2.1.33 (February 2026)

**New Features**:
- ✅ **TeammateIdle and TaskCompleted Hook Events**: New hook events for multi-agent coordination
  - **TeammateIdle**: Triggered when a teammate agent becomes idle
  - **TaskCompleted**: Triggered when a task finishes execution
  - **Affected**: `abstract:hook-authoring` updated with new events, `abstract:hooks-eval` updated with types
  - **Affected**: `conserve:subagent-coordination` updated with coordination hook patterns
  - **Action Required**: None — progressive enhancement for agent teams workflows

- ✅ **Task(agent_type) Sub-Agent Restrictions**: Restrict sub-agent spawning via tools frontmatter
  - **Syntax**: `Task(specific-agent)` in agent `tools:` list
  - **Impact**: Fine-grained control over delegation chains
  - **Affected**: `abstract:plugin-validator` updated with validation for new syntax
  - **Affected**: `conserve:mcp-subagents` and `conserve:subagent-coordination` updated with restriction patterns
  - **Action Required**: Consider adding restrictions to pipeline agents

- ✅ **Agent Memory Frontmatter**: Persistent memory for agents with scope control
  - **Syntax**: `memory: user|project|local` in agent frontmatter
  - **Impact**: Agents can record and recall memories across sessions
  - **Affected**: `abstract:plugin-validator` updated with memory field validation
  - **Affected**: memory-palace, sanctum, conserve, abstract agents updated with `memory: project`
  - **Action Required**: None — progressive enhancement, opt-in per agent

- ✅ **Plugin Name in Skill Descriptions**: Plugin name auto-displayed in `/skills` menu
  - **Impact**: Better skill discoverability, no need to repeat plugin name in descriptions
  - **Affected**: `abstract:skill-authoring` updated with guidance to avoid redundant plugin names
  - **Action Required**: None — cosmetic enhancement

**Bug Fixes**:
- ✅ **Agent Teammate Sessions in tmux**: Fixed send/receive for teammate sessions
- ✅ **Agent Teams Plan Warnings**: Fixed incorrect "not available" warnings
- ✅ **Thinking Interruption Fix**: New message during extended thinking no longer interrupts
- ✅ **API Proxy 404 Fix**: Streaming 404 errors no longer trigger non-streaming fallback
- ✅ **Proxy Settings for WebFetch**: Environment proxy settings now applied to HTTP requests
- ✅ **Resume Session Picker**: Shows clean titles instead of raw XML markup
- ✅ **API Error Messages**: Shows specific cause (ECONNREFUSED, SSL) instead of generic errors
- ✅ **Managed Settings Errors**: Invalid settings errors now surfaced to user

**Notes**:
- TeammateIdle and TaskCompleted hooks extend agent teams coordination capabilities
- Task(agent_type) provides governance over delegation chains — use for pipeline agents
- Agent memory is opt-in and does not overlap with Memory Palace structured knowledge

### Claude Code 2.1.32 (February 2026)

**New Model**:
- ✅ **Claude Opus 4.6**: New flagship model with 200K context (1M beta), 128K max output, adaptive thinking with effort controls
  - **Effort Controls**: 4 levels (low/medium/high/max) trade reasoning depth against speed/cost
  - **Adaptive Thinking**: `thinking: {type: "adaptive"}` — Claude decides when and how deeply to think
  - **Server-Side Compaction**: Automatic API-level context summarization for infinite conversations
  - **Affected**: `abstract:model-optimization-guide` updated with Opus 4.6 capabilities and effort controls as escalation alternative
  - **Affected**: `abstract:escalation-governance` updated with effort controls as complementary axis
  - **Affected**: `conserve:mecw-principles` updated with variable context window thresholds

**New Features**:
- ✅ **Agent Teams (Research Preview)**: Multi-agent collaboration with lead/teammate roles
  - **Enable**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
  - **Capabilities**: Shared task lists, inter-agent messaging, lead coordination
  - **Limitations**: No session resumption with teammates, one team per session, no nested teams, token-intensive
  - **Affected**: `conserve:subagent-coordination` updated with agent teams comparison and guidance
  - **Action Required**: None for production workflows — experimental feature

- ✅ **Automatic Memory Recording**: Claude records and recalls memories across sessions
  - **Impact**: Passive cross-session continuity without manual checkpoints
  - **Affected**: `memory-palace/README.md` updated with differentiation from native memory
  - **Affected**: `sanctum:session-management` updated with automatic memory section
  - **Affected**: `conserve:token-conservation` updated noting memory token overhead
  - **Action Required**: None — automatic behavior on first-party API

- ✅ **"Summarize from here"**: Partial conversation summarization via message selector
  - **Impact**: Middle ground between `/compact` (full) and `/new` (clean slate)
  - **Affected**: `conserve:token-conservation` step 4 updated with partial summarization option
  - **Affected**: `conserve:clear-context` updated as alternative before full auto-clear
  - **Affected**: `conserve:mecw-principles` updated with partial summarization reference

- ✅ **Skills from `--add-dir` Auto-Loaded**: Skills in `.claude/skills/` within additional directories now auto-discovered
  - **Previous**: Only CLAUDE.md from `--add-dir` was loaded (2.1.20)
  - **Now**: Skills also auto-discovered from additional directories
  - **Impact**: Better monorepo support — package-specific skills work with `--add-dir`
  - **Affected**: `abstract:skill-authoring` — monorepo skill patterns now fully supported

- ✅ **Skill Character Budget Scales**: 2% of context window instead of fixed limit
  - **Impact**: Larger context windows = more room for skill descriptions (200K → ~4K chars, 1M → ~20K chars)
  - **Affected**: `abstract:skill-authoring` updated with scaling budget table
  - **Action Required**: None — previously truncated skills may now display fully

- ✅ **`--resume` Re-uses `--agent`**: Resume preserves agent value from previous session
  - **Impact**: Agent-specific workflows resume seamlessly
  - **Affected**: `sanctum:session-management` updated with agent persistence note

**Bug Fixes**:
- ✅ **Heredoc JavaScript Template Literal Fix**: `${index + 1}` in heredocs no longer causes "Bad substitution"
  - **Previous Bug**: Heredocs containing JS template literals interrupted tool execution
  - **Now Fixed**: Bash tool handles template literals correctly
  - **Impact**: Passive fix — 8 ecosystem files using heredocs benefit automatically

- ✅ **@ File Completion Fix**: Fixed incorrect relative paths when running from subdirectories
- ✅ **Thai/Lao Spacing Vowels Fix**: Input rendering fix for Thai/Lao characters

**Notes**:
- Opus 4.6 effort controls provide a new cost/quality axis complementary to model escalation
- Agent teams are experimental — use Task tool patterns for production workflows
- Automatic memory overlaps with memory-palace but serves different purpose (session continuity vs structured knowledge)
- Skill budget scaling reduces pressure on aggressive description compression

### Claude Code 2.1.31 (February 2026)

**Behavioral Changes**:
- ✅ **Strengthened Dedicated Tool Preference**: System prompts now more aggressively guide toward Read, Edit, Glob, Grep instead of bash equivalents (cat, sed, grep, find)
  - **Previous (2.1.21)**: Initial file operation tool preference introduced
  - **Now (2.1.31)**: Guidance is stronger and more explicit — reduces unnecessary Bash command usage further
  - **Impact**: Skills/agents with bash-based file operation examples may see Claude prefer native tools instead
  - **Affected**: `conserve:ai-hygiene-auditor` pseudocode, `conserve:bloat-detector` patterns — added clarifying notes
  - **Action Taken**: Updated bloat-detector and ai-hygiene-auditor docs to clarify bash snippets are for external script execution

**Bug Fixes**:
- ✅ **PDF Session Lock-Up Fix**: PDF-too-large errors no longer permanently lock sessions
  - **Previous Bug**: Oversized PDFs could make sessions completely unusable, requiring a new conversation
  - **Now Fixed**: Error handled gracefully with clear limits shown (100 pages max, 20MB max)
  - **Impact**: Sessions are more resilient during PDF-heavy workflows
  - **Affected**: `conserve:token-conservation` — updated with explicit PDF limits

- ✅ **Bash Sandbox "Read-only file system" Fix**: Bash commands no longer falsely report failure in sandbox mode
  - **Previous Bug**: Sandbox mode could cause spurious "Read-only file system" errors on valid commands
  - **Now Fixed**: Sandbox isolation no longer produces false-positive errors
  - **Impact**: Agents using Bash tool with sandbox mode enabled now get accurate results
  - **Action Required**: None — passive fix, no workarounds existed to remove

- ✅ **Plan Mode Crash Fix**: Entering plan mode no longer crashes when `~/.claude.json` is missing default fields
  - **Previous Bug**: Sessions became unusable after entering plan mode with incomplete project config
  - **Now Fixed**: Missing fields handled gracefully
  - **Affected**: `spec-kit:spec-writing` references plan mode — no changes needed

- ✅ **temperatureOverride Streaming Fix**: `temperatureOverride` now respected in streaming API path
  - **Previous Bug**: All streaming requests silently used default temperature (1.0) regardless of configured override
  - **Now Fixed**: Custom temperature correctly applied to streaming requests
  - **Impact**: SDK integrations using streaming with custom temperature will now produce different (correct) outputs
  - **Action Required**: None for ecosystem — but SDK users should verify their temperature-dependent workflows

- ✅ **LSP Shutdown/Exit Compatibility**: Fixed null params handling for strict language servers
  - **Previous Bug**: Language servers requiring non-null params for shutdown/exit (e.g., rust-analyzer, clangd) could fail
  - **Now Fixed**: Proper null-safe params sent during LSP lifecycle
  - **Impact**: Improved LSP stability for strict servers — benefits `pensive` and `sanctum` LSP workflows
  - **Affected**: LSP experimental status (Issue #72) — incrementally more stable

**UX Improvements**:
- ✅ **Session Resume Hint on Exit**: Claude Code now shows how to continue the conversation when exiting
  - **Impact**: Improved discoverability of `--resume` functionality
  - **Affected**: `sanctum:session-management` — users will discover resume patterns organically
  - **Action Taken**: Updated session-management skill with reference to this feature

- ✅ **Improved PDF/Request Error Messages**: Now shows actual limits (100 pages, 20MB) instead of generic errors
  - **Impact**: Better user experience during PDF and large request workflows
  - **Affected**: `conserve:token-conservation` — updated with explicit limits

- Reduced layout jitter when spinner appears/disappears during streaming
- Full-width (zenkaku) space input support from Japanese IME in checkbox selection
- Removed misleading Anthropic API pricing from model selector for third-party provider users

**Notes**:
- The strengthened tool preference reinforces 2.1.21's direction — ecosystem bash-based analysis scripts are unaffected (they run as subprocesses), but skills should prefer native tools for direct analysis
- PDF session lock-up was a critical reliability issue now resolved
- temperatureOverride fix may change outputs for SDK streaming integrations that previously defaulted to temperature 1.0
- LSP improvements incrementally improve the experimental feature's stability

### Claude Code 2.1.30 (February 2026)

**New Features**:
- ✅ **Read Tool PDF Pages Parameter**: `pages` parameter for targeted PDF reading (e.g., `pages: "1-5"`)
  - Large PDFs (>10 pages) now return lightweight reference when @-mentioned instead of inlining into context
  - **Affected**: `conserve:token-conservation` — new token-saving technique for PDF-heavy workflows
  - **Action Required**: Update token conservation guidance to recommend `pages` parameter for PDFs

- ✅ **Task Tool Metrics**: Token count, tool uses, and duration metrics now included in Task tool results
  - **Impact**: Subagent coordination can now measure actual efficiency instead of estimating
  - **Affected**: `conserve:subagent-coordination` efficiency calculations, `conserve:mcp-code-execution` coordination metrics
  - **Action Required**: Update subagent decision frameworks to incorporate real measured metrics from prior Task invocations

- ✅ **MCP OAuth Client Credentials**: Pre-configured OAuth for MCP servers without Dynamic Client Registration
  - **Usage**: `--client-id` and `--client-secret` with `claude mcp add`
  - **Use Case**: Slack and similar services that require pre-configured OAuth
  - **Affected**: `conjure:delegation-core` — new MCP authentication option for external services
  - **Action Required**: None — progressive enhancement for MCP server configuration

- ✅ **`/debug` Command**: Session troubleshooting command
  - **Impact**: New diagnostic tool for troubleshooting session issues
  - **Action Required**: None — reference in troubleshooting documentation

- ✅ **Expanded Read-Only Git Flags**: `--topo-order`, `--cherry-pick`, `--format`, `--raw` for `git log` and `git show`
  - **Impact**: Read-only agents can now produce structured git output and more precise change detection
  - **Affected**: `sanctum:git-workspace-agent`, `imbue:catchup`, `imbue:diff-analysis`
  - **Action Required**: None — progressive enhancement for git-based analysis agents

- ✅ **Improved TaskStop Display**: Shows stopped command/task description instead of generic "Task stopped"
  - **Impact**: Better debugging of multi-agent workflows when subagents are stopped
  - **Affected**: `conserve:subagent-coordination` monitoring patterns
  - **Action Required**: None — passive improvement

**Bug Fixes**:
- ✅ **Subagent SDK MCP Tool Access**: Fixed subagents not being able to access SDK-provided MCP tools
  - **Previous Bug**: SDK-provided MCP tools were not synced to shared application state, so subagents couldn't use them
  - **Now Fixed**: MCP tools properly synced across subagent boundaries
  - **Impact**: Any workflow delegating MCP tool usage to subagents was silently broken
  - **Affected**: `conserve:mcp-code-execution/mcp-subagents`, `conjure:delegation-core` subagent patterns
  - **Action Required**: Remove any workarounds for MCP tool access in subagents

- ✅ **Phantom "(no content)" Text Blocks**: Fixed empty blocks in API conversation history
  - **Previous Bug**: Phantom blocks wasted tokens and confused model reasoning
  - **Now Fixed**: Clean conversation history without empty blocks
  - **Impact**: More accurate MECW calculations, reduced token waste
  - **Affected**: `conserve:context-optimization` MECW threshold accuracy — passive improvement

- ✅ **Prompt Cache Invalidation**: Fixed cache not invalidating when tool descriptions/schemas changed
  - **Previous Bug**: Cache only invalidated on tool *name* changes, not description/schema changes
  - **Now Fixed**: Cache properly invalidates on any tool metadata change
  - **Impact**: More reliable behavior when MCP tool schemas evolve
  - **Action Required**: None — passive fix

- ✅ **Session Resume Memory**: 68% memory reduction for `--resume` via stat-based session loading
  - **Previous**: Full session index loaded into memory
  - **Now**: Lightweight stat-based loading with progressive enrichment
  - **Impact**: Faster resume for users with many sessions
  - **Affected**: `sanctum:session-management` — improved resume performance

- ✅ **Session Resume Hang Fix**: Fixed hang when resuming sessions with corrupted transcript files (parentUuid cycles)
  - **Impact**: More robust session resumption — no code changes needed

- Fixed 400 errors after `/login` with thinking blocks
- Fixed rate limit message showing incorrect "/upgrade" for Max 20x users
- Fixed permission dialogs stealing focus while typing
- Fixed Windows `.bashrc` regression for Bash commands

**UX Improvements**:
- `/model` now executes immediately instead of being queued
- Added reduced motion mode to config

**Notes**:
- Task tool metrics enable data-driven subagent delegation decisions — a significant improvement for MECW optimization
- SDK MCP tool fix resolves silent failures in subagent MCP workflows
- Prompt cache fix improves reliability for workflows with evolving MCP tool schemas
- Resume memory improvements benefit heavy session users

### Claude Code 2.1.29 (February 2026)

**Bug Fixes**:
- ✅ **Session Resume Performance**: Fixed startup performance issues when resuming sessions with `saved_hook_context`
  - **Root Cause**: Sessions accumulating `once: true` hook state (from skill/agent frontmatter hooks) experienced slow resume times as the saved context grew
  - **Impact**: Passive improvement for all ecosystem components using `once: true` hooks — no code changes needed
  - **Affected Components**: `conserve:context-optimization`, `conserve:bloat-scan`, `sanctum:commit-agent`, `sanctum:prepare-pr`, `sanctum:update-dependencies`, `sanctum:git-workspace-review`, `pensive:architecture-reviewer`, `abstract:plugin-validator`
  - **Action Required**: None — internal performance optimization with no API or behavioral changes

**Notes**: Pure performance fix. No breaking changes, no API changes, no schema changes.

### Claude Code 2.1.22–2.1.27 (February 2026)

Stabilization releases. Key changes:

- ✅ **PR-Linked Sessions** (2.1.27): `--from-pr` flag resumes sessions by PR number/URL; sessions auto-linked when using `gh pr create`
  - **Affected**: `sanctum:session-management` updated with PR session workflow pattern
- ✅ **Ripgrep Timeout Reporting** (2.1.23): Search timeouts now report errors instead of silently returning empty results
  - **Impact**: Grep tool results are more reliable; no ecosystem code changes needed
- ✅ **Async Hook Cancellation** (2.1.23): Pending async hooks properly cancelled when headless sessions end
  - **Impact**: No ecosystem hooks affected (all synchronous)
- ✅ **Structured Output Fix** (2.1.22): Fixed `--output-format json` in `-p` mode
- ✅ **Per-User Temp Directory Isolation** (2.1.23): Prevents permission conflicts on shared systems
- ✅ **Debug Logging** (2.1.27): Tool call failures and denials now in debug logs
- Various Bedrock/Vertex gateway fixes (2.1.25, 2.1.27), Windows fixes (2.1.27), UI fixes

**Notes**: No breaking changes. PR-linked sessions are a progressive enhancement for PR review workflows.

### [Claude Code 2.1.21](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2121) (February 2026)

**Bug Fixes**:
- ✅ **Auto-Compact Threshold Fix**: Auto-compact no longer triggers too early on models with large output token limits
  - **Previous Bug**: Models with large max output tokens (e.g., Opus) could see compaction trigger well below the expected ~160k threshold
  - **Now Fixed**: Effective context calculation properly accounts for output token reservation
  - **Affected**: `conserve:subagent-coordination` compaction threshold documentation updated

- ✅ **Task ID Reuse Fix**: Task IDs no longer reused after deletion
  - **Previous Bug**: Deleting a task and creating a new one could silently reuse the same ID, leaking old state
  - **Now Fixed**: Deleted task IDs are properly retired
  - **Affected**: `imbue:proof-of-work`, `sanctum:session-management` — both updated with version note

- ✅ **Session Resume During Tool Execution**: Fixed API errors when resuming sessions interrupted during tool execution
  - **Previous Bug**: Sessions interrupted mid-tool-execution could fail to resume
  - **Now Fixed**: Tool execution state properly handled on resume
  - **Affected**: `sanctum:session-management` troubleshooting section updated

**Behavioral Changes**:
- ✅ **File Operation Tool Preference**: Claude now prefers native file tools (Read, Edit, Write, Grep, Glob) over bash equivalents (cat, sed, awk, grep, find)
  - **Impact**: Ecosystem guidance recommending `rg`/`sed -n` via Bash now conflicts with system prompt
  - **Affected**: `conserve:token-conservation`, `docs/guides/rules-templates.md`, `docs/claude-rules-templates.md`
  - **Action Taken**: Updated all three files to recommend Read with offset/limit and Grep tool instead

**Other Fixes**:
- Fixed full-width (zenkaku) number input from Japanese IME in option selection prompts
- Fixed shell completion cache files being truncated on exit
- Fixed file search not working in VS Code extension on Windows

**UX Improvements**:
- Improved read/search progress indicators to show "Reading…" while in progress and "Read" when complete

**Notes**:
- The file operation tool preference is a system prompt change, not a feature flag — aligns Claude behavior with tool capabilities
- Task ID reuse fix makes the 2.1.20 deletion feature safe for production use
- Auto-compact fix improves reliability of MECW threshold calculations across model tiers

### [Claude Code 2.1.20](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2120) (February 2026)

**New Features**:
- ✅ **TaskUpdate Delete**: Tasks can now be deleted via the TaskUpdate tool
  - **Impact**: Workflows creating many TodoWrite items can clean up after completion
  - **Affected**: `sanctum:session-management`, `imbue:proof-of-work`
  - **Best Practice**: Delete transient tracking items; preserve proof-of-work and audit items
  - **Ecosystem Updates**: TodoWrite pattern docs updated with deletion guidelines

- ✅ **Background Agent Permission Prompting**: Background agents now prompt for tool permissions before launching
  - **Previous**: Permissions resolved during background execution (could stall)
  - **Now**: Permissions confirmed upfront before agent enters background
  - **Impact**: Multi-agent dispatches show sequential permission prompts before work begins
  - **Affected**: All 41 ecosystem agents, `conserve:subagent-coordination` patterns
  - **Action Required**: None — improved behavior, but document for user expectations

- ✅ **`Bash(*)` Permission Normalization**: `Bash(*)` now treated as equivalent to plain `Bash`
  - **Previous**: `Bash(*)` and `Bash` were distinct permission rules
  - **Now**: Collapsed to equivalent behavior
  - **Impact**: Scoped wildcards (`Bash(npm *)`) remain distinct and valid
  - **Affected**: `abstract:plugin-validator` — should warn on redundant `Bash(*)` usage
  - **Action Required**: Update plugin validation to flag `Bash(*)` as redundant

- ✅ **CLAUDE.md from Additional Directories**: Load CLAUDE.md from `--add-dir` directories
  - **Requires**: `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` environment variable
  - **Use Case**: Monorepo setups where package-specific CLAUDE.md files are needed
  - **Affected**: `attune:arch-init` monorepo initialization patterns
  - **Ecosystem Impact**: No changes needed — progressive enhancement for monorepo users

- ✅ **PR Review Status Indicator**: Branch PR state shown in prompt footer
  - **States**: Approved, changes requested, pending, or draft (colored dot with link)
  - **Impact**: Better visibility during PR workflows — no code changes needed

- ✅ **Config Backup Rotation**: Timestamped backups with rotation (keeping 5 most recent)
  - **Previous**: Config backups could accumulate or become corrupted (partially fixed in 2.1.6)
  - **Now**: Permanent solution with automatic rotation
  - **Impact**: No ecosystem changes needed — resolves long-standing config backup issues

**Bug Fixes**:
- ✅ **Session Compaction Resume Fix**: Resume now loads compact summary instead of full history
  - **Previous Bug**: Resumed sessions could reload entire uncompacted conversation
  - **Now Fixed**: Compact summary loaded correctly on resume
  - **Impact**: More reliable session resumption; `sanctum:session-management` troubleshooting updated
  - **Affected**: `conserve:subagent-coordination` compaction documentation updated

- ✅ **Agent Message Handling Fix**: Agents no longer ignore user messages sent while actively working
  - **Previous Bug**: Messages sent during agent execution could be silently dropped
  - **Now Fixed**: User messages respected during active agent work
  - **Impact**: Corrections and cancellations during agent execution now work reliably

- Fixed wide character (emoji, CJK) rendering artifacts
- Fixed JSON parsing errors when MCP tool responses contain special Unicode characters
- Fixed draft prompt lost when pressing UP arrow to navigate command history
- Fixed ghost text flickering when typing slash commands mid-input
- Fixed marketplace source removal not properly deleting settings
- Fixed duplicate output in `/context` command
- Fixed task list sometimes showing outside the main conversation view
- Fixed syntax highlighting for diffs within multiline constructs (e.g., Python docstrings)
- Fixed crashes when cancelling tool use

**UX Improvements**:
- Improved `/sandbox` command to show dependency status with installation instructions
- Improved thinking status text with shimmer animation
- Task list dynamically adjusts visible items based on terminal height
- Collapsed read/search groups show present tense while in progress, past tense when complete
- ToolSearch results appear as brief notification instead of inline
- `/copy` command available to all users
- Fork conversation hint shows how to resume original session

**Other Changes**:
- `/commit-push-pr` skill auto-posts PR URLs to Slack when configured via MCP
- Arrow key history navigation in vim normal mode when cursor cannot move further
- Ctrl+G (external editor) added to help menu

**Notes**:
- TaskUpdate delete enables cleaner workflow tracking — update TodoWrite patterns to include cleanup phase
- Background agent permissions improve reliability of multi-agent workflows
- `Bash(*)` normalization simplifies permission rule configuration
- Session resume fix makes long-running session workflows more reliable

### [Claude Code 2.1.19](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2119) (February 2026)

**New Features**:
- ✅ **CLAUDE_CODE_ENABLE_TASKS**: Environment variable to disable new task system
  - **Usage**: `CLAUDE_CODE_ENABLE_TASKS=false` reverts to old system temporarily
  - **Use Case**: CI/CD pipelines or workflows dependent on previous task behavior
  - **Ecosystem Impact**: Subagent delegation via Task tool still works; this controls the UI task system

- ✅ **Command Argument Shorthand**: `$0`, `$1`, etc. for individual arguments in custom commands
  - **Previous**: Only `$ARGUMENTS` (full string) or `$ARGUMENTS.0` (indexed, now deprecated)
  - **Now**: `$0`, `$1` shorthand plus `$ARGUMENTS[0]` bracket syntax
  - **Breaking Change**: `$ARGUMENTS.0` dot syntax replaced with `$ARGUMENTS[0]` bracket syntax
  - **Ecosystem Impact**: No commands use indexed argument access (all use `$ARGUMENTS` as whole string)
  - **Action Required**: Update `abstract:create-command` documentation to teach new syntax

- ✅ **Skills Auto-Approval**: Skills without additional permissions or hooks now allowed without user approval
  - **Impact**: Faster skill invocation for read-only and analysis skills
  - **Ecosystem Impact**: Many ecosystem skills benefit (no hooks or special permissions needed)

**Bug Fixes**:
- Fixed `/rename` and `/tag` not updating correct session in git worktrees
  - **Affected**: `sanctum:session-management` workflows — improved reliability, no changes needed
- Fixed resuming sessions by custom title from different directories
- Fixed backgrounded hook commands not returning early (potential session blocking)
  - **Ecosystem Impact**: No hooks use shell backgrounding — no changes needed
- Fixed agent list showing "Sonnet (default)" instead of "Inherit (default)" for agents without explicit model
  - **Ecosystem Impact**: All 28 ecosystem agents set model explicitly — no changes needed
- Fixed file write preview omitting empty lines
- Fixed pasted text lost when using prompt stash (Ctrl+S) and restore
- Fixed crashes on processors without AVX instruction support
- Fixed dangling processes when terminal closed

**SDK**:
- Added replay of queued_command attachment messages as SDKUserMessageReplay events

**Notes**:
- The `$ARGUMENTS[0]` bracket syntax replaces `$ARGUMENTS.0` dot syntax — update command authoring docs
- Skills auto-approval improves UX for the majority of ecosystem skills
- CLAUDE_CODE_ENABLE_TASKS provides a fallback for workflows dependent on old task behavior

### [Claude Code 2.1.18](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2118) (February 2026)

**New Features**:
- ✅ **Customizable Keyboard Shortcuts**: Full keybinding customization via `~/.claude/keybindings.json`
  - **Configuration**: Run `/keybindings` to create or open config file
  - **Hot-Reload**: Changes applied automatically without restarting Claude Code
  - **17 Contexts**: `Global`, `Chat`, `Autocomplete`, `Settings`, `Confirmation`, `Tabs`, `Help`, `Transcript`, `HistorySearch`, `Task`, `ThemePicker`, `Attachments`, `Footer`, `MessageSelector`, `DiffDialog`, `ModelPicker`, `Select`, `Plugin`
  - **Chord Sequences**: Multi-key sequences like `ctrl+k ctrl+s`
  - **Unbinding**: Set action to `null` to remove default shortcuts
  - **Reserved Keys**: `Ctrl+C` (interrupt) and `Ctrl+D` (exit) cannot be rebound
  - **Terminal Conflict Awareness**: Documents `Ctrl+B` (tmux), `Ctrl+A` (screen), `Ctrl+Z` (suspend) conflicts
  - **Vim Mode Compatibility**: Keybindings and vim mode operate independently at different levels
  - **Validation**: `/doctor` shows keybinding warnings for parse errors, invalid contexts, conflicts
  - **Plugin Context**: `plugin:toggle` (Space) and `plugin:install` (I) for plugin management UI
  - **Schema Support**: JSON Schema at `schemastore.org` for editor autocompletion
  - **Documentation**: https://code.claude.com/docs/en/keybindings
  - **Ecosystem Impact**: No plugin code changes needed — keybindings are a user-facing UI layer
  - **Action Required**: None — existing workflows unaffected
  - **Note**: Skills/hooks/agents that reference specific default shortcuts (e.g., `Ctrl+B` for background tasks) should use descriptive language rather than hardcoded key references, since users may rebind them

### [Claude Code 2.1.9](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#219) (January 2026)

**New Features**:
- ✅ **MCP Tool Search Threshold Configuration**: `auto:N` syntax for configuring threshold
  - **Usage**: `ENABLE_TOOL_SEARCH=auto:5` sets 5% threshold (default is 10%)
  - **Impact**: Fine-grained control over when tools are deferred to MCPSearch
  - **Use Case**: Lower thresholds for context-sensitive workflows, higher for tool-heavy setups

- ✅ **plansDirectory Setting**: Customize where plan files are stored
  - **Configuration**: Set in `/config` or `settings.json`
  - **Default**: Plans stored in project directory
  - **Affected**: `spec-kit` workflows can specify custom plan locations
  - **Use Case**: Centralized planning, monorepo support

- ✅ **PreToolUse additionalContext**: Hooks can now inject context before tool execution
  - **Previous**: Only PostToolUse could return `additionalContext`
  - **Now**: PreToolUse hooks can return `hookSpecificOutput.additionalContext`
  - **Impact**: Inject relevant context/guidance before a tool runs
  - **Affected**: `abstract:hook-authoring` patterns, memory-palace research interceptor
  - **Use Case**: Provide cached results, inject warnings, add relevant context
  - **Ecosystem Updates**:
    - `sanctum:security_pattern_check.py` - Now injects security warnings as visible context
    - `abstract:pre_skill_execution.py` - Now injects skill execution context
    - `memory-palace:research_interceptor.py` - Already used additionalContext (no changes needed)

- ✅ **${CLAUDE_SESSION_ID} Substitution**: Skills can access current session ID
  - **Usage**: `${CLAUDE_SESSION_ID}` in skill content is replaced with actual session ID
  - **Impact**: Session-aware logging, tracking, and state management
  - **Affected**: `leyline:usage-logging`, session-scoped hooks
  - **Use Case**: Correlate logs across session, track skill usage per session

- ✅ **External Editor in AskUserQuestion**: Ctrl+G support in "Other" input field
  - **Impact**: Compose complex responses in external editor

- ✅ **Session URL Attribution**: Commits/PRs from web sessions include attribution
  - **Impact**: Traceability for web-created changes

**Bug Fixes**:
- ✅ **Long Session Parallel Tool Fix**: Fixed API error about orphan tool_result blocks
  - **Previous Bug**: Long sessions with parallel tool calls could fail
  - **Impact**: More reliable long-running sessions with heavy tool use

- Fixed MCP server reconnection hanging when cached connection promise never resolves
- Fixed Ctrl+Z suspend not working in Kitty keyboard protocol terminals

**Notes**:
- PreToolUse additionalContext enables powerful pre-execution context injection patterns
- Session ID substitution enables better observability and session-scoped behavior
- The plansDirectory setting enables enterprise planning workflows

### [Claude Code 2.1.7](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#217) (January 2026)

**New Features**:
- ✅ **showTurnDuration Setting**: Hide turn duration messages (e.g., "Cooked for 1m 6s")
  - **Impact**: Cleaner output for users who don't want timing info
  - **Configuration**: Set in `/config` or `settings.json`

- ✅ **Permission Prompt Feedback**: Provide feedback when accepting permission prompts
  - **Impact**: Better telemetry and UX improvements

- ✅ **Task Notification Agent Response**: Inline display of agent's final response in task notifications
  - **Impact**: See results without reading full transcript

- ✅ **MCP Tool Search Auto Mode (Default)**: Automatically defers MCP tools when descriptions exceed 10% of context
  - **Feature**: Tools discovered via MCPSearch instead of loaded upfront
  - **Token Savings**: ~85% reduction in MCP tool overhead
  - **Threshold**: 10% of context window (configurable via `ENABLE_TOOL_SEARCH=auto:N`)
  - **Model Requirements**: Sonnet 4+ or Opus 4+ (Haiku not supported)
  - **Disable**: Add `MCPSearch` to `disallowedTools` in settings
  - **Ecosystem Impact**: MCP-related skills should account for deferred tool loading
  - **Affected**: `conserve:mcp-code-execution` skill may need on-demand tool discovery patterns

**Security Fixes**:
- 🔒 **Wildcard Permission Compound Command Fix**: Critical security fix
  - **Previous Bug**: Wildcards like `Bash(npm *)` could match compound commands with shell operators (`;`, `&&`, `||`, `|`)
  - **Example Exploit**: `Bash(npm *)` would match `npm install && rm -rf /`
  - **Now Fixed**: Wildcards only match single commands, not compound chains
  - **Related Issues**: [#4956](https://github.com/anthropics/claude-code/issues/4956), [#13371](https://github.com/anthropics/claude-code/issues/13371)
  - **Action Required**: None - fix is automatic, existing wildcard patterns are now secure
  - **Ecosystem Impact**: No changes needed to documented wildcard patterns

**Bug Fixes**:
- ✅ **Context Window Blocking Limit Fix**: Critical for MECW calculations
  - **Previous Bug**: Blocking limit used full context window size
  - **Now Fixed**: Uses *effective* context window (reserves space for max output tokens)
  - **MECW Impact**: The effective context is smaller than total; 50% rule now applies to effective context
  - **Affected**: `conserve:context-optimization` MECW principles documentation
  - **Action Required**: Note distinction between total and effective context in monitoring

- Fixed false "file modified" errors on Windows with cloud sync/antivirus/Git
- Fixed orphaned tool_result errors when sibling tools fail during streaming
- Fixed spinner flash when running local slash commands
- Fixed terminal title animation jitter
- Fixed plugins with git submodules not fully initialized
- Fixed Bash commands failing on Windows with escape sequences in temp paths

**Performance Improvements**:
- ✅ **Improved Typing Responsiveness**: Reduced memory allocation overhead in terminal rendering

**URL Changes**:
- OAuth and API Console URLs changed from `console.anthropic.com` to `platform.claude.com`

**Notes**:
- The wildcard permission fix closes a significant security vector without breaking valid patterns
- MCP tool search auto mode fundamentally changes how many-tool workflows behave
- The context window blocking fix means effective context is smaller than total context
- Consider these changes when designing workflows that approach context limits

### [Claude Code 2.1.6](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#216) (January 2026)

**New Features**:
- ✅ **Nested Skills Discovery**: Skills from nested `.claude/skills` directories auto-discovered
  - **Use Case**: Monorepos with package-specific skills
  - **Example**: `packages/frontend/.claude/skills/` discovered when editing frontend files
  - **Impact**: Plugin structure can now support subdirectory-specific skills
  - **Action Required**: None - automatic behavior for monorepo setups

- ✅ **Status Line Context Percentage**: `context_window.used_percentage` and `remaining_percentage` in status line input
  - **Extends**: 2.1.0 context window fields now accessible via status line
  - **Impact**: Easier MECW monitoring without running `/context`
  - **Affected**: `conserve:context-optimization` can reference these fields for real-time monitoring

- ✅ **Config Search**: Search functionality in `/config` command
  - **Impact**: Quickly filter settings by name
  - **Usage**: Type to search while in `/config`

- ✅ **Doctor Updates Section**: `/doctor` shows auto-update channel and available npm versions
  - **Impact**: Better visibility into update status (stable/latest channels)

- ✅ **Stats Date Filtering**: Date range filtering in `/stats` command
  - **Usage**: Press `r` to cycle between Last 7 days, Last 30 days, and All time
  - **Impact**: More granular usage analytics

**Breaking Changes**:
- ⚠️ **MCP @-mention Removal**: Use `/mcp enable <name>` instead of @-mentioning servers
  - **Previous**: @-mention MCP servers to enable/disable them
  - **Now**: Must use `/mcp enable <name>` or `/mcp disable <name>` commands
  - **Ecosystem Impact**: None - no references found in codebase

**Bug Fixes**:
- Fixed error display when editor fails during Ctrl+G
- Fixed text styling (bold, colors) getting progressively misaligned in multi-line responses
- Fixed feedback panel closing unexpectedly when typing 'n' in the description field
- Fixed rate limit options menu incorrectly auto-opening when resuming a previous session
- Fixed numpad keys outputting escape sequences in Kitty keyboard protocol terminals
- Fixed Option+Return not inserting newlines in Kitty keyboard protocol terminals
- Fixed corrupted config backup files accumulating in the home directory

**UX Improvements**:
- Improved external CLAUDE.md imports approval dialog to show which files are being imported
- Improved `/tasks` dialog to go directly to task details when only one background task running
- Improved `@` autocomplete with icons for different suggestion types
- Changed task notification display to cap at 3 lines with overflow summary
- Changed terminal title to "Claude Code" on startup

**Notes**:
- Nested skills discovery enables better monorepo support without plugin structure changes
- Status line context fields provide real-time MECW monitoring
- MCP @-mention removal is a minor breaking change with no ecosystem impact

### [Claude Code 2.1.5](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#215) (January 2026)

**New Environment Variables**:
- ✅ **`CLAUDE_CODE_TMPDIR`**: Override the temp directory for internal temp files
  - **Scope**: Controls where Claude Code stores internal temporary files
  - **Use Cases**: Termux (Android), restricted `/tmp` environments, custom temp directory requirements
  - **Default**: Falls back to system temp directory (`/tmp` on Linux/macOS)
  - **Example**: `CLAUDE_CODE_TMPDIR=/data/data/com.termux/files/usr/tmp claude "task"`
  - **Plugin Impact**: Plugins should use `${CLAUDE_CODE_TMPDIR:-/tmp}` pattern for temp files

**Notes**:
- Addresses [Issue #15637](https://github.com/anthropics/claude-code/issues/15637) - Termux compatibility
- Addresses [Issue #15700](https://github.com/anthropics/claude-code/issues/15700) - Background task temp directory
- Minor release focused on platform compatibility

### [Claude Code 2.1.4](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#214) (January 2026)

**New Environment Variables**:
- ✅ **`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`**: Disable all background task functionality
  - **Scope**: Disables auto-backgrounding and `Ctrl+B` shortcut
  - **Use Cases**: CI/CD pipelines, debugging, environments where detached processes are problematic
  - **Does NOT affect**: Python subprocess spawning, asyncio tasks in hooks, general async processing
  - **Example**: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1 claude "run tests"`

**Bug Fixes**:
- ✅ **OAuth Token Refresh**: Fixed "Help improve Claude" setting fetch
  - Automatically refreshes OAuth token and retries when stale
  - **Impact**: Better reliability for user preference settings

**Notes**:
- Minor release focused on CI/CD compatibility and OAuth reliability
- Background task disable is useful for deterministic test environments

### [Claude Code 2.1.3](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#213) (January 2026)

**Architectural Changes**:
- ✅ **Merged Slash Commands and Skills**: Unified mental model with no behavior change
  - Skills now appear in `/` menu alongside commands
  - Explicit invocation via `/skill-name` now available
  - Auto-discovery still works as before
  - **Impact**: Simplified extensibility model - skills and commands are conceptually unified
  - **Action Required**: None - existing plugin.json structure remains valid

**Bug Fixes**:
- ✅ **Fixed Subagent Model Selection During Compaction**: Critical fix for long conversations
  - **Previous Bug**: Subagents could use wrong model when parent context was compacted
  - **Now Fixed**: Model specified in agent frontmatter (`model: sonnet/haiku/opus`) respected
  - **Impact**: All 29 ecosystem agents with `model:` specification now work correctly during compaction
  - **Action Required**: None - agents already specify models

- ✅ **Fixed Web Search in Subagents**: Web search now uses correct model
  - **Previous Bug**: Web search in subagents used incorrect model
  - **Now Fixed**: Web search respects agent's model specification
  - **Impact**: Agents using web search get consistent results

- ✅ **Fixed Plan File Persistence**: Fresh plan after `/clear`
  - **Previous Bug**: Plan files persisted across `/clear` commands
  - **Now Fixed**: Fresh plan file created after clearing conversations
  - **Impact**: Cleaner session restarts

- ✅ **Fixed Skill Duplicate Detection on ExFAT**: Large inode handling
  - **Previous Bug**: False duplicate detection on filesystems with large inodes
  - **Now Fixed**: 64-bit precision for inode values
  - **Impact**: Better compatibility with ExFAT filesystems

- ✅ **Fixed Trust Dialog from Home Directory**: Hooks now work correctly
  - **Previous Bug**: Trust dialog acceptance from home directory didn't enable hooks
  - **Now Fixed**: Trust-requiring features like hooks work during session
  - **Impact**: More reliable hook execution

**Performance Improvements**:
- ✅ **Hook Timeout Extended**: 60 seconds → 10 minutes
  - **Impact**: Long-running hooks now viable (CI/CD, complex validation, external APIs)
  - **Affected**: `abstract:hook-authoring` guidance updated
  - **Best Practice**: Aim for < 30s for typical hooks; use extended time only when needed

- ✅ **Terminal Rendering Stability**: Prevents cursor corruption
  - **Impact**: Better terminal experience with uncontrolled writes

**New Features**:
- ✅ **Unreachable Permission Rule Detection**: New diagnostic in `/doctor`
  - **Feature**: Warns about permission rules that can never match
  - **Impact**: Easier debugging of permission configurations
  - **Usage**: Run `/doctor` to check for unreachable rules
  - **Output**: Shows source of each rule and actionable fix guidance

- ✅ **Release Channel Toggle**: Choose `stable` or `latest` in `/config`
  - **Feature**: Switch between release channels
  - **Impact**: More control over update timing

**User Experience**:
- ✅ **Improved Slash Command Suggestions**: Long descriptions truncated to 2 lines
  - **Impact**: Better readability in `/` menu

**Notes**:
- This release consolidates skills and commands conceptually while maintaining backward compatibility
- The subagent model fixes are critical for long-running sessions with model escalation
- Hook timeout increase enables more sophisticated automation workflows
- Run `/doctor` periodically to check permission rule health

### [Claude Code 2.1.0](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#210) (January 2026)

**Architectural Changes**:
- ✅ **Automatic Skill Hot-Reload**: Skills created or modified in `~/.claude/skills` or `.claude/skills` now immediately available
  - **Impact**: No session restart needed when developing or updating skills
  - **Affected**: `abstract:skill-authoring` - Development workflow significantly faster
  - **Action Required**: None - automatic behavior

- ✅ **Forked Sub-Agent Context**: Support for `context: fork` in skill frontmatter
  - **Feature**: Skills/commands can run in isolated forked context
  - **Impact**: Prevents context pollution from exploratory operations
  - **Affected**: All agents with multi-perspective analysis patterns
  - **Documentation**: See session forking patterns

- ✅ **Enhanced Hooks Support**: Hooks now available in agent, skill, and slash command frontmatter
  - **Impact**: Fine-grained lifecycle control for plugin components
  - **Affected**: `abstract:hook-authoring` - New hook attachment points
  - **Action Required**: Review hook placement options for existing plugins

**New Features**:
- ✅ **Language Configuration**: New `language` setting to customize Claude's response language
  - **Impact**: Better internationalization support
  - **Usage**: Set in `/config` or `settings.json`

- ✅ **Wildcard Bash Permissions**: Support for `Bash(npm *)` pattern in permissions
  - **Impact**: Simpler permission rules for command families
  - **Affected**: `abstract:hook-authoring` security patterns

- ✅ **Agent Disabling Syntax**: Disable specific agents using `Task(AgentName)` in permissions
  - **Impact**: More granular control over agent invocation
  - **Documentation**: Permission configuration reference

- ✅ **Plugin Hook Support**: Prompt and agent hook types now available from plugins
  - **Impact**: Plugins can define hooks that run during prompt/agent lifecycle
  - **Affected**: All plugins with custom workflows

- ✅ **Context Window Fields**: New `context_window.used_percentage` and `remaining_percentage`
  - **Impact**: Precise context monitoring for MECW compliance
  - **Affected**: `conserve:context-optimization` - Better metrics available

**Performance Improvements**:
- ✅ **Subagent Model Inheritance**: Subagents now properly inherit parent's model by default
  - **Previous Bug**: Model selection could be inconsistent
  - **Now Fixed**: Predictable model behavior across agent hierarchies
  - **Affected**: All 29 ecosystem agents with model specifications

- ✅ **Skills Progress Display**: Skills now show progress while executing
  - **Impact**: Better UX during long-running skill operations

- ✅ **Improved Skill Suggestions**: Prioritizes recent and frequent usage
  - **Impact**: Faster access to commonly-used skills

**Security Fixes**:
- 🔒 **Shell Line Continuation Fix**: Resolved vulnerability where continuation could bypass blocked commands
  - **Security Impact**: Prevents command injection via multi-line tricks
  - **Action Required**: None - automatic protection

- 🔒 **Command Injection Fix**: Fixed vulnerability in bash command processing
  - **Security Impact**: Closes potential injection vector
  - **Action Required**: None - automatic protection

**Bug Fixes**:
- Fixed "File has been unexpectedly modified" false errors with file watchers
- Fixed rate limit warning appearing at low usage after weekly reset
- Fixed `mcp list` and `mcp get` commands leaving orphaned MCP server processes
- Fixed memory leak where tree-sitter parse trees weren't being freed
- Fixed binary files being included in memory with `@include` directives

**User Experience**:
- ✅ **Shift+Enter Default Support**: Works out of box in iTerm2, WezTerm, Ghostty, Kitty
  - **Impact**: No terminal configuration needed for multiline input
- ✅ **Vim Motion Improvements**: Added `;`, `,` for motion repetition; `y` for yank; text objects
  - **Impact**: Better vim-mode editing experience
- ✅ **Skills in Slash Menu**: Skills from `/skills/` directories visible in `/` menu by default
  - **Impact**: Improved skill discoverability

**Notes**:
- This is a major release with significant skill/agent infrastructure improvements
- Hot-reload dramatically improves plugin development workflow
- Forked context enables safer exploratory operations
- Security fixes close potential command injection vectors
- Run `/context` to see new percentage fields for MECW monitoring

### [Claude Code 2.0.74](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2074) (December 2025)

**New Features**:
- ⚠️ **LSP (Language Server Protocol) Tool**: Native code intelligence integration (**EXPERIMENTAL - See [Issue #72](https://github.com/athola/claude-night-market/issues/72)**)

  > **⚠️ CURRENT STATUS (v2.0.74-2.0.76):** LSP support is experimental with known bugs (race conditions, plugin loading failures, "No LSP server available" errors). **Recommend using Grep (ripgrep) as primary method** until LSP stabilizes. See "LSP Integration Patterns" section below for details.

  - **Capabilities**: Go-to-definition, find references, hover documentation
  - **Performance**: 50ms semantic searches (when working) vs. 100-500ms grep searches (reliable)
  - **Impact**: Semantic code navigation when functional, but unstable in current versions
  - **Affected Plugins**:
    - **pensive**: Enhanced code review with semantic analysis, impact detection, unused code identification
    - **sanctum**: Documentation updates with reference finding, API completeness verification
    - **conservation**: LSP queries more token-efficient than broad grep searches
    - **abstract**: Plugin developers should document LSP usage patterns
  - **Language Support**: TypeScript, Rust, Python, Go, Java, Kotlin, C/C++, PHP, Ruby, C#, PowerShell, HTML/CSS, LaTeX, BSL
  - **Activation**: Set `ENABLE_LSP_TOOL=1` environment variable
  - **Documentation**: See "LSP Integration Patterns" section below
  - **Resources**:
    - [cclsp MCP server](https://github.com/ktnyt/cclsp) - MCP integration for LSP
    - [Official LSP Plugins](https://github.com/anthropics/claude-plugins-official) - Anthropic's official LSP plugins (pyright-lsp, typescript-lsp, rust-analyzer-lsp, etc.)
  - **Examples**:
    ```bash
    # Enable LSP for session (from within a code project)
    cd /path/to/your/project
    ENABLE_LSP_TOOL=1 claude
    # Then: "Find all references to processData function"

    # Code review with semantic understanding
    ENABLE_LSP_TOOL=1 claude "/pensive:code-review --use-lsp src/"

    # Documentation update with API verification
    ENABLE_LSP_TOOL=1 claude "/sanctum:update-docs --verify-references"
    ```

- ✅ **Terminal Setup Support**: Extended `/terminal-setup` compatibility
  - **Added Support**: Kitty, Alacritty, Zed, Warp terminals
  - **Impact**: Improved cross-terminal compatibility
  - **Affected**: Users on modern terminal emulators
  - **Documentation**: Run `/terminal-setup` to configure

**User Experience**:
- ✅ **Improved /context Visualization**: Skills/agents grouped by source plugin
  - **Display**: Shows plugin organization, slash commands, sorted token counts
  - **Benefits**:
    - Easier plugin discovery and context understanding
    - Better visibility into which plugins consume context
    - Improved MECW monitoring and optimization
  - **Affected**:
    - **conservation**: Update context optimization guidance
    - **abstract**: Plugin metadata more visible
  - **Documentation**: `conserve/skills/context-optimization/modules/mecw-principles.md`

- Added `ctrl+t` shortcut in `/theme` to toggle syntax highlighting on/off
- Added syntax highlighting info to theme picker
- Added guidance for macOS users when Alt shortcuts fail due to terminal configuration
- Improved macOS keyboard shortcuts to display 'opt' instead of 'alt'

**Security Fixes**:
- 🔒 **CRITICAL: Fixed skill allowed-tools enforcement**
  - **Previous Bug**: `allowed-tools` restrictions in skill frontmatter were NOT being applied
  - **Now Fixed**: Tool restrictions properly enforced for skills
  - **Security Impact**: Skills that assumed tool restrictions were actually exposing all tools
  - **Ecosystem Impact**: Currently no plugins use `allowed-tools` (verified via audit)
  - **Action Required**:
    - Plugin developers should review if any skills need tool restrictions
    - Consider using `allowed-tools` for security-sensitive skills
    - Distinguish between agent `tools:` (whitelist) and skill `allowed-tools:` (restrictions)
  - **Documentation**: See "Tool Restriction Patterns" section below
  - **Example**:
    ```yaml
    ---
    name: restricted-skill
    description: Skill that should not execute arbitrary code
    allowed-tools: [Read, Grep, Glob]  # Now properly enforced!
    ---
    ```
  - **Best Practices**:
    - Use `allowed-tools` for skills processing untrusted input
    - Restrict Bash/Write/Edit for read-only analysis skills
    - Document security assumptions in skill descriptions

**Bug Fixes**:
- Fixed visual bug in `/plugins discover` where list selection indicator showed while search box was focused
- Fixed a potential crash when syntax highlighting isn't initialized correctly
- Fixed Opus 4.5 tip incorrectly showing when user was already using Opus

**Notes**:
- LSP integration represents a paradigm shift from text-based to semantic code understanding
- `allowed-tools` fix closes a security gap - audit your skills if you assumed tool restrictions
- Improved /context visualization aids MECW compliance and plugin discoverability
- Terminal compatibility improvements benefit cross-platform development

### [Claude Code 2.0.73](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2073) (December 2025)

**New Features**:
- ✅ **Session Forking**: Custom session IDs with `--session-id` + `--fork-session` + (`--resume` | `--continue`)
  - Creates isolated session branches from existing conversations
  - Enables "what-if" exploration without affecting original session
  - Perfect for: parallel analysis, alternative approaches, subagent delegation
  - Affected: All workflow plugins (`sanctum`, `imbue`, `pensive`, `memory-palace`)
  - Use cases:
    - **sanctum**: Fork to explore alternative PR approaches or commit strategies
    - **imbue**: Fork for parallel evidence analysis and multiple review perspectives
    - **pensive**: Fork for multi-perspective code reviews (security, performance, maintainability)
    - **memory-palace**: Fork for exploratory knowledge intake and categorization strategies
  - Documentation: `plugins/abstract/docs/session-forking-patterns.md` (see below)
  - Example: `claude --fork-session --session-id "pr-alt-approach" --resume`

- ✅ **Plugin Discover Search**: Filter plugins by name, description, marketplace
  - Type to search while browsing plugin marketplace
  - Improves plugin discoverability
  - Affected: `leyline:update-all-plugins`, plugin metadata best practices
  - Impact: Plugin descriptions and metadata should be search-friendly
  - Recommendation: Use descriptive keywords in plugin.json description field

- ✅ **Image Viewing**: Clickable `[Image #N]` links open in default viewer
  - Quick preview of attached or generated images
  - Affected: `scry:media-composition`, `imbue:evidence-logging`
  - Impact: Easier review of visual assets and evidence artifacts
  - Complements GIF generation and media workflows

**User Experience**:
- Added alt-y yank-pop to cycle through kill ring history after ctrl-y yank
- Improved `/theme` command to open theme picker directly
- Improved theme picker UI
- Unified SearchBox component across resume session, permissions, and plugins screens

**Performance**:
- Fixed slow input history cycling
- Fixed race condition that could overwrite text after message submission

**VSCode Extension**:
- [VSCode] Added tab icon badges showing pending permissions (blue) and unread completions (orange)

**Notes**:
- Session forking enables workflow patterns similar to git branching for conversations
- Forked sessions inherit context but maintain independent history
- Built on Agent Client Protocol's session fork RFD
- See "Session Forking Patterns" section below for detailed usage examples

### [Claude Code 2.0.72](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2072) (December 2025)

**New Features**:
- ✅ **Claude in Chrome (Beta)**: Native browser control integration
  - Works with Chrome extension (https://claude.ai/chrome)
  - Direct browser control from Claude Code terminal
  - Console log reading, network monitoring, DOM inspection
  - GIF recording of browser interactions
  - Affected: `scry:browser-recording` - Complements Playwright workflows
  - Documentation: `scry/README.md`, `scry/skills/browser-recording/SKILL.md`

**User Experience**:
- Changed thinking toggle from `Tab` to `Alt+T` to avoid accidental triggers
- Added scannable QR code to mobile app tip
- Added loading indicator when resuming conversations
- Improved settings validation errors to be more prominent

**Performance**:
- Improved @ mention file suggestion speed (~3x faster in git repositories)
- Improved file suggestion performance in repos with `.ignore` or `.rgignore` files
- Reduced terminal flickering for better visual experience

**Bug Fixes**:
- Fixed `/context` command not respecting custom system prompts in non-interactive mode
- Fixed order of consecutive Ctrl+K lines when pasting with Ctrl+Y

**Notes**:
- Chrome integration requires Chrome extension installation (Pro/Team subscribers)
- Known issue: Chromium browsers (non-Chrome) on Linux may have connection issues
- Native Chrome control complements Playwright for different use cases:
  - **Native Chrome**: Interactive debugging, live testing, exploratory work
  - **Playwright**: Automated recording, headless execution, CI/CD, cross-browser

### [Claude Code 2.0.71](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2071) (December 2025)

**New Commands**:
- `/config toggle` - Enable/disable prompt suggestions
- `/settings` - Alias for `/config` command

**Bug Fixes**:
- ✅ **Bash Glob Patterns**: Permission rules now correctly allow shell glob patterns
  - Affected: All plugins using bash commands with `*.txt`, `*.png`, etc.
  - Impact: Removes false-positive permission rejections
  - Documentation: `abstract/skills/hook-authoring/modules/hook-types.md`
  - Documentation: `abstract/skills/hook-authoring/modules/security-patterns.md`

- ✅ **MCP Server Loading**: `.mcp.json` servers now load with `--dangerously-skip-permissions`
  - Affected: CI/CD workflows, automated testing
  - Impact: Enables fully automated MCP workflows
  - Documentation: `abstract/skills/hook-authoring/modules/hook-types.md`

- ✅ **@ File Reference**: Fixed cursor position triggering incorrect suggestions
  - Affected: File reference autocomplete
  - Impact: Better UX, fewer false suggestions

**Other Changes**:
- New syntax highlighting engine for native build
- Bedrock: `ANTHROPIC_BEDROCK_BASE_URL` environment variable respected

### [Claude Code 2.0.70](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2070) (December 2025)

**New Features**:
- **MCP Wildcard Permissions**: `mcp__server__*` syntax for bulk permissions
  - Documentation: `abstract/skills/hook-authoring/modules/hook-types.md`
- **Enter Key for Prompt Suggestions**: Improved suggestion UX
- **3x Memory Improvement**: Better handling of large conversations

**Enhancements**:
- **Improved Context Accuracy**: `current_usage` field enables precise percentage calculations
  - Affected: `conserve:context-optimization`
  - Documentation: `conserve/skills/context-optimization/modules/mecw-principles.md`

**Bug Fixes**:
- Thinking mode toggle in `/config` now persists correctly

### [Claude Code 2.0.65](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2065) (November 2025)

**New Features**:
- **Native Context Visibility**: Status line displays real-time context utilization
  - Affected: `conserve:context-optimization`
  - Documentation: `conserve/skills/context-optimization/modules/mecw-principles.md`

- **CLAUDE_CODE_SHELL Override**: Environment variable for shell detection
  - Affected: Hook execution in non-standard shell environments
  - Documentation: `abstract/skills/hook-authoring/modules/security-patterns.md`

## Plugin-Specific Compatibility

### Abstract Plugin

**Minimum Version**: 2.0.65+ (recommended 2.0.71+)

**Version-Specific Features**:
- Hook authoring documentation references 2.0.70+ wildcard permissions
- Hook authoring documentation includes 2.0.71+ glob pattern fixes
- Security patterns updated for 2.0.71+ glob validation

**Testing**: All hooks tested with 2.0.71+

### Conservation Plugin

**Minimum Version**: 2.0.65+ (recommended 2.0.74+)

**Version-Specific Features**:
- Context monitoring uses 2.0.65+ status line visibility
- Token tracking uses 2.0.70+ improved accuracy
- 2.0.74+ improved /context visualization
  - Skills/agents grouped by source plugin
  - Better visibility into context consumption
  - Sorted token counts for optimization
- 2.0.74+ LSP integration for token efficiency
  - ~90% token reduction for reference finding
  - Semantic queries vs. broad grep searches
  - Targeted reads vs. bulk file loading

**Recommendations**:
- Use 2.0.70+ for accurate context percentage calculations
- Use 2.0.74+ /context visualization for plugin-level optimization
- use LSP for token-efficient code navigation
- Native visibility replaces manual context estimation

### Sanctum Plugin

**Minimum Version**: 2.0.70+ (recommended 2.0.74+)

**Version-Specific Features**:
- CI/CD workflows benefit from 2.0.71+ MCP server loading fix
- Git operations use glob patterns fixed in 2.0.71+
- 2.0.74+ LSP integration for documentation workflows
  - Reference finding: Locate all usages of documented items
  - API completeness: Verify all public APIs are documented
  - Signature verification: Check docs match actual code
  - Cross-reference validation: validate doc links are accurate

**Recommendations**:
- Use 2.0.71+ for automated PR workflows with MCP
- Use 2.0.74+ with LSP for detailed documentation updates
- GitHub Actions integration requires 2.0.71+ for reliable MCP
- use LSP to validate documentation completeness and accuracy

### Leyline Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- MECW patterns reference 2.0.70+ context accuracy
- Error patterns benefit from improved context tracking

### Scry Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- Browser recording uses Playwright for automated workflows
- 2.0.72+ adds complementary native Chrome integration
- 2.0.73+ adds image viewing for generated media assets

**Recommendations**:
- Use 2.0.72+ Chrome integration for interactive debugging and live testing
- Use Playwright (scry:browser-recording) for automated recording, CI/CD, and cross-browser
- Both approaches can be combined: develop with Chrome, automate with Playwright
- Use 2.0.73+ image viewing to preview generated GIFs and screenshots

### Imbue Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- 2.0.73+ session forking enables parallel evidence analysis
- 2.0.73+ image viewing supports visual evidence artifacts

**Recommendations**:
- Use 2.0.73+ session forking for multi-perspective reviews
- Fork sessions to analyze different evidence paths without context pollution

### Pensive Plugin

**Minimum Version**: 2.0.65+ (recommended 2.0.74+)

**Version-Specific Features**:
- 2.0.73+ session forking enables multi-perspective code reviews
- 2.0.74+ LSP integration for semantic code analysis
  - Impact analysis: Find all references to changed functions
  - Unused code detection: Identify unreferenced exports
  - API consistency: Verify usage patterns
  - Type safety: Validate type usage across codebase

**Recommendations**:
- Use 2.0.74+ with `ENABLE_LSP_TOOL=1` for semantic code review
- Fork sessions for specialized reviews (security, performance, maintainability)
- Combine LSP-powered analysis with traditional pattern matching
- use LSP for accurate impact assessments during refactoring reviews

### Memory-Palace Plugin

**Minimum Version**: 2.0.65+

**Version-Specific Features**:
- 2.0.73+ session forking enables exploratory knowledge intake

**Recommendations**:
- Fork sessions to experiment with different categorization strategies
- Test alternative tagging approaches in forked sessions
