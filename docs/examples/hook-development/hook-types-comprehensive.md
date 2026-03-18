# Hook Types and Event Signatures

Complete reference for Claude Code and SDK hook event types.
See individual references for detailed specifications.

## Event Lifecycle

```
User Input → UserPromptSubmit → Agent Processing → PreToolUse → Tool Execution
    → PostToolUse → More Processing... → Stop/SubagentStop
```

Context compaction can occur at any time: `PreCompact`

## Quick Reference (Claude Code 2.1.50)

| Hook Event | Timing | Version | Purpose |
|------------|--------|---------|---------|
| **Setup** | Plugin install/enable | 2.1.0+ | One-time initialization |
| **SessionStart** | Session begins | 2.1.0+ | Initialize state, config |
| **SessionEnd** | Session ends normally | 2.1.0+ | Cleanup, persist state |
| **UserPromptSubmit** | User message submitted | 2.1.0+ | Inject context/filter |
| **PreToolUse** | Before tool execution | 2.1.0+ | Validate/transform inputs |
| **PostToolUse** | After tool execution | 2.1.0+ | Log/modify outputs |
| **PostToolUseFailure** | Tool fails | 2.1.20+ | Error handling/fallback |
| **PermissionRequest** | Permission dialog | 2.1.0+ | Auto-approve/deny/modify |
| **Notification** | System notification | 2.1.20+ | Forward alerts, log |
| **SubagentStart** | Subagent spawns | 2.1.20+ | Track agent lifecycle |
| **SubagentStop** | Subagent completes | 2.1.20+ | Aggregate results |
| **Stop** | Agent completes | 2.1.0+ | Cleanup/summarize |
| **TeammateIdle** | Teammate idle | 2.1.33+ | Work assignment |
| **TaskCompleted** | Task finishes | 2.1.33+ | Coordination/chaining |
| **ConfigChange** | Config modified | 2.1.49+ | React to settings |
| **InstructionsLoaded** | Instructions loaded | 2.1.33+ | Augment instructions |
| **PreCompact** | Before compaction | 2.1.20+ | Preserve state |
| **WorktreeCreate** | Worktree created | 2.1.50+ | Initialize worktree |
| **WorktreeRemove** | Worktree removed | 2.1.50+ | Cleanup worktree |

See sections below for detailed specifications of each hook type.

### Hook Event Field Enrichment (2.1.69+)

All hook events now include `agent_id` (subagent
sessions) and `agent_type` (subagent and `--agent`
sessions) in the input JSON. These fields enable
agent-specific hook logic. Status line hooks also
gain a `worktree` field in worktree sessions.

`TeammateIdle` and `TaskCompleted` hooks support
`{"continue": false, "stopReason": "..."}` to stop
a teammate, matching `Stop` hook behavior.

Plugin-registered `WorktreeCreate`/`WorktreeRemove`
hooks were silently ignored before 2.1.69 and now
fire correctly.

### Cron Scheduling Tools (2.1.71+)

New built-in tools `CronCreate`, `CronList`,
`CronDelete` for session-scoped scheduled tasks. These
appear as tool names in `PreToolUse`/`PostToolUse`
events. Sessions support up to 50 scheduled tasks with
3-day auto-expiry. Disable with
`CLAUDE_CODE_DISABLE_CRON=1`.

### Bash Allowlist and Heredoc Fixes (2.1.71+)

Added `fmt`, `comm`, `cmp`, `numfmt`, `expr`, `test`,
`printf`, `getconf`, `seq`, `tsort`, `pr` to the bash
auto-approval allowlist. Heredoc commit messages in
compound commands no longer trigger false-positive
permission prompts.

### Security: Workspace Trust (2.1.51+)

Hook commands that emit `statusLine` or `fileSuggestion`
require workspace trust acceptance in interactive mode.
Untrusted hooks cannot execute these commands. Test hooks
in both trusted and untrusted workspace contexts.

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

**Claude Code**: If hook command exits with non-zero status,
the event is blocked (for PreToolUse) or logged as error (for PostToolUse/Stop)

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

### BashTool Login Shell (2.1.51+)

BashTool now skips the login shell (`-l` flag) by
default when a shell snapshot is available. This
improves command execution performance. Previously
this behavior required setting
`CLAUDE_BASH_NO_LOGIN=true`. Hook developers using
Bash commands should not rely on login shell profile
sourcing (`.bash_profile`, `.zprofile`). Use explicit
`source` commands if your hook needs specific shell
environment setup.

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

**Fixed**: MCP servers defined in `.mcp.json` now load correctly when using
`--dangerously-skip-permissions`.

**Impact**: Enables fully automated workflows that combine
`--dangerously-skip-permissions` with MCP server capabilities,
particularly valuable for CI/CD environments.

## Bash Command Permissions

### Glob Pattern Support (2.0.71+)

**Fixed**: Permission rules now correctly allow valid bash commands containing
shell glob patterns.

**Examples Now Supported**:
```bash
ls *.txt
for f in *.png; do echo $f; done
rm *.tmp
cp src/*.js dist/
```

**Security Note**: Hooks using `PreToolUse` or
`PermissionRequest` should still validate glob patterns
for appropriate use cases
(see [security-patterns.md](security-patterns.md#bash-glob-pattern-validation)).

## Related Modules

- **sdk-callbacks.md**: Full SDK implementation patterns
- **security-patterns.md**: Security best practices for hooks
- **performance-guidelines.md**: Detailed optimization techniques
- **testing-hooks.md**: Comprehensive testing strategies
