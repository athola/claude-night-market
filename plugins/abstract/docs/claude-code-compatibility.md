# Claude Code Compatibility

This document tracks compatibility between the claude-night-market plugin ecosystem and Claude Code versions.

## Quick Navigation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[Reference](compatibility/compatibility-reference.md)** | Version matrix, breaking changes, migration guides | Check version compatibility, plan upgrades |
| **[Features](compatibility/compatibility-features.md)** | Feature timeline by Claude Code version | Learn what's available in each version |
| **[Patterns](compatibility/compatibility-patterns.md)** | LSP, session forking, tool restriction patterns | Implement advanced features |
| **[Issues](compatibility/compatibility-issues.md)** | Known issues, testing, troubleshooting | Debug problems, report bugs |

## Current Recommendations

**Recommended Version**: Claude Code 2.0.74+
- ✅ LSP tool (experimental)
- ✅ Improved /context visualization
- ✅ Security fixes (allowed-tools enforcement)
- ✅ Terminal setup support

**Minimum Version**: Claude Code 2.0.65+
- All core features available
- Native context visibility
- Stable hook execution

## Version Support Matrix

| Claude Code Version | Ecosystem Version | Status | Key Features |
|---------------------|-------------------|--------|--------------|
| 2.0.74+ | 1.1.1+ | ✅ Recommended | LSP, allowed-tools fix, improved /context |
| 2.0.73+ | 1.1.0+ | ✅ Supported | Session forking, plugin discovery, image viewing |
| 2.0.72+ | 1.1.0+ | ✅ Supported | Chrome integration, performance improvements |
| 2.0.71+ | 1.1.0+ | ✅ Supported | Glob patterns, MCP loading fixes |
| 2.0.70+ | 1.0.0+ | ✅ Supported | Wildcard permissions, context accuracy |
| 2.0.65+ | 1.0.0+ | ✅ Supported | Status line visibility, CLAUDE_CODE_SHELL |
| < 2.0.65 | 1.0.0+ | ⚠️ Limited | Missing modern features |

**Full version details**: See [Reference](compatibility/compatibility-reference.md)

## Feature Highlights

### LSP Integration (2.0.74+)

⚠️ **EXPERIMENTAL** - LSP support has known stability issues ([Issue #72](https://github.com/athola/claude-night-market/issues/72))

**Current Recommendation**: Use Grep (ripgrep) as primary method, test LSP experimentally

- **When stable**: Semantic code navigation, 50ms searches vs. 100-500ms grep
- **Affected Plugins**: pensive, sanctum, conserve
- **Documentation**: [LSP Integration Patterns](compatibility/compatibility-patterns.md#lsp-integration-patterns-2074)

### Session Forking (2.0.73+)

Create isolated conversation branches for exploration:

- **Use Cases**: Alternative approaches, parallel analysis, specialized reviews
- **Affected Plugins**: sanctum, imbue, pensive, memory-palace
- **Documentation**: [Session Forking Patterns](compatibility/compatibility-patterns.md#session-forking-patterns-2073)

### Tool Restrictions (2.0.74+)

🔒 **Security Fix**: `allowed-tools` now properly enforced in skills

- **Impact**: Skills can restrict tool access for security
- **Current Usage**: No plugins currently use this (verified)
- **Documentation**: [Tool Restriction Patterns](compatibility/compatibility-patterns.md#tool-restriction-patterns-2074)

## Plugin-Specific Compatibility

### Abstract Plugin
- **Minimum**: 2.0.65+ (recommended 2.0.71+)
- **Features**: Hook authoring, glob pattern fixes, wildcard permissions

### Conservation Plugin
- **Minimum**: 2.0.65+ (recommended 2.0.74+)
- **Features**: Context monitoring, token tracking, /context visualization, LSP efficiency

### Sanctum Plugin
- **Minimum**: 2.0.70+ (recommended 2.0.74+)
- **Features**: CI/CD workflows, LSP documentation, GitHub Actions

### Pensive Plugin
- **Minimum**: 2.0.65+ (recommended 2.0.74+)
- **Features**: Session forking reviews, LSP semantic analysis

**Full plugin compatibility**: See [Features](compatibility/compatibility-features.md#plugin-specific-compatibility)

## Getting Help

- **Known Issues**: See [Issues](compatibility/compatibility-issues.md#known-issues)
- **Testing**: See [Issues](compatibility/compatibility-issues.md#testing-compatibility)
- **Reporting Bugs**: See [Issues](compatibility/compatibility-issues.md#reporting-compatibility-issues)

---

**Last Updated**: 2025-12-30
**Ecosystem Version**: 1.1.1+
**Tested With**: Claude Code 2.0.74
