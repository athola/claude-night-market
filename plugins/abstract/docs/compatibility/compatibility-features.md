# Claude Code Compatibility Features

Feature timeline and version-specific capabilities.

> **See Also**: [Reference](compatibility-reference.md) | [Patterns](compatibility-patterns.md) | [Issues](compatibility-issues.md)

## Feature Timeline

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
