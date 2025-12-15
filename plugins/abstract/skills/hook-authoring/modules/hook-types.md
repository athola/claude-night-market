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

## Related Modules

- **sdk-callbacks.md**: Full SDK implementation patterns
- **security-patterns.md**: Security best practices for hooks
- **performance-guidelines.md**: Detailed optimization techniques
- **testing-hooks.md**: Comprehensive testing strategies
