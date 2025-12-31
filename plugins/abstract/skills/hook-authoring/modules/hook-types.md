# Hook Types and Event Signatures

Complete reference for all Claude Code and SDK hook event types, their parameters, timing, and use cases.

## Event Lifecycle

```
User Input → UserPromptSubmit → Agent Processing → PreToolUse → Tool Execution
    → PostToolUse → More Processing... → Stop/SubagentStop
```

Context compaction can occur at any time: `PreCompact`

## Hook Event Specifications

### PreToolUse

**Triggered**: Before any tool execution

**Purpose**: Validate, filter, or transform tool inputs before execution

**Claude Code Signature** (JSON):
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": {
        "toolName": "Bash",           // Optional: filter by tool name
        "inputPattern": "production"  // Optional: filter by input pattern
      },
      "hooks": [{
        "type": "command",
        "command": "validation-script.sh"
      }]
    }]
  }
}
```

**Environment Variables**:
- `CLAUDE_TOOL_NAME`: Name of the tool being executed
- `CLAUDE_TOOL_INPUT`: JSON string of tool input parameters
- `CLAUDE_EVENT`: "PreToolUse"

**Claude Agent SDK Signature**:
```python
async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
    """
    Args:
        tool_name: Name of the tool (e.g., "Bash", "Read", "Edit")
        tool_input: Dictionary of tool parameters

    Returns:
        None: Proceed with original input
        dict: Replace input with returned dictionary
        Raises exception to block execution
    """
    pass
```

**Use Cases**:
- Input validation against security policies
- Parameter transformation (e.g., normalize paths)
- Command filtering (block dangerous operations)
- Pre-execution logging
- Dynamic parameter injection

**Example - Block Production Edits**:
```python
async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
    if tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        if "/production/" in file_path and not self._has_approval():
            raise ValueError(f"Production edit blocked: {file_path}")
    return None
```

---

### PermissionRequest

**Triggered**: When Claude Code displays a permission dialog to the user

**Purpose**: Automatically approve or deny tool permissions, optionally modify inputs

**Claude Code Signature** (JSON):
```json
{
  "hooks": {
    "PermissionRequest": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "permission-handler.sh"
      }]
    }]
  }
}
```

**Environment Variables**:
- `CLAUDE_TOOL_NAME`: Name of the tool requesting permission
- `CLAUDE_TOOL_INPUT`: JSON string of tool input parameters
- `CLAUDE_PERMISSION_MODE`: Current permission mode (e.g., "default")
- `CLAUDE_EVENT`: "PermissionRequest"

**Hook Input** (via stdin as JSON):
```json
{
  "session_id": "abc123",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm install"
  },
  "tool_use_id": "toolu_01ABC123...",
  "permission_mode": "default",
  "cwd": "/path/to/project"
}
```

**Hook Output** (JSON to stdout):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {
        "command": "npm install --save"
      }
    }
  }
}
```

**Decision Behaviors**:

| Behavior | Effect |
|----------|--------|
| `"allow"` | Grants permission, bypasses dialog. Optional `updatedInput` modifies parameters. |
| `"deny"` | Denies permission. Optional `message` explains why. Optional `interrupt: true` stops execution. |

**Use Cases**:
- Auto-approve safe read-only commands (ls, pwd, cat)
- Block dangerous commands with explanations
- Modify command parameters before approval (add safety flags)
- Enforce organization security policies
- Streamline development workflows by pre-approving known-safe operations

**Example - Auto-Approve Safe Commands**:
```bash
#!/bin/bash
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Auto-approve safe read-only commands
if [[ "$tool_name" == "Bash" ]] && [[ "$command" =~ ^(ls|pwd|cat|grep|find|head|tail) ]]; then
  echo '{
    "hookSpecificOutput": {
      "hookEventName": "PermissionRequest",
      "decision": { "behavior": "allow" }
    }
  }'
  exit 0
fi

# Default: let permission dialog proceed
exit 0
```

