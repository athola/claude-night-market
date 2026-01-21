# Hook Types and Event Signatures

Complete reference for Claude Code and SDK hook event types. See individual references for detailed specifications.

## Event Lifecycle

```
User Input → UserPromptSubmit → Agent Processing → PreToolUse → Tool Execution
    → PostToolUse → More Processing... → Stop/SubagentStop
```

Context compaction can occur at any time: `PreCompact`

## Quick Reference

| Hook Event | Timing | Purpose |
|------------|--------|---------|
| **PreToolUse** | Before tool execution | Validate/transform inputs |
| **PostToolUse** | After tool execution | Log/modify outputs |
| **PermissionRequest** | Permission dialog | Auto-approve/deny/modify |
| **UserPromptSubmit** | User message submitted | Inject context/filter |
| **Stop** | Agent completes | Cleanup/summarize |
| **SubagentStop** | Subagent completes | Aggregate results |
| **PreCompact** | Before context compaction | Preserve state |

See sections below for detailed specifications of each hook type.

## Hook Execution Order

When multiple hooks match an event:

1. **Global hooks** (from `~/.claude/settings.json`)
2. **Project hooks** (from `.claude/settings.json`)
3. **Plugin hooks** (from plugin `hooks/hooks.json`)

All matching hooks execute **in parallel** unless dependencies exist.

## Return Value Semantics

### PreToolUse
- `None`: Proceed with original input unchanged
- `dict`: Replace tool input with returned dictionary
- `Exception`: Block tool execution, propagate error

### PostToolUse
- `None`: Proceed with original output unchanged
- `str`: Replace tool output with returned string

### UserPromptSubmit
- `None`: Proceed with original message unchanged
- `str`: Replace user message with returned string

### Stop, SubagentStop, PreCompact
- Return value ignored (hook is for side effects only)

## Error Handling

### Hook Failures

**Claude Code**: If hook command exits with non-zero status, the event is blocked (for PreToolUse) or logged as error (for PostToolUse/Stop)

**SDK**: If hook raises exception:
- **PreToolUse**: Blocks tool execution, error propagates to agent
- **PostToolUse/Stop**: Error logged but doesn't block agent
- **UserPromptSubmit**: Error logged, original message proceeds

### Best Practices

1. **Fail Safe**: Default to allowing operations on errors
2. **Timeout**: Set reasonable timeouts (< 30s)
3. **Logging**: Always log hook failures for debugging
4. **Validation**: Validate inputs before processing
5. **Graceful Degradation**: Handle missing data gracefully

## Performance Considerations

### Hook Timing Budgets

- **PreToolUse**: < 1s (blocks tool execution)
- **PostToolUse**: < 5s (blocks output processing)
- **UserPromptSubmit**: < 2s (blocks message processing)
- **Stop/SubagentStop**: < 10s (final cleanup)
- **PreCompact**: < 3s (blocks compaction)

### Optimization Tips

1. **Async I/O**: Use async file/network operations
2. **Batch Operations**: Queue logs, write in batches
3. **Early Returns**: Validate quickly, fail fast
4. **Caching**: Cache expensive computations
5. **Lazy Loading**: Load resources only when needed

## MCP Tool Permissions

### Wildcard Syntax (2.0.70+)

Use `mcp__server__*` to allow or deny all tools from a specific MCP server:

```json
{
  "permissions": {
    "allow": [
      "mcp__notion__*",
      "mcp__github__*"
    ],
    "deny": [
      "mcp__untrusted_server__*"
    ]
  }
}
```

### Permission Patterns

| Pattern | Effect |
|---------|--------|
| `mcp__server__*` | All tools from `server` |
| `mcp__server__specific_tool` | Single tool from `server` |
| `mcp__*` | All MCP tools (use cautiously) |

### MCP Server Loading Fix (2.0.71+)

**Fixed**: MCP servers defined in `.mcp.json` now load correctly when using `--dangerously-skip-permissions`.

**Impact**: Enables fully automated workflows that combine `--dangerously-skip-permissions` with MCP server capabilities, particularly valuable for CI/CD environments.

## Bash Command Permissions

### Glob Pattern Support (2.0.71+)

**Fixed**: Permission rules now correctly allow valid bash commands containing shell glob patterns.

**Examples Now Supported**:
```bash
ls *.txt
for f in *.png; do echo $f; done
rm *.tmp
cp src/*.js dist/
```

**Security Note**: Hooks using `PreToolUse` or `PermissionRequest` should still validate glob patterns for appropriate use cases (see [security-patterns.md](security-patterns.md#bash-glob-pattern-validation)).

## Related Modules

- **sdk-callbacks.md**: Full SDK implementation patterns
- **security-patterns.md**: Security best practices for hooks
- **performance-guidelines.md**: Detailed optimization techniques
- **testing-hooks.md**: Comprehensive testing strategies
