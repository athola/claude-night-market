# Python SDK Hook Types

Complete reference for Claude Agent SDK hook types, callbacks,
and matchers.

## Hook Events

### HookEvent

Supported hook event types in the Python SDK.

```python
from typing import Literal

HookEvent = Literal[
    "Setup",             # Called when plugin installed/enabled
    "SessionStart",      # Called when session begins
    "SessionEnd",        # Called when session ends normally
    "UserPromptSubmit",  # Called when user submits a prompt
    "PreToolUse",        # Called before tool execution
    "PostToolUse",       # Called after tool execution
    "PostToolUseFailure",# Called when tool execution fails (2.1.20+)
    "PermissionRequest", # Called when permission dialog would appear
    "Notification",      # Called on system notification (2.1.20+)
    "SubagentStart",     # Called when subagent spawns (2.1.20+)
    "SubagentStop",      # Called when a subagent stops
    "Stop",              # Called when stopping execution
    "TeammateIdle",      # Called when teammate agent becomes idle (2.1.33+)
    "TaskCompleted",     # Called when a task finishes execution (2.1.33+)
    "ConfigChange",      # Called when config is modified (2.1.49+)
    "InstructionsLoaded",# Called when instructions are loaded (2.1.33+)
    "PreCompact",        # Called before message compaction
    "PostCompact",       # Called after compaction (2.1.76+)
    "WorktreeCreate",    # Called when git worktree is created (2.1.50+)
    "WorktreeRemove",    # Called when git worktree is removed (2.1.50+)
    "StopFailure",       # Called on error (2.1.78+)
    "TaskCreated",       # Called when task created (2.1.84+)
    "CwdChanged",        # Called on working dir change (2.1.83+)
    "FileChanged",       # Called on file change (2.1.83+)
    "Elicitation",       # MCP elicitation request (2.1.76+)
    "ElicitationResult", # MCP elicitation response (2.1.76+)
]
```

**SDK vs CLI availability**: Most events work in both JSON
hooks (CLI) and Python SDK hooks. `PermissionRequest` is
CLI-only. `Setup`, `SessionStart`, `SessionEnd`, and
`Notification` are CLI-only (JSON hooks).
`WorktreeCreate` and `WorktreeRemove` are command-only
hooks (no Python SDK callback). They do not support
matchers.

### Event Summary

| Event | Trigger | Blockable | Matcher |
|-------|---------|-----------|---------|
| `Setup` | Plugin installed/enabled | No | No |
| `SessionStart` | Session begins | No | No |
| `SessionEnd` | Session ends normally | No | No |
| `UserPromptSubmit` | User submits input | No | No |
| `PreToolUse` | Before any tool runs | Yes | Tool name |
| `PostToolUse` | After tool completes | No | Tool name |
| `PostToolUseFailure` | Tool execution fails | No | Tool name |
| `PermissionRequest` | Permission dialog | Yes | Tool name |
| `SubagentStart` | Subagent spawns | No | No |
| `SubagentStop` | Subagent completes | No | No |
| `Stop` | Agent stops | No | No |
| `TeammateIdle` | Teammate idle | No | No |
| `TaskCompleted` | Task finishes | No | No |
| `ConfigChange` | Config modified | No | No |
| `InstructionsLoaded` | Instructions loaded | No | No |
| `PreCompact` | Before compaction | No | No |
| `PostCompact` | After compaction | No | No |
| `WorktreeCreate` | Worktree created | No | No |
| `WorktreeRemove` | Worktree removed | No | No |
| `StopFailure` | Error occurs | No | Error type |
| `TaskCreated` | Task created | Yes | No |
| `CwdChanged` | Directory changed | No | No |
| `FileChanged` | File changed | No | Filename |
| `Elicitation` | MCP elicitation | Yes | MCP server |
| `ElicitationResult` | Elicitation response | Yes | MCP server |

### Notable Version Changes

All hook events include `agent_id` and `agent_type` as
of 2.1.69+.