**Example - Deny with Explanation**:
```python
#!/usr/bin/env python3
import json
import sys

input_data = json.load(sys.stdin)
command = input_data.get("tool_input", {}).get("command", "")

dangerous = ["rm -rf", "sudo", ":(){ :|:& };:"]
if any(p in command for p in dangerous):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "deny",
                "message": "Command blocked: contains dangerous pattern",
                "interrupt": True
            }
        }
    }))
    sys.exit(0)

sys.exit(0)
```

**Key Differences from PreToolUse**:

| Aspect | PreToolUse | PermissionRequest |
|--------|------------|-------------------|
| **Timing** | Before tool execution | When permission dialog would appear |
| **Purpose** | Validate/transform inputs | Control permission grant/deny |
| **User Experience** | User may still see dialog | Can bypass dialog entirely |
| **Blocking** | Raise exception to block | Return `deny` decision |

**Note**: PermissionRequest hooks run when the user would normally see a permission dialog. If the operation is already allowed (via allowlist or permission mode), this hook won't trigger.

---

### PostToolUse

**Triggered**: After tool execution completes successfully

**Purpose**: Log, analyze, or modify tool outputs

**Claude Code Signature** (JSON):
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": { "toolName": "Bash" },
      "hooks": [{
        "type": "command",
        "command": "echo \"Executed: $CLAUDE_TOOL_NAME\" >> audit.log"
      }]
    }]
  }
}
```

**Environment Variables**:
- `CLAUDE_TOOL_NAME`: Name of the tool that executed
- `CLAUDE_TOOL_INPUT`: JSON string of tool input parameters
- `CLAUDE_TOOL_OUTPUT`: Tool execution output
- `CLAUDE_EVENT`: "PostToolUse"

**Claude Agent SDK Signature**:
```python
async def on_post_tool_use(
    self,
    tool_name: str,
    tool_input: dict,
    tool_output: str
) -> str | None:
    """
    Args:
        tool_name: Name of the tool that executed
        tool_input: Dictionary of tool parameters
        tool_output: Raw output from tool execution

    Returns:
        None: Proceed with original output
        str: Replace output with returned string
    """
    pass
```

**Use Cases**:
- Audit logging
- Performance metrics collection
- Output transformation or filtering
- Success/failure tracking
- Cost accounting (token usage, API calls)

**Example - Performance Tracking**:
```python
async def on_post_tool_use(
    self, tool_name: str, tool_input: dict, tool_output: str
) -> str | None:
    execution_time = time.time() - self._start_times.get(tool_name, 0)

    await self._metrics.record({
        'tool': tool_name,
        'duration_ms': execution_time * 1000,
        'output_size': len(tool_output),
        'timestamp': datetime.now().isoformat()
    })

    return None  # Don't modify output
```

---

### UserPromptSubmit

**Triggered**: When user submits a message to the agent

**Purpose**: Inject context or filter user input before processing

**Claude Code Signature** (JSON):
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "inject-context.sh"
      }]
    }]
  }
}
```

**Environment Variables**:
- `CLAUDE_USER_MESSAGE`: The user's submitted message
- `CLAUDE_EVENT`: "UserPromptSubmit"

**Claude Agent SDK Signature**:
```python
async def on_user_prompt_submit(self, message: str) -> str | None:
    """
    Args:
        message: The user's original message

    Returns:
        None: Proceed with original message
        str: Replace message with returned string
    """
    pass
```

**Use Cases**:
- Inject project-specific context
- Add relevant documentation references
- Filter sensitive information
- Translate or normalize input
- Add instructions or constraints

**Example - Context Injection**:
```python
async def on_user_prompt_submit(self, message: str) -> str | None:
    # Load project context if task involves files
    if any(keyword in message.lower() for keyword in ['file', 'code', 'edit']):
        project_context = await self._load_project_conventions()
        enhanced = f"{project_context}\n\nUser Request: {message}"
        return enhanced

    return None
```

---

### Stop

**Triggered**: When the agent completes execution

**Purpose**: Final cleanup, summary reporting, or result processing

