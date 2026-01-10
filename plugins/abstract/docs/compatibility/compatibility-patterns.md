# Claude Code Compatibility Patterns

Integration patterns for LSP, session forking, and tool restrictions.

> **See Also**: [Reference](compatibility-reference.md) | [Features](compatibility-features.md) | [Issues](compatibility-issues.md)

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

> **⚠️ CRITICAL: LSP IS EXPERIMENTAL (v2.0.74-2.0.76)**
>
> LSP support in Claude Code has significant stability issues. See [Issue #72](https://github.com/athola/claude-night-market/issues/72) for details.
>
> **Known Issues:**
> - [#15255](https://github.com/anthropics/claude-code/issues/15255) - Plugin loading broken
> - [#13952](https://github.com/anthropics/claude-code/issues/13952) - Race condition (LSP Manager initializes 52ms before plugins load)
> - [#15641](https://github.com/anthropics/claude-code/issues/15641) - "No LSP server available" despite correct setup
> - [#16214](https://github.com/anthropics/claude-code/issues/16214) - LSP returns errors with proper configuration
>
> **Current Recommendation:** Use **Grep (ripgrep) as primary method**. Test LSP experimentally if desired, but have Grep fallback ready.

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

**Default Strategy (v2.0.74-2.0.76)**: **Try LSP first (if enabled), automatically fall back to Grep on failure.**

This provides the best of both worlds:
- ✅ Get LSP's semantic understanding and speed when it works (~50ms)
- ✅ Automatically fall back to reliable Grep when LSP fails (~100-500ms)
- ✅ Transparent to user - always get results

| Task | Strategy | Implementation |
|------|----------|----------------|
| Find function/class definition | LSP → Grep fallback | Try LSP first; if "No LSP server available", use Grep |
| Find all references to symbol | LSP → Grep fallback | LSP for semantic accuracy; Grep if LSP times out |
| Get type information | LSP → Grep fallback | LSP for type system; read files with Grep if unavailable |
| Unused code detection | LSP → Grep fallback | LSP semantic analysis; Grep pattern search on failure |
| API usage patterns | LSP → Grep fallback | LSP call hierarchies; Grep pattern matching as backup |
| Code navigation | LSP → Grep fallback | LSP 50ms when working; Grep 100-500ms fallback |
| Search for text pattern | **Grep only** | Grep is better for plain text search |
| Cross-language search | **Grep only** | LSP is language-specific |

**Graceful Degradation Pattern**:
```python
# Pseudocode for implementation
try:
    result = lsp_query(symbol)
    if result.is_valid():
        return result
except (LSPUnavailable, LSPTimeout, LSPError):
    return grep_search(symbol)  # Automatic fallback
```

**Best Practice**: Enable `ENABLE_LSP_TOOL=1` permanently. The automatic fallback ensures you always get results, whether LSP is working or not.

### Enabling LSP (Experimental)

> **⚠️ WARNING:** These setup instructions may not result in working LSP due to known bugs in Claude Code v2.0.74-2.0.76. Even with correct setup, you may encounter "No LSP server available" errors due to race conditions and plugin loading issues. See [Issue #72](https://github.com/athola/claude-night-market/issues/72).

**Two Methods Available:**
1. **Plugin-based** (Recommended for testing) - Uses Claude Code plugin marketplace
2. **MCP-based** - Uses cclsp MCP server (documented below)

#### Method 1: Plugin-Based LSP (Recommended)

```bash
# Step 1: Enable LSP feature flag
export ENABLE_LSP_TOOL=1  # Note: Singular "TOOL" not "TOOLS"

# Step 2: Install language servers (the actual LSP binaries)
npm install -g pyright typescript-language-server typescript
rustup component add rust-analyzer  # For Rust
go install golang.org/x/tools/gopls@latest  # For Go

# Step 3: Install official Claude Code LSP plugins
/plugin install pyright-lsp@claude-plugins-official       # Python
/plugin install typescript-lsp@claude-plugins-official    # TypeScript/JavaScript
/plugin install rust-analyzer-lsp@claude-plugins-official # Rust
/plugin install gopls-lsp@claude-plugins-official         # Go

# Other languages: clangd-lsp, csharp-lsp, jdtls-lsp, lua-lsp, php-lsp, swift-lsp
# List all: claude plugin list available | grep lsp
```

**Note:** Use official `claude-plugins-official` marketplace instead of third-party alternatives for better compatibility and support.

**Known Issue:** Even with correct setup, LSP may fail due to race condition where LSP Manager initializes 52ms before plugins load.

#### Method 2: MCP-Based LSP (Alternative)

```bash
# Step 1: Enable LSP Feature Flag
export ENABLE_LSP_TOOL=1  # Add to ~/.bashrc or ~/.zshrc

# Step 2: Install cclsp MCP Server (see below)
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

# More languages available in official marketplace
# List all: claude plugin list available | grep lsp
```

#### Verification

After setup, verify LSP is working:

```bash
cd /path/to/your/project
ENABLE_LSP_TOOL=1 claude

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
- Confirm `ENABLE_LSP_TOOL=1` is set in environment
- Restart Claude Code after configuration changes
- Check that file extensions in `.cclsp.json` match your project files

**Resources**:
- [cclsp](https://github.com/ktnyt/cclsp) - MCP server for LSP integration
- [Official LSP Plugins](https://github.com/anthropics/claude-plugins-official) - Anthropic's official LSP plugins

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
ENABLE_LSP_TOOL=1 claude

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
ENABLE_LSP_TOOL=1 claude "/sanctum:update-docs --verify-completeness"

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
- **Enable globally**: Add `export ENABLE_LSP_TOOL=1` to your shell rc
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
2. **Enable by Default**: Set `ENABLE_LSP_TOOL=1` in environment permanently
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
