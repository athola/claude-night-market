# Claude Code Compatibility Features: February 2026 (Late)

Feature timeline for Claude Code versions 2.1.21 through 2.1.34,
released in February 2026.

> **See Also**:
> [Features Index](compatibility-features.md) |
> [March 2026](compatibility-features-march2026-recent.md) |
> [February 2026 Early](compatibility-features-feb2026-early.md) |
> [January 2026](compatibility-features-jan2026.md) |
> [Plugin Compatibility](compatibility-features-plugin-compat.md) |
> [Reference](compatibility-reference.md) |
> [2025 Archive](compatibility-features-2025.md)

## Feature Timeline

### Claude Code 2.1.38 (February 2026)

**Security Fixes**:
- 🔒 **Heredoc Delimiter Parsing Hardened**: Improved delimiter parsing to prevent command smuggling via crafted heredoc delimiters
  - **Previous Risk**: Specially crafted heredoc delimiters could potentially inject commands during bash tool execution
  - **Now Fixed**: Delimiter parsing validates and sanitizes heredoc boundaries before execution
  - **Security Impact**: Closes a potential command injection vector in bash tool heredoc handling
  - **Affected**: Ecosystem files using heredoc patterns for commit messages, PR bodies, and multi-line output (sanctum rules, commit-messages skill, pr-prep skill, do-issue command) — all benefit automatically
  - **Action Required**: None — passive security improvement, no pattern changes needed
  - **Note**: The `git commit -m "$(cat <<'EOF' ... EOF)"` pattern recommended by sanctum remains safe and is now more robustly handled

- 🔒 **Sandbox Blocks Writes to `.claude/skills` Directory**: Skills directory is now read-only when sandbox mode is active
  - **Previous Behavior**: Sandbox mode allowed writes to `.claude/skills/`, enabling runtime skill creation/modification
  - **Now Blocked**: Write, Edit, and file creation operations targeting `.claude/skills/` are rejected in sandbox mode
  - **Security Impact**: Prevents runtime injection of malicious skills that could alter Claude's behavior
  - **Affected**: `abstract:skill-authoring` — updated with sandbox write restriction note
  - **Affected**: `abstract:create-skill` — skill creation requires non-sandbox mode or `dangerouslyDisableSandbox`
  - **Action Required**: Workflows that dynamically create skills must either disable sandbox or use pre-deployment skill installation
  - **Note**: Skills installed via plugin marketplace are unaffected — this only blocks runtime file writes to the skills directory
  - **Clarification**: This blocks writes to `.claude/skills/` within the sandbox path (project-level). User-level `~/.claude/skills/logs/` writes (e.g., skill execution logging by abstract's PostToolUse hook) are outside the sandbox boundary and remain unaffected

**Bug Fixes**:
- ✅ **VS Code Terminal Scroll-to-Top Regression Fixed**: VS Code extension terminal no longer scrolls to top unexpectedly
  - **Previous Bug** (2.1.37): Terminal would jump to the top of output history during interaction, losing the user's scroll position
  - **Now Fixed**: Terminal scroll position maintained correctly in VS Code extension
  - **Impact**: Passive UX fix — no ecosystem changes needed
  - **Action Required**: None

- ✅ **Tab Key Autocomplete Restored**: Tab key now correctly autocompletes instead of queueing slash commands
  - **Previous Bug**: Pressing Tab would queue a slash command instead of triggering autocomplete, disrupting the expected interaction flow
  - **Now Fixed**: Tab key behavior restored to autocomplete (consistent with standard terminal behavior)
  - **Impact**: Passive UX fix — skills and commands invoked via `/` menu are unaffected
  - **Action Required**: None

- ✅ **Bash Permission Matching for Env Variable Wrappers**: Permission rules now correctly match commands prefixed with environment variable assignments
  - **Previous Bug**: Commands like `NODE_ENV=production npm test` or `FORCE_COLOR=1 jest` would not match permission rules expecting `npm test` or `jest` — resulting in unexpected permission prompts or denials ([#15292](https://github.com/anthropics/claude-code/issues/15292), [#15777](https://github.com/anthropics/claude-code/issues/15777))
  - **Now Fixed**: Environment variable prefixes (e.g., `KEY=value command`) are stripped during permission matching, so the base command matches existing rules
  - **Impact**: Permission rules using wildcard patterns like `Bash(npm *)` or `Bash(jest *)` now correctly match env-prefixed invocations
  - **Affected**: `abstract:hook-authoring` — updated with env wrapper matching note
  - **Affected**: `hookify:writing-rules` — rule patterns benefit automatically (no changes needed)
  - **Action Required**: None — existing permission rules now work correctly for a broader set of command invocations

- ✅ **Text Between Tool Uses Preserved (Non-Streaming)**: Text output between consecutive tool calls no longer disappears
  - **Previous Bug**: When not using streaming mode (e.g., SDK integrations, `--output-format json`), text generated between tool uses was silently dropped
  - **Now Fixed**: All inter-tool text is correctly preserved and displayed
  - **Impact**: SDK integrations and non-streaming pipelines now receive complete output
  - **Action Required**: None — passive fix, no workarounds existed

- ✅ **VS Code Duplicate Sessions on Resume Fixed**: Resuming sessions in VS Code extension no longer creates duplicate session entries
  - **Previous Bug**: Each resume in VS Code could create a duplicate session entry, cluttering the session list
  - **Now Fixed**: Resume correctly reuses the existing session without duplication
  - **Impact**: Cleaner session management in VS Code extension
  - **Affected**: `sanctum:session-management` — updated troubleshooting section with version note
  - **Action Required**: None

**Notes**:
- The heredoc delimiter hardening is a defense-in-depth security fix — the recommended `<<'EOF'` quoting pattern was already safe, but edge cases with crafted delimiters are now properly handled
- Sandbox `.claude/skills` write blocking is a significant security boundary — any plugin workflow that generates skills at runtime needs to account for this
- The env variable wrapper permission fix resolves a common friction point for CI/CD and test workflows that set environment variables inline
- Recommended version bumped to 2.1.38+ due to the heredoc security fix and sandbox hardening

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
- ✅ **Claude Opus 4.6**: New flagship model with 1M context (GA), 128K max output, adaptive thinking with effort controls
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


> **Next**: See [January 2026](compatibility-features-jan2026.md) for versions 2.1.0-2.1.18.
