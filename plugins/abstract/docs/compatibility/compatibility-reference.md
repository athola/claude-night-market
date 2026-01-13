# Claude Code Compatibility Reference

Quick reference for version support, breaking changes, and migration guides.

> **See Also**: [Features](compatibility-features.md) | [Patterns](compatibility-patterns.md) | [Issues](compatibility-issues.md)

# Claude Code Compatibility Reference

This document tracks compatibility between the claude-night-market plugin ecosystem and Claude Code versions, documenting version-specific features and fixes that affect plugin functionality.

## Version Support Matrix

| Claude Code Version | Ecosystem Version | Status | Notes |
|---------------------|-------------------|--------|-------|
| 2.1.4+ | 1.2.5+ | ✅ Recommended | Background task disable env var, OAuth fix |
| 2.1.3+ | 1.2.5+ | ✅ Supported | Skills/commands merge, subagent model fix, 10-min hook timeout |
| 2.1.0+ | 1.2.3+ | ✅ Supported | Frontmatter hooks, context forking, `once: true` |
| 2.0.74+ | 1.1.1+ | ✅ Supported | LSP tool, allowed-tools fix, improved /context |
| 2.0.73+ | 1.1.0+ | ✅ Supported | Session forking, plugin discovery, image viewing |
| 2.0.72+ | 1.1.0+ | ✅ Supported | Chrome integration, performance improvements |
| 2.0.71+ | 1.1.0+ | ✅ Supported | Glob patterns, MCP loading fixes |
| 2.0.70+ | 1.0.0+ | ✅ Supported | Wildcard permissions, context accuracy |
| 2.0.65+ | 1.0.0+ | ✅ Supported | Status line visibility, CLAUDE_CODE_SHELL |
| < 2.0.65 | 1.0.0+ | ⚠️ Limited | Missing modern features |

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
