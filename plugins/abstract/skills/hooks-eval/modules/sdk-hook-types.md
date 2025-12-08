# Python SDK Hook Types

Complete reference for Claude Agent SDK hook types, callbacks, and matchers.

## Hook Events

### HookEvent

Supported hook event types in the Python SDK.

```python
from typing import Literal

HookEvent = Literal[
    "PreToolUse",       # Called before tool execution
    "PostToolUse",      # Called after tool execution
    "UserPromptSubmit", # Called when user submits a prompt
    "Stop",             # Called when stopping execution
    "SubagentStop",     # Called when a subagent stops
    "PreCompact"        # Called before message compaction
]
```

**Important**: Due to setup limitations, the Python SDK does **not** support:
- `SessionStart`
- `SessionEnd`
- `Notification`

### Event Descriptions

| Event | Trigger | Common Uses |
|-------|---------|-------------|
| `PreToolUse` | Before any tool runs | Validation, blocking dangerous commands, logging |
| `PostToolUse` | After tool completes | Audit logging, result transformation, cleanup |
| `UserPromptSubmit` | User submits input | Input validation, preprocessing, redaction |
| `Stop` | Agent stops | Cleanup, final logging, state persistence |
| `SubagentStop` | Subagent completes | Coordination, result aggregation |
| `PreCompact` | Before message compaction | Context preservation, important info extraction |

## Type Definitions

### HookCallback

Type definition for hook callback functions.

```python
from typing import Any, Awaitable, Callable

HookCallback = Callable[
    [dict[str, Any], str | None, HookContext],
    Awaitable[dict[str, Any]]
]
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_data` | `dict[str, Any]` | Hook-specific input data (varies by event) |
| `tool_use_id` | `str \| None` | Tool use identifier (for tool-related hooks) |
| `context` | `HookContext` | Additional context information |

**Returns:** `dict[str, Any]` containing optional fields:

| Field | Type | Description |
|-------|------|-------------|
| `decision` | `str` | Set to `"block"` to block the action |
| `systemMessage` | `str` | System message to add to transcript |
| `hookSpecificOutput` | `dict` | Hook-specific output data |

### HookContext

Context information passed to hook callbacks.

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class HookContext:
    signal: Any | None = None  # Future: abort signal support
```

**Note**: The `signal` field is reserved for future abort signal support.

### HookMatcher

Configuration for matching hooks to specific events or tools.

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class HookMatcher:
    matcher: str | None = None        # Tool name or pattern (e.g., "Bash", "Write|Edit")
    hooks: list[HookCallback] = field(default_factory=list)  # Callbacks to run
    timeout: float | None = None      # Timeout in seconds (default: 60)
```

**Matcher Patterns:**

| Pattern | Matches |
|---------|---------|
| `"Bash"` | Only Bash tool |
| `"Write\|Edit"` | Write OR Edit tools |
| `"Read"` | Only Read tool |
| `None` | All tools (universal matcher) |

**Timeout Behavior:**
- Default timeout is 60 seconds
- Set custom timeout per matcher
- Hook is cancelled if timeout exceeded

## Complete Usage Example

```python
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, HookContext
from typing import Any

async def validate_bash_command(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Validate and potentially block dangerous bash commands."""
    if input_data['tool_name'] == 'Bash':
        command = input_data['tool_input'].get('command', '')
        if 'rm -rf /' in command:
            return {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': 'Dangerous command blocked'
                }
            }
    return {}

async def log_tool_use(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Log all tool usage for auditing."""
    print(f"Tool used: {input_data.get('tool_name')}")
    return {}

# Configure hooks
options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(
                matcher='Bash',
                hooks=[validate_bash_command],
                timeout=120  # 2 minutes for validation
            ),
            HookMatcher(
                hooks=[log_tool_use]  # Applies to all tools (default 60s)
            )
        ],
        'PostToolUse': [
            HookMatcher(hooks=[log_tool_use])
        ]
    }
)

# Run with hooks
async for message in query(
    prompt="Analyze this codebase",
    options=options
):
    print(message)
```

## Input Data by Event Type

### PreToolUse Input

```python
{
    "tool_name": "Bash",           # Name of tool being called
    "tool_input": {                # Tool-specific parameters
        "command": "ls -la",
        "timeout": 30000
    }
}
```

### PostToolUse Input

```python
{
    "tool_name": "Bash",
    "tool_input": {"command": "ls -la"},
    "tool_result": "file1.txt\nfile2.txt",  # Tool output
    "error": None                            # Error if failed
}
```

### UserPromptSubmit Input

```python
{
    "prompt": "User's input text",
    "conversation_id": "conv_123"
}
```

### Stop / SubagentStop Input

```python
{
    "reason": "completed",         # Why stopped
    "final_message": "..."         # Last assistant message
}
```

### PreCompact Input

```python
{
    "messages": [...],             # Messages to be compacted
    "token_count": 50000           # Current token count
}
```

## Hook Return Patterns

### Allow (Default)

```python
return {}  # Empty dict = allow action to proceed
```

### Block Action

```python
return {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Explanation of why blocked"
    }
}
```

### Add System Message

```python
return {
    "systemMessage": "Important context added to conversation"
}
```

### Combined Response

```python
return {
    "decision": "block",
    "systemMessage": "Action blocked for safety",
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Contains dangerous pattern"
    }
}
```

## Common Hook Patterns

### Security Validation Hook

```python
DANGEROUS_PATTERNS = ['rm -rf', 'DROP TABLE', ':(){:|:&};:']

async def security_validator(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Block commands containing dangerous patterns."""
    if input_data['tool_name'] == 'Bash':
        command = input_data['tool_input'].get('command', '')
        for pattern in DANGEROUS_PATTERNS:
            if pattern in command:
                return {
                    'hookSpecificOutput': {
                        'hookEventName': 'PreToolUse',
                        'permissionDecision': 'deny',
                        'permissionDecisionReason': f'Blocked: contains "{pattern}"'
                    }
                }
    return {}
```

### Audit Logging Hook

```python
import json
from datetime import datetime

async def audit_logger(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Log all tool usage to audit file."""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'tool_name': input_data.get('tool_name'),
        'tool_use_id': tool_use_id,
        'input_summary': str(input_data.get('tool_input', {}))[:200]
    }
    with open('audit.log', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    return {}
```

### Rate Limiting Hook

```python
from collections import defaultdict
from time import time

call_counts: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 10  # calls per minute

async def rate_limiter(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Limit tool calls to prevent runaway invocations."""
    tool_name = input_data.get('tool_name', 'unknown')
    now = time()

    # Clean old entries
    call_counts[tool_name] = [t for t in call_counts[tool_name] if now - t < 60]

    if len(call_counts[tool_name]) >= RATE_LIMIT:
        return {
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': f'Rate limit exceeded for {tool_name}'
            }
        }

    call_counts[tool_name].append(now)
    return {}
```

## Best Practices

### Performance

- Keep hooks fast (<100ms for PreToolUse, <200ms for PostToolUse)
- Use appropriate timeouts to prevent hangs
- Avoid blocking I/O in hook callbacks
- Cache expensive computations

### Security

- Validate all input data before processing
- Never use dynamic code evaluation with hook input
- Sanitize any data written to logs
- Use allowlists over blocklists when possible

### Reliability

- Always return a dict (even empty `{}`)
- Handle exceptions gracefully
- Design hooks to be idempotent
- Include meaningful error messages in block reasons

### Testing

- Test hooks with various input patterns
- Verify timeout behavior
- Test error conditions
- Benchmark performance under load
