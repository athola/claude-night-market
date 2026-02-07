# Claude Code Compatibility Issues

Known issues, testing procedures, and troubleshooting guidance.

> **See Also**: [Reference](compatibility-reference.md) | [Features](compatibility-features.md) | [Patterns](compatibility-patterns.md)

## Known Issues

### Version-Specific Bugs

| Version | Issue | Workaround | Fixed In |
|---------|-------|------------|----------|
| < 2.1.34 | Sandbox-excluded commands bypass permission prompts when auto-allow enabled | Set `allowUnsandboxedCommands: false` or disable auto-allow | 2.1.34 |
| < 2.1.34 | Agent teams setting change between renders causes crash | Avoid changing agent teams settings mid-session | 2.1.34 |
| < 2.1.31 | PDF-too-large errors permanently lock sessions | Start a new conversation | 2.1.31 |
| < 2.1.31 | Bash commands report false "Read-only file system" in sandbox mode | Disable sandbox or retry | 2.1.31 |
| < 2.1.31 | temperatureOverride silently ignored in streaming API | Use non-streaming path | 2.1.31 |
| < 2.1.31 | LSP shutdown fails with strict language servers (null params) | Restart session | 2.1.31 |
| < 2.1.31 | Plan mode crash with missing ~/.claude.json defaults | Ensure config has default fields | 2.1.31 |
| < 2.1.30 | Subagents cannot access SDK-provided MCP tools | Avoid MCP delegation to subagents | 2.1.30 |
| < 2.1.30 | Prompt cache not invalidating on tool schema changes | Restart session after MCP tool updates | 2.1.30 |
| < 2.1.30 | Phantom "(no content)" blocks waste tokens | None | 2.1.30 |
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
- [Official LSP Plugins](https://github.com/anthropics/claude-plugins-official) - Anthropic's official LSP plugins

---

**Last Updated**: 2025-12-30
**Ecosystem Version**: 1.1.1+
**Tested With**: Claude Code 2.0.74
