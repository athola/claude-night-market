# Claude Code Compatibility Reference

This document tracks compatibility between the claude-night-market plugin ecosystem and Claude Code versions, documenting version-specific features and fixes that affect plugin functionality.

## Version Support Matrix

| Claude Code Version | Ecosystem Version | Status | Notes |
|---------------------|-------------------|--------|-------|
| 2.0.74+ | 1.1.1+ | ✅ Recommended | LSP tool, allowed-tools fix, improved /context |
| 2.0.73+ | 1.1.0+ | ✅ Supported | Session forking, plugin discovery, image viewing |
| 2.0.72+ | 1.1.0+ | ✅ Supported | Chrome integration, performance improvements |
| 2.0.71+ | 1.1.0+ | ✅ Supported | Glob patterns, MCP loading fixes |
| 2.0.70+ | 1.0.0+ | ✅ Supported | Wildcard permissions, context accuracy |
| 2.0.65+ | 1.0.0+ | ✅ Supported | Status line visibility, CLAUDE_CODE_SHELL |
| < 2.0.65 | 1.0.0+ | ⚠️ Limited | Missing modern features |

## Feature Timeline

### Claude Code 2.0.74 (December 2024)

**New Features**:
- ✅ **LSP (Language Server Protocol) Tool**: Native code intelligence integration
  - **Capabilities**: Go-to-definition, find references, hover documentation
  - **Performance**: 50ms semantic searches vs. 45s grep searches
  - **Impact**: Fundamentally changes code navigation from syntactic to semantic
  - **Affected Plugins**:
    - **pensive**: Enhanced code review with semantic analysis, impact detection, unused code identification
    - **sanctum**: Documentation updates with reference finding, API completeness verification
    - **conservation**: LSP queries more token-efficient than broad grep searches
    - **abstract**: Plugin developers should document LSP usage patterns
  - **Language Support**: TypeScript, Rust, Python, Go, Java, Kotlin, C/C++, PHP, Ruby, C#, PowerShell, HTML/CSS, LaTeX, BSL
  - **Activation**: Set `ENABLE_LSP_TOOLS=1` environment variable
  - **Documentation**: See "LSP Integration Patterns" section below
  - **Resources**:
    - [cclsp MCP server](https://github.com/ktnyt/cclsp) - MCP integration for LSP
    - [Claude Code LSPs](https://github.com/Piebald-AI/claude-code-lsps) - Plugin marketplace with LSP servers
  - **Examples**:
    ```bash
    # Enable LSP for session (from within a code project)
    cd /path/to/your/project
    ENABLE_LSP_TOOLS=1 claude
    # Then: "Find all references to processData function"

    # Code review with semantic understanding
    ENABLE_LSP_TOOLS=1 claude "/pensive:code-review --use-lsp src/"

    # Documentation update with API verification
    ENABLE_LSP_TOOLS=1 claude "/sanctum:update-docs --verify-references"
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

### Claude Code 2.0.73 (December 2024)

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

### Claude Code 2.0.72 (December 2024)

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

### Claude Code 2.0.71 (December 2024)

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

### Claude Code 2.0.70 (December 2024)

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

### Claude Code 2.0.65 (November 2024)

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
- Use 2.0.74+ with `ENABLE_LSP_TOOLS=1` for semantic code review
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

## Breaking Changes

### None Currently

The ecosystem maintains backward compatibility with Claude Code 2.0.65+. All version-specific features are progressive enhancements.

## Migration Guides

### Upgrading to 2.0.71 from 2.0.70

**Actions Required**: None (fully backward compatible)

**Recommended Updates**:

1. **Remove Glob Pattern Workarounds**:
   ```python
   # BEFORE 2.0.71 - Remove these workarounds
   async def on_permission_request(self, tool_name: str, tool_input: dict) -> str:
       if tool_name == "Bash" and re.match(r'^ls\s+\*\.\w+$', command):
           return "allow"  # No longer needed
   ```

2. **Simplify MCP CI/CD**:
   ```yaml
   # BEFORE 2.0.71 - Manual trust step
   - run: claude --trust-mcp-servers
   - run: claude --dangerously-skip-permissions "task"

   # AFTER 2.0.71 - Direct execution
   - run: claude --dangerously-skip-permissions "task"
   ```

3. **Review Hook Validation**:
   - validate hooks don't block legitimate glob patterns
   - Update dangerous pattern lists to focus on actual risks
   - See: `abstract/skills/hook-authoring/modules/security-patterns.md`

### Upgrading to 2.0.70 from 2.0.65

**Actions Required**: None (fully backward compatible)

**Recommended Updates**:
1. Adopt MCP wildcard permissions if using multiple MCP servers
2. Update context monitoring to use improved accuracy
3. Remove manual context estimation code

## Known Issues

### Version-Specific Bugs

| Version | Issue | Workaround | Fixed In |
|---------|-------|------------|----------|
| < 2.0.71 | Glob patterns incorrectly rejected | Use permission hooks | 2.0.71 |
| < 2.0.71 | MCP servers don't load with --dangerously-skip-permissions | Manual trust step | 2.0.71 |
| < 2.0.70 | /config thinking mode doesn't persist | Manual reset | 2.0.70 |

## Testing Compatibility

### Verification Checklist

Run these tests to verify compatibility:

```bash
# 1. Test hook execution
claude --version
# Should be 2.0.71+

# 2. Test glob patterns in bash
# Create test files
touch test1.txt test2.txt

# Run glob command (should work without permission dialog)
claude "List all .txt files in current directory"
# Should execute: ls *.txt

# 3. Test MCP server loading (if applicable)
# Create .mcp.json in project
# Run with --dangerously-skip-permissions
claude --dangerously-skip-permissions "Check MCP servers available"

# 4. Test context monitoring
claude "Show context usage"
# Should display accurate percentage

# Cleanup
rm test1.txt test2.txt
```

### Automated Testing

```bash
# Run plugin test suite
cd plugins/abstract
python -m pytest tests/ -v

# Validate all plugins
python scripts/validate_plugins.py --check-compatibility
```

## Reporting Compatibility Issues

If you encounter compatibility problems:

1. **Check this document** for known issues and workarounds
2. **Verify Claude Code version**: `claude --version`
3. **Test with latest version**: Update to 2.0.71+
4. **Report issues** with:
   - Claude Code version
   - Plugin name and version
   - Minimal reproduction steps
   - Error messages or unexpected behavior

**Issue Template**:
```markdown
**Environment**:
- Claude Code: X.Y.Z
- Plugin: name@version
- OS: platform

**Description**:
[What went wrong]

**Expected Behavior**:
[What should happen]

**Reproduction Steps**:
1. ...
2. ...

**Error Output**:
```
[paste error]
```
```

## Future Compatibility

### Upcoming Features

Monitor these Claude Code developments that may affect plugins:

- **Agent SDK Enhancements**: New hook types and callbacks
- **MCP Protocol Updates**: Protocol version changes
- **Permission System Evolution**: New permission patterns
- **Context Window Changes**: Larger context windows, new monitoring

### Deprecation Warnings

**None Currently**: All documented features remain supported.

## Session Forking Patterns (2.0.73+)

### Overview

Session forking creates isolated conversation branches from existing sessions, enabling exploration of alternative approaches without affecting the original conversation history.

**Key Concept**: Like git branching for conversations - fork, explore, and optionally merge insights back.

### Command Syntax

```bash
# Fork from current/resumed session with custom ID
claude --fork-session --session-id "custom-fork-id" --resume

# Fork from specific session
claude --fork-session --session-id "security-review" --resume <session-id>

# Fork and continue (starts immediately)
claude --fork-session --session-id "experiment" --continue
```

### When to Fork vs. Resume vs. Continue

| Scenario | Command | Reason |
|----------|---------|--------|
| Explore alternative approach | `--fork-session` | Keep original session intact |
| Parallel analysis | `--fork-session` | Analyze from different perspectives |
| Subagent delegation | `--fork-session` | Inherit context, independent work |
| Generate multiple outputs | `--fork-session` | Create variants without conflicts |
| Simple continuation | `--resume` | Just pick up where you left off |
| Error recovery | `--continue` | Restart after interruption |

### Plugin-Specific Patterns

#### Sanctum: Git Workflow Forking

**Use Case**: Explore alternative PR approaches

```bash
# Original session: Working on feature
claude "Help me implement feature X"

# Fork to explore alternative implementation
claude --fork-session --session-id "feature-x-alt-approach" --resume

# In fork: Try different architecture
> "Let's try a functional approach instead of OOP"

# Fork for different commit strategy
claude --fork-session --session-id "feature-x-atomic-commits" --resume
> "Break this into atomic commits with conventional commit messages"

# Compare results and choose best approach
```

**Benefits**:
- Test multiple refactoring strategies
- Generate alternative PR descriptions
- Explore different commit organization patterns
- Compare implementation trade-offs side-by-side

#### Imbue: Parallel Evidence Analysis

**Use Case**: Multi-perspective review

```bash
# Original session: Evidence collection
claude "Analyze this codebase for technical debt"

# Fork for security perspective
claude --fork-session --session-id "security-analysis" --resume
> "Review the same codebase from a security perspective"

# Fork for performance perspective
claude --fork-session --session-id "performance-analysis" --resume
> "Review the same codebase from a performance perspective"

# Fork for maintainability perspective
claude --fork-session --session-id "maintainability-analysis" --resume
> "Review the same codebase from a maintainability perspective"

# Consolidate findings from all forks
```

**Benefits**:
- Parallel specialized reviews
- Independent evidence logging
- No cross-contamination of perspectives
- detailed multi-angle analysis

#### Pensive: Multi-Perspective Code Reviews

**Use Case**: Specialized review angles

```bash
# Original session: Code review request
claude "/pensive:code-review src/"

# Fork for security audit
claude --fork-session --session-id "security-audit" --resume
> "Focus exclusively on security vulnerabilities and auth issues"

# Fork for architecture review
claude --fork-session --session-id "architecture-review" --resume
> "Focus exclusively on architectural patterns and design quality"

# Fork for test coverage review
claude --fork-session --session-id "test-review" --resume
> "Focus exclusively on test coverage and quality"
```

**Benefits**:
- Deep-dive specialized reviews
- Avoid diluting focus across concerns
- Expert-level analysis per dimension
- Combine insights for detailed feedback

#### Memory-Palace: Exploratory Knowledge Intake

**Use Case**: Test categorization strategies

```bash
# Original session: Knowledge intake
claude "/memory-palace:knowledge-intake article.md"

# Fork to try hierarchical categorization
claude --fork-session --session-id "hierarchical-tags" --resume
> "Organize this using hierarchical tags"

# Fork to try flat categorization
claude --fork-session --session-id "flat-tags" --resume
> "Organize this using flat, single-level tags"

# Fork to try semantic categorization
claude --fork-session --session-id "semantic-links" --resume
> "Organize this using semantic relationship links"

# Compare and choose best strategy
```

**Benefits**:
- Test knowledge organization approaches
- Experiment without committing
- Compare categorization effectiveness
- Learn which patterns work best for your content

### Best Practices

#### Naming Conventions

Use descriptive session IDs that indicate purpose:

```bash
# Good
--session-id "pr-123-security-review"
--session-id "feature-x-functional-approach"
--session-id "db-migration-rollback-strategy"

# Avoid
--session-id "fork1"
--session-id "test"
--session-id "temp"
```

#### Fork Lifecycle Management

1. **Create fork with clear purpose**
   ```bash
   claude --fork-session --session-id "clear-purpose" --resume
   ```

2. **Work in fork until complete**
   - Stay focused on fork's specific goal
   - Don't drift into unrelated topics

3. **Extract results**
   - Save findings to file
   - Document key insights
   - Create artifacts (code, docs, configs)

4. **Clean up**
   - Forked sessions persist like any session
   - Use descriptive IDs to identify later
   - Consider documenting fork results in main session

#### Integration with Subagents

Session forking works naturally with subagent delegation:

```bash
# Fork for specialized subagent work
claude --fork-session --session-id "rust-security-audit" --resume

# In fork: Delegate to specialized agent
> "Agent(pensive:rust-auditor): Audit this Rust codebase for memory safety"

# Subagent inherits original context but works in isolated fork
```

#### Avoiding Common Pitfalls

**Don't**: Fork for simple continuations
```bash
# Bad - just use --resume
claude --fork-session --session-id "continue-work" --resume
```

**Do**: Fork for genuinely different approaches
```bash
# Good - exploring alternatives
claude --fork-session --session-id "alternative-architecture" --resume
```

**Don't**: Create forks you won't use
```bash
# Bad - creating forks "just in case"
claude --fork-session --session-id "maybe-later" --resume
```

**Do**: Fork with specific intent
```bash
# Good - clear purpose
claude --fork-session --session-id "refactor-to-dependency-injection" --resume
```

### Advanced Patterns

#### Decision Tree Exploration

```bash
# Original: Architecture decision needed
claude "Should we use microservices or monolith?"

# Fork A: Explore microservices
claude --fork-session --session-id "microservices-exploration" --resume
> "Design this as microservices architecture"

# Fork B: Explore monolith
claude --fork-session --session-id "monolith-exploration" --resume
> "Design this as modular monolith"

# Fork C: Explore hybrid
claude --fork-session --session-id "hybrid-exploration" --resume
> "Design this as monolith with extraction-ready modules"

# Compare trade-offs and make informed decision
```

#### Experiment-Driven Development

```bash
# Original: Feature design
claude "Design user authentication system"

# Fork: Experiment with JWT
claude --fork-session --session-id "auth-jwt-experiment" --resume

# Fork: Experiment with sessions
claude --fork-session --session-id "auth-sessions-experiment" --resume

# Fork: Experiment with OAuth
claude --fork-session --session-id "auth-oauth-experiment" --resume

# Prototype each, evaluate results
```

#### Parallel Testing Strategies

```bash
# Original: Test plan needed
claude "How should we test this API?"

# Fork: Unit test approach
claude --fork-session --session-id "unit-test-strategy" --resume

# Fork: Integration test approach
claude --fork-session --session-id "integration-test-strategy" --resume

# Fork: E2E test approach
claude --fork-session --session-id "e2e-test-strategy" --resume

# Fork: Contract test approach
claude --fork-session --session-id "contract-test-strategy" --resume

# Combine insights for detailed test strategy
```

## LSP Integration Patterns (2.0.74+)

### Overview

The LSP (Language Server Protocol) tool provides **semantic** code intelligence, fundamentally different from syntactic pattern matching with grep/rg.

**Key Difference**:
- **Grep/Ripgrep**: Text pattern matching - fast but syntactic
- **LSP**: Semantic understanding - understands code structure, types, references

**Performance Comparison**:
```
Find all call sites of a function:
- grep: ~45 seconds (searches all text)
- LSP: ~50ms (uses semantic index)
```

### When to Use LSP vs. Grep

**Default Strategy**: **Prefer LSP, fallback to grep when needed.**

| Task | Tool | Reason |
|------|------|--------|
| Find function/class definition | **LSP (preferred)** | Semantic accuracy (handles overloads, shadowing) |
| Find all references to symbol | **LSP (preferred)** | True references, not string matches |
| Get type information | **LSP (preferred)** | Type system awareness |
| Unused code detection | **LSP (preferred)** | Semantic analysis of references |
| API usage patterns | **LSP (preferred)** | Understands call hierarchies |
| Code navigation | **LSP (preferred)** | 900x faster than grep |
| Search for text pattern | Grep (fallback) | Simple text search when LSP unavailable |
| Cross-language search | Grep (fallback) | LSP is language-specific |
| Search in docs/comments | Grep (fallback) | LSP focuses on code semantics |
| LSP unavailable | Grep (fallback) | When language server not configured |

**Best Practice**: Enable `ENABLE_LSP_TOOLS=1` by default in your environment.

### Enabling LSP

LSP integration requires three components: environment flag, MCP server bridge, and language servers.

#### Step 1: Enable LSP Feature Flag

```bash
# Enable for single session
ENABLE_LSP_TOOLS=1 claude "review this code"

# Enable permanently (recommended - add to ~/.bashrc or ~/.zshrc)
export ENABLE_LSP_TOOLS=1
```

#### Step 2: Install cclsp MCP Server

The cclsp MCP server bridges Language Server Protocol to Claude Code's Model Context Protocol.

**Quick Setup (Interactive)**:
```bash
# Run interactive setup wizard
npx cclsp@latest setup

# The wizard will:
# 1. Detect your project languages
# 2. Recommend language servers
# 3. Configure .cclsp.json
# 4. Update ~/.claude/.mcp.json
# 5. Install language servers (optional)
```

**Manual Setup** (when interactive setup unavailable):

1. **Install cclsp**:
   ```bash
   npm install -g cclsp
   ```

2. **Create project config** (`.cclsp.json` in project root):
   ```json
   {
     "servers": [
       {
         "extensions": ["py", "pyi"],
         "command": ["pylsp"],
         "rootDir": ".",
         "initializationOptions": {
           "settings": {
             "pylsp": {
               "plugins": {
                 "jedi_completion": { "enabled": true },
                 "jedi_definition": { "enabled": true },
                 "jedi_references": { "enabled": true }
               }
             }
           }
         }
       },
       {
         "extensions": ["js", "ts", "jsx", "tsx"],
         "command": ["typescript-language-server", "--stdio"],
         "rootDir": "."
       }
     ]
   }
   ```

3. **Configure MCP server** (`~/.claude/.mcp.json`):
   ```json
   {
     "mcpServers": {
       "cclsp": {
         "type": "stdio",
         "command": "npx",
         "args": ["-y", "cclsp@latest"],
         "env": {
           "CCLSP_CONFIG_PATH": "/home/YOUR_USERNAME/.config/cclsp/config.json"
         }
       }
     }
   }
   ```

   *Notes*:
   - Replace `YOUR_USERNAME` with your actual username
   - If you already have other MCP servers, add `cclsp` to the existing `mcpServers` object
   - You can use a global config (`~/.config/cclsp/config.json`) or project-specific configs

4. **Restart Claude Code** to load the MCP server:
   ```bash
   exit  # Exit current session
   claude  # Start new session
   ```

#### Step 3: Install Language Servers

Install language servers for your project languages:

```bash
# TypeScript/JavaScript
npm install -g typescript typescript-language-server

# Python
pip install python-lsp-server
# Or with uv: uv tool install python-lsp-server

# Rust
rustup component add rust-analyzer

# Go
go install golang.org/x/tools/gopls@latest

# More languages: https://github.com/Piebald-AI/claude-code-lsps
```

#### Verification

After setup, verify LSP is working:

```bash
cd /path/to/your/project
ENABLE_LSP_TOOLS=1 claude

# Ask Claude to test LSP:
# "Find all references to the main function"
# "Show me the definition of MyClass"
```

Claude should respond with precise, semantic results instead of text-based grep matches.

#### Troubleshooting

**MCP server not loading**:
- Check `~/.claude/.mcp.json` syntax (must be valid JSON)
- Verify `npx` is in PATH: `which npx`
- Check logs: `~/.claude/debug/` for MCP errors

**Language server not working**:
- Verify language server is installed: `which typescript-language-server` or `which pylsp`
- Check `.cclsp.json` command paths match installed locations
- validate project has proper language config files (tsconfig.json, pyproject.toml, etc.)

**LSP queries failing**:
- Confirm `ENABLE_LSP_TOOLS=1` is set in environment
- Restart Claude Code after configuration changes
- Check that file extensions in `.cclsp.json` match your project files

**Resources**:
- [cclsp](https://github.com/ktnyt/cclsp) - MCP server for LSP integration
- [Claude Code LSPs](https://github.com/Piebald-AI/claude-code-lsps) - Language server marketplace

### Plugin-Specific Patterns

#### Pensive: Code Review with LSP

**Enhanced Capabilities**:
1. **Impact Analysis**: Find all references to changed functions
2. **Unused Code Detection**: Identify unreferenced functions/types
3. **API Consistency**: Verify consistent usage patterns
4. **Type Safety**: Validate type usage across codebase

**Example Workflow**:
```bash
# Start code review with LSP enabled
ENABLE_LSP_TOOLS=1 claude

# Request review with semantic analysis
> "/pensive:code-review src/ --check-impact --find-unused"

# Agent uses LSP to:
# 1. Find all call sites of modified functions (impact)
# 2. Identify unused exports (dead code)
# 3. Verify type consistency
# 4. Check API usage patterns
```

**Agent Integration**:
When LSP is available, agents should:
- Use LSP for reference finding instead of grep
- use type information for better analysis
- Detect unused code automatically
- Provide accurate impact assessments

#### Sanctum: Documentation with LSP

**Enhanced Capabilities**:
1. **Reference Finding**: Locate all usages of documented items
2. **API Completeness**: Verify all public APIs are documented
3. **Cross-Reference Validation**: validate doc links are accurate
4. **Signature Verification**: Check docs match actual signatures

**Example Workflow**:
```bash
ENABLE_LSP_TOOLS=1 claude "/sanctum:update-docs --verify-completeness"

# Agent uses LSP to:
# 1. Find all public APIs
# 2. Check which lack documentation
# 3. Verify documented signatures match code
# 4. Find references for usage examples
```

#### Conservation: Token Efficiency with LSP

**Token Savings**:
```
Without LSP (grep approach):
1. Read multiple files to search (10,000+ tokens)
2. Filter results manually (context pollution)
3. Verify matches are correct (additional reads)

With LSP:
1. Query LSP for exact location (100 tokens)
2. Read only relevant sections (500 tokens)
3. Results are semantically accurate (no verification needed)

Savings: ~90% token reduction for reference finding
```

**Best Practices**:
- **Default to LSP**: Use LSP for all code navigation and analysis
- **Fallback to grep**: Only when LSP unavailable or for text-in-comments searches
- **Enable globally**: Add `export ENABLE_LSP_TOOLS=1` to your shell rc
- **Combine when needed**: LSP for precision + grep for broad text searches

### LSP Tool Usage Examples

#### Find Definition
```yaml
Task: Find where function `processData` is defined
LSP Query: "Find definition of processData"
Result: Exact file:line with full context
```

#### Find All References
```yaml
Task: Find all call sites of `UserService.authenticate`
LSP Query: "Find all references to UserService.authenticate"
Result: List of all actual calls (not string matches)
```

#### Get Type Information
```yaml
Task: What is the return type of `fetchUser`?
LSP Query: "Show type information for fetchUser"
Result: Function signature with return type
```

#### Find Unused Code
```yaml
Task: Which exports are never imported?
LSP Query: "Find unused exports in src/"
Result: List of exported items with zero references
```

### Integration Best Practices

1. **LSP First**: Always try LSP before falling back to grep
2. **Enable by Default**: Set `ENABLE_LSP_TOOLS=1` in environment permanently
3. **Graceful Degradation**: If LSP unavailable, automatically fall back to grep
4. **Language Awareness**: Verify LSP supports project language, fallback otherwise
5. **Context Efficiency**: Prefer LSP for 90% token reduction vs. grep
6. **Accuracy Priority**: LSP provides semantic correctness (essential for refactoring, impact analysis)

### Limitations

- **Language-Specific**: Requires language server per language
- **Setup Required**: Language servers must be installed/configured
- **Project-Aware**: Works best with properly configured projects
- **Not for Text Search**: Use grep for searching strings in comments/docs

## Tool Restriction Patterns (2.0.74+)

### Overview

Claude Code 2.0.74 fixed a critical security bug where `allowed-tools` restrictions in skill frontmatter were not being enforced. Now they work correctly.

### Security Context

**The Bug (< 2.0.74)**:
```yaml
---
name: read-only-skill
allowed-tools: [Read, Grep, Glob]  # ❌ NOT enforced - skill had ALL tools!
---
```

**The Fix (2.0.74+)**:
```yaml
---
name: read-only-skill
allowed-tools: [Read, Grep, Glob]  # ✅ Properly enforced - only these tools available
---
```

### When to Use Tool Restrictions

**Use `allowed-tools` when**:
1. Processing untrusted input
2. Read-only analysis/auditing tasks
3. Skills that shouldn't modify filesystem
4. Skills that shouldn't execute arbitrary code
5. Security-sensitive operations

**Don't restrict when**:
1. Full control needed for task
2. Legitimate need for restricted tools
3. Performance requires broad tool access

### Agent tools vs. Skill allowed-tools

**Important Distinction**:

```yaml
# AGENT frontmatter (whitelist - what's available)
---
name: code-reviewer
tools: [Read, Write, Edit, Bash, Glob, Grep]  # Agent CAN use these
---
```

```yaml
# SKILL frontmatter (restrictions - what's allowed)
---
name: read-only-analysis
allowed-tools: [Read, Grep, Glob]  # Skill MAY ONLY use these
---
```

**Combined Behavior**:
- Agent `tools:` defines available toolset
- Skill `allowed-tools:` further restricts what skill can use
- Skill restrictions apply to tools invoked BY the skill
- Result: Intersection of agent tools and skill allowed-tools

### Security Patterns

#### Pattern 1: Read-Only Analysis

**Use Case**: Code auditing, security scanning, review tasks

```yaml
---
name: security-audit
description: Audit codebase for security vulnerabilities (read-only)
allowed-tools: [Read, Grep, Glob]
---

# This skill can:
# ✅ Read files
# ✅ Search with grep
# ✅ Find files with glob
# ❌ Write/Edit files
# ❌ Execute bash commands
# ❌ Make changes
```

#### Pattern 2: Safe Execution

**Use Case**: Skills that need bash but with restrictions

```yaml
---
name: test-runner
description: Run tests without modifying code
allowed-tools: [Read, Bash, Grep, Glob]
---

# This skill can:
# ✅ Read test files
# ✅ Run test commands (bash)
# ✅ Parse results (grep)
# ❌ Modify source code
# ❌ Write new files
```

**Note**: Bash is capable - if allowed, skill can still do dangerous things. Consider carefully.

#### Pattern 3: No External Execution

**Use Case**: Pure analysis without system interaction

```yaml
---
name: code-complexity-analyzer
description: Analyze code complexity without executing anything
allowed-tools: [Read, Grep, Glob]
---

# This skill can:
# ✅ Read source files
# ✅ Search patterns
# ✅ Find files
# ❌ Execute code
# ❌ Make system calls
# ❌ Modify anything
```

#### Pattern 4: Untrusted Input Processing

**Use Case**: Skills processing user-provided data

```yaml
---
name: user-config-validator
description: Validate user configuration files (no execution)
allowed-tools: [Read]
---

# This skill can:
# ✅ Read config file
# ❌ Search filesystem (prevent info disclosure)
# ❌ Execute validation scripts (prevent code injection)
# ❌ Write anywhere (prevent file creation)
```

### Migration from < 2.0.74

**Action Required**: Audit existing skills

```bash
# Find skills with allowed-tools
grep -r "allowed-tools:" plugins/*/skills/*/SKILL.md

# Verify each:
# 1. Was restriction intentional?
# 2. Does skill assume restricted toolset?
# 3. Does description document security boundary?
```

**Risk Assessment**:
- **Low Risk**: Ecosystem currently has NO skills using `allowed-tools`
- **Future Risk**: New skills may assume restrictions work
- **Mitigation**: Document patterns, test restrictions, security reviews

### Best Practices

1. **Principle of Least Privilege**: Grant minimum tools needed
2. **Document Assumptions**: Explain why tools are restricted
3. **Test Restrictions**: Verify skill works with restricted toolset
4. **Security Review**: Audit skills processing untrusted input
5. **Explicit Over Implicit**: State restrictions clearly in description

### Testing Tool Restrictions

```bash
# Create test skill with restrictions
cat > test-skill.md <<'EOF'
---
name: test-restricted
description: Test tool restrictions
allowed-tools: [Read, Grep]
---

Try to use Write tool (should fail)
EOF

# Test with Claude Code 2.0.74+
claude --skill test-restricted.md "Try to write a file"

# Expected: Error or refusal (Write not in allowed-tools)
```

### Ecosystem Audit Results

**Current Status** (as of 2025-12-30):
- ✅ No plugins currently use `allowed-tools`
- ✅ No migration needed for existing skills
- ✅ All agents use `tools:` field (different purpose)
- ⚠️ Future skills should consider tool restrictions

**Recommendations**:
1. Consider `allowed-tools` for new security-sensitive skills
2. Document any security assumptions in skill descriptions
3. Test restrictions if added
4. Review during PR process

## Resources

### Documentation References

- **Hook Authoring**: `plugins/abstract/skills/hook-authoring/`
- **Security Patterns**: `plugins/abstract/skills/hook-authoring/modules/security-patterns.md`
- **Context Optimization**: `plugins/conserve/skills/context-optimization/`
- **MECW Principles**: `plugins/conserve/skills/context-optimization/modules/mecw-principles.md`

### External Resources

- [Claude Code Release Notes](https://code.claude.com/docs/en/release-notes)
- [Claude Agent SDK Documentation](https://github.com/anthropics/claude-code-sdk)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Agent Skills Documentation](https://platform.claude.com/docs/en/agent-sdk/skills)
- [cclsp LSP MCP Server](https://github.com/ktnyt/cclsp)
- [Claude Code LSP Marketplace](https://github.com/Piebald-AI/claude-code-lsps)

---

**Last Updated**: 2025-12-30
**Ecosystem Version**: 1.1.1+
**Tested With**: Claude Code 2.0.74