| Version | Change |
|---------|--------|
| 2.1.69 | `TeammateIdle`/`TaskCompleted` support `{"continue": false}` for graceful shutdown |
| 2.1.69 | Plugin WorktreeCreate/WorktreeRemove hooks fire correctly (were silently ignored) |
| 2.1.71 | New tools: `CronCreate`, `CronList`, `CronDelete` appear in PreToolUse/PostToolUse |
| 2.1.72 | `ExitWorktree` tool added; `lsof`/`pgrep`/`tput`/`ss`/`fd`/`fdfind` auto-approved |
| 2.1.72 | Skill hook double-fire fixed; `transcript_path` correct for resumed sessions |
| 2.1.72 | Failed Read/WebFetch/Glob no longer cancel sibling tool calls (only Bash cascades) |
| 2.1.73 | SessionStart no longer double-fires on `--resume`/`--continue` |
| 2.1.73 | JSON-output hooks no longer inject spurious system-reminder messages |
| 2.1.74 | SessionEnd hooks timeout now configurable via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` |
| 2.1.75 | Hook source displayed in permission prompts; async hook messages suppressed by default |
| 2.1.76 | `Elicitation` and `ElicitationResult` events for MCP servers |
| 2.1.76 | `PostCompact` event fires after context compaction |
| 2.1.77 | PreToolUse "allow" no longer bypasses deny rules (security fix) |
| 2.1.83 | `CwdChanged` and `FileChanged` events added |
| 2.1.84 | `TaskCreated` event (blockable); HTTP hooks can return worktree path |
| 2.1.85 | `if` field for conditional hook execution; PreToolUse can match `AskUserQuestion` |

## Type Definitions

### HookCallback

```python
from typing import Any, Awaitable, Callable

HookCallback = Callable[
    [dict[str, Any], str | None, HookContext],
    Awaitable[dict[str, Any]]
]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_data` | `dict[str, Any]` | Hook-specific input data (varies by event) |
| `tool_use_id` | `str \| None` | Tool use identifier (for tool-related hooks) |
| `context` | `HookContext` | Additional context information |

**Returns:** `dict[str, Any]` with optional fields:
`decision` ("block"), `systemMessage` (str),
`hookSpecificOutput` (dict).

### HookMatcher

```python
@dataclass
class HookMatcher:
    matcher: str | None = None
    hooks: list[HookCallback] = field(default_factory=list)
    timeout: float | None = None  # Default: 60s
```

| Pattern | Matches |
|---------|---------|
| `"Bash"` | Only Bash tool |
| `"Write\|Edit"` | Write OR Edit tools |
| `None` | All tools (universal matcher) |

## Complete Usage Example

```python
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, HookContext
from typing import Any

async def validate_bash_command(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Block dangerous bash commands."""
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

options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(matcher='Bash', hooks=[validate_bash_command], timeout=120),
            HookMatcher(hooks=[log_tool_use])
        ],
        'PostToolUse': [
            HookMatcher(hooks=[log_tool_use])
        ]
    }
)

async for message in query(prompt="Analyze this codebase", options=options):
    print(message)
```

## Input Data by Event Type

### PreToolUse / PostToolUse

```python
# PreToolUse
{"tool_name": "Bash", "tool_input": {"command": "ls -la"}}

# PostToolUse (adds result)
{"tool_name": "Bash", "tool_input": {"command": "ls -la"},
 "tool_result": "file1.txt\nfile2.txt", "error": None}
```

### PermissionRequest (CLI only)

```python
# Input
{"session_id": "abc123", "tool_name": "Bash",
 "tool_input": {"command": "npm install"},
 "permission_mode": "default", "cwd": "/path/to/project"}

# Output: allow
{"hookSpecificOutput": {"hookEventName": "PermissionRequest",
 "decision": {"behavior": "allow"}}}

# Output: deny
{"hookSpecificOutput": {"hookEventName": "PermissionRequest",
 "decision": {"behavior": "deny", "message": "Reason"}}}
```

### Other Events

| Event | Key Fields |
|-------|------------|
| `UserPromptSubmit` | `prompt`, `conversation_id` |
| `TeammateIdle` | `agent_id`, `session_id` |
| `TaskCompleted` | `task_id`, `result`, `duration_ms`, `token_count` |
| `Stop` / `SubagentStop` | `reason`, `final_message` |
| `PreCompact` | `messages`, `token_count` |
| `PostCompact` | `trigger` ("manual"/"auto"), `compact_summary` |
| `WorktreeCreate` | `name` (must print worktree path to stdout) |
| `WorktreeRemove` | `worktree_path` (cannot block removal) |

## Hook Return Patterns

```python
# Allow (default)
return {}

# Block action
return {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Explanation"
    }
}

# Add system message
return {"systemMessage": "Important context added to conversation"}
```

## Best Practices

| Area | Guidance |
|------|----------|
| Performance | Keep hooks fast (<100ms PreToolUse, <200ms PostToolUse) |
| Performance | Use appropriate timeouts; cache expensive computations |
| Security | Validate all input; never use dynamic code eval with hook input |
| Security | Use allowlists over blocklists; sanitize log data |
| Reliability | Always return a dict (even empty `{}`); handle exceptions |
| Reliability | Design hooks to be idempotent; include meaningful block reasons |
| Testing | Test with various input patterns; verify timeout behavior |