**Claude Code Signature** (JSON):
```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "cleanup-and-report.sh"
      }]
    }]
  }
}
```

**Environment Variables**:
- `CLAUDE_STOP_REASON`: Why agent stopped ("complete", "error", "user_interrupt")
- `CLAUDE_RESULT`: Final result or output
- `CLAUDE_EVENT`: "Stop"

**Claude Agent SDK Signature**:
```python
async def on_stop(self, reason: str, result: Any) -> None:
    """
    Args:
        reason: Why the agent stopped
        result: Final result from agent execution

    Returns:
        None (return value ignored)
    """
    pass
```

**Use Cases**:
- Generate execution summaries
- Clean up temporary resources
- Final metric reporting
- Send notifications
- Archive session data

**Example - Summary Report**:
```python
async def on_stop(self, reason: str, result: Any) -> None:
    summary = {
        'reason': reason,
        'tools_used': len(self._tool_executions),
        'duration': time.time() - self._session_start,
        'success': reason == 'complete'
    }

    await self._save_summary(summary)
    print(f"Session complete: {summary['tools_used']} tools in {summary['duration']:.2f}s")
```

---

### SubagentStop

**Triggered**: When a subagent completes its task

**Purpose**: Process subagent results, aggregate data, or coordinate multi-agent workflows

**Claude Agent SDK Signature**:
```python
async def on_subagent_stop(self, subagent_id: str, result: Any) -> None:
    """
    Args:
        subagent_id: Unique identifier for the subagent
        result: Result from subagent execution

    Returns:
        None (return value ignored)
    """
    pass
```

**Use Cases**:
- Aggregate results from multiple subagents
- Coordinate parallel task execution
- Track subagent performance
- Handle failures or retries
- Result validation before merging

**Example - Result Aggregation**:
```python
async def on_subagent_stop(self, subagent_id: str, result: Any) -> None:
    self._subagent_results[subagent_id] = result

    # If all subagents complete, aggregate results
    if len(self._subagent_results) == self._expected_subagents:
        aggregated = await self._aggregate_results(self._subagent_results)
        await self._store_final_result(aggregated)
```

---

### PreCompact

**Triggered**: Before the context window is compacted to free space

**Purpose**: Preserve important state before context is reduced

**Claude Agent SDK Signature**:
```python
async def on_pre_compact(self, context_size: int) -> dict | None:
    """
    Args:
        context_size: Current context window size in tokens

    Returns:
        None: No state to preserve
        dict: State to preserve across compaction
    """
    pass
```

**Use Cases**:
- Save critical state before context reduction
- Create checkpoints for long-running sessions
- Preserve metrics or tracking data
- Store intermediate results
- Backup conversation history

**Example - State Preservation**:
```python
async def on_pre_compact(self, context_size: int) -> dict | None:
    # Save important state before compaction
    state = {
        'tool_usage_count': self._tool_counts,
        'session_metrics': self._metrics.summary(),
        'important_context': self._extract_critical_context(),
        'timestamp': datetime.now().isoformat()
    }

    await self._save_checkpoint(state)
    return state
```

---

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

## Testing Hook Events

```python
import pytest
from my_hooks import MyHooks

@pytest.mark.asyncio
async def test_pre_tool_use_validation():
    hooks = MyHooks()

    # Test validation
    with pytest.raises(ValueError):
        await hooks.on_pre_tool_use("Bash", {"command": "rm -rf /"})

    # Test passthrough
    result = await hooks.on_pre_tool_use("Read", {"file_path": "/safe/file.txt"})
    assert result is None

@pytest.mark.asyncio
async def test_post_tool_use_logging():
    hooks = MyHooks()

    await hooks.on_post_tool_use("Bash", {"command": "ls"}, "file1\nfile2")

    # Verify logging occurred
    assert len(hooks._log_entries) == 1
    assert hooks._log_entries[0]['tool'] == 'Bash'
```

## MCP Tool Permissions

When working with MCP (Model Context Protocol) servers, Claude Code supports wildcard syntax for bulk permission management.

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

