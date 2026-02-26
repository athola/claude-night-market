# Claude Code Compatibility Features (2025 Archive)

Feature timeline for Claude Code versions released in November-December 2025.

> **See Also**: [Current Features (2026)](compatibility-features.md) | [Reference](compatibility-reference.md) | [Patterns](compatibility-patterns.md) | [Issues](compatibility-issues.md)

## Feature Timeline (2025)

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