### Integration with Hooks

Combine MCP permissions with hooks for fine-grained control:

```json
{
  "permissions": {
    "allow": ["mcp__github__*"]
  },
  "hooks": {
    "PreToolUse": [{
      "matcher": { "toolName": "mcp__github__push_files" },
      "hooks": [{
        "type": "command",
        "command": "validate-push.sh"
      }]
    }]
  }
}
```

This allows all GitHub MCP tools but adds validation before push operations.

### MCP Server Loading Fix (2.0.71+)

**Fixed**: MCP servers defined in `.mcp.json` now load correctly when using `--dangerously-skip-permissions`.

**Previous Behavior** (2.0.70 and earlier):
- MCP servers from `.mcp.json` were not detected when running with `--dangerously-skip-permissions`
- Required initial manual trust step before automation workflows could use MCP servers
- CI/CD pipelines needed workarounds to trust MCP servers first

**Current Behavior** (2.0.71+):
- MCP servers automatically load from `.mcp.json` even with `--dangerously-skip-permissions`
- Automated workflows and CI/CD pipelines work seamlessly
- No manual trust step required for pre-configured MCP servers

**Use Case - CI/CD with MCP**:
```bash
# .mcp.json in repository
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "args": ["--token", "${GITHUB_TOKEN}"]
    }
  }
}

# GitHub Actions workflow
- name: Run Claude Code with MCP
  run: |
    claude --dangerously-skip-permissions \
           --max-turns 10 \
           "Review PR and use GitHub MCP to comment"
```

**Impact**: This fix enables fully automated workflows that combine `--dangerously-skip-permissions` with MCP server capabilities, particularly valuable for CI/CD environments.

## Bash Command Permissions

### Glob Pattern Support (2.0.71+)

**Fixed**: Permission rules now correctly allow valid bash commands containing shell glob patterns.

**Previous Behavior** (2.0.70 and earlier):
- Commands like `ls *.txt` or `for f in *.png` were incorrectly rejected
- Permission system treated glob patterns as potential security risks
- Required explicit permission dialogs for legitimate pattern matching

**Current Behavior** (2.0.71+):
- Shell glob patterns are recognized as valid bash syntax
- No false-positive permission rejections for pattern matching
- Standard glob operations work without permission prompts

**Examples Now Supported**:
```bash
# File listing with patterns
ls *.txt
ls src/**/*.py

# Iteration over matching files
for f in *.png; do echo $f; done
for img in images/*.jpg; do convert $img; done

# Cleanup operations
rm *.tmp
rm -f build/*.o

# Pattern-based operations
cp src/*.js dist/
mv *.log logs/
```

**Security Note**: This fix only affects **shell glob patterns** (wildcards expanded by the shell). It does not change validation for other potentially dangerous patterns. Hooks using `PreToolUse` or `PermissionRequest` should still validate glob patterns for appropriate use cases:

```python
async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
    """Validate glob patterns are used appropriately."""
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Allow safe glob patterns
        safe_patterns = [r'\*\.txt$', r'\*\.log$', r'\*\.tmp$']

        # Block dangerous glob usage
        if re.search(r'rm\s+-rf\s+\*', command):
            raise ValueError("Recursive delete with glob requires confirmation")

    return None
```

**Migration**: If you previously implemented workarounds for glob pattern permissions, you can now simplify your code:

```python
# BEFORE 2.0.71 - needed workarounds
async def on_permission_request(self, tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        # Auto-approve safe glob patterns
        if re.match(r'^ls\s+\*\.\w+$', command):
            return "allow"
    return "ask"

# AFTER 2.0.71 - no workaround needed, glob patterns work natively
# Can remove permission overrides for standard glob operations
```

## Related Modules

- **sdk-callbacks.md**: Full SDK implementation patterns
- **security-patterns.md**: Security best practices for hooks
- **performance-guidelines.md**: Detailed optimization techniques
- **testing-hooks.md**: Comprehensive testing strategies
