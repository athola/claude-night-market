---
name: hook-authoring
description: |
  Complete guide for writing Claude Code and SDK hooks with security-first design.

  Triggers: hook creation, hook writing, PreToolUse, PostToolUse, UserPromptSubmit,
  tool validation, logging hooks, context injection, workflow automation

  Use when: creating new hooks for tool validation, logging operations for audit,
  injecting context before prompts, enforcing project-specific workflows,
  preventing dangerous operations in production

  DO NOT use when: logic belongs in core skill - use Skills instead.
  DO NOT use when: complex multi-step workflows needed - use Agents instead.
  DO NOT use when: behavior better suited for custom tool.

  Use this skill BEFORE writing any hook. Check even if unsure.
version: 1.0.0
category: hook-development
tags: [hooks, sdk, security, performance, automation, validation]
dependencies: []
estimated_tokens: 1200
complexity: intermediate
provides:
  patterns: [hook-authoring, security-patterns, performance-optimization]
  infrastructure: [hook-validation, testing-framework]
usage_patterns:
  - writing-hooks
  - hook-validation
  - security-patterns
  - performance-optimization
  - sdk-integration
---

# Hook Authoring Guide

## Overview

Hooks are event interceptors that allow you to extend Claude Code and Claude Agent SDK behavior by executing custom logic at specific points in the agent lifecycle. They enable validation before tool use, logging after actions, context injection, workflow automation, and security enforcement.

This skill teaches you how to write effective, secure, and performant hooks for both declarative JSON (Claude Code) and programmatic Python (Claude Agent SDK) use cases.

### Key Capabilities

- **PreToolUse**: Validate, filter, or transform tool inputs before execution
- **PostToolUse**: Log, analyze, or modify tool outputs after execution
- **UserPromptSubmit**: Inject context or filter user messages before processing
- **Stop/SubagentStop**: Cleanup, final reporting, or result aggregation
- **PreCompact**: State preservation before context window compaction

## Quick Start

### Your First Hook (JSON - Claude Code)

Create a simple logging hook in `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": { "toolName": "Bash" },
        "hooks": [{
          "type": "command",
          "command": "echo \"$(date): Executed $CLAUDE_TOOL_NAME\" >> ~/.claude/audit.log"
        }]
      }
    ]
  }
}
```

This logs every Bash command execution with a timestamp.

### Your First Hook (Python - Claude Agent SDK)

Create a validation hook using the SDK:

```python
from claude_agent_sdk import AgentHooks

class ValidationHooks(AgentHooks):
    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Validate tool inputs before execution."""
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if "rm -rf /" in command:
                raise ValueError("Dangerous command blocked by hook")

        # Return None to proceed unchanged, or modified dict to transform
        return None
```

## Hook Event Types

Quick reference for all supported hook events:

| Event | Trigger Point | Parameters | Common Use Cases |
|-------|--------------|------------|------------------|
| **PreToolUse** | Before tool execution | `tool_name`, `tool_input` | Validation, filtering, input transformation |
| **PostToolUse** | After tool execution | `tool_name`, `tool_input`, `tool_output` | Logging, metrics, output transformation |
| **UserPromptSubmit** | User sends message | `message` | Context injection, content filtering |
| **Stop** | Agent completes | `reason`, `result` | Final cleanup, summary reports |
| **SubagentStop** | Subagent completes | `subagent_id`, `result` | Result processing, aggregation |
| **PreCompact** | Before context compact | `context_size` | State preservation, checkpointing |

## Claude Code vs SDK

### JSON Hooks (Claude Code)

**Declarative configuration** in `.claude/settings.json`, project `.claude/settings.json`, or plugin `hooks/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "toolName": "Edit", "inputPattern": "production" },
        "hooks": [{
          "type": "command",
          "command": "echo 'WARNING: Editing production file' >&2"
        }]
      }
    ]
  }
}
```

**Pros:** Simple, no code required, easy to version control
**Cons:** Limited logic capabilities, shell command only

### Python SDK Hooks

**Programmatic callbacks** using `AgentHooks` base class:

```python
from claude_agent_sdk import AgentHooks

class MyHooks(AgentHooks):
    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        # Complex validation logic
        if self._is_dangerous(tool_input):
            raise ValueError("Operation blocked")
        return None  # or return modified input
```

**Pros:** Full Python capabilities, complex logic, state management
**Cons:** Requires Python, more complex setup

## Security Essentials

### Critical Security Rules

1. **Input Validation**: Always validate tool inputs before processing
2. **No Secret Logging**: Never log API keys, tokens, passwords, or credentials
3. **Sandbox Awareness**: Respect sandbox boundaries, don't escape
4. **Fail-Safe Defaults**: Return None on error instead of blocking the agent
5. **Rate Limiting**: Prevent hook abuse from malicious or buggy code
6. **Injection Prevention**: Sanitize all logged content to prevent log injection

### Example: Secure Logging Hook

```python
import re
from claude_agent_sdk import AgentHooks

class SecureLoggingHooks(AgentHooks):
    # Patterns that might contain secrets
    SECRET_PATTERNS = [
        r'api[_-]?key',
        r'password',
        r'token',
        r'secret',
        r'credential',
        r'auth',
    ]

    def _sanitize_output(self, text: str) -> str:
        """Remove potential secrets from log output."""
        for pattern in self.SECRET_PATTERNS:
            text = re.sub(
                rf'({pattern}["\s:=]+)([^\s,}}]+)',
                r'\1***REDACTED***',
                text,
                flags=re.IGNORECASE
            )
        return text

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        """Log tool use with sanitization."""
        safe_output = self._sanitize_output(tool_output)
        # Log safe_output...
        return None  # Don't modify output
```

See `modules/security-patterns.md` for detailed security guidance.

## Performance Guidelines

### Performance Best Practices

1. **Non-Blocking**: Use `async`/`await` properly, don't block the event loop
2. **Timeout Handling**: Set reasonable timeouts (< 30s for hooks)
3. **Efficient Logging**: Batch writes, use async I/O
4. **Memory Management**: Don't accumulate unbounded state
5. **Fail Fast**: Quick validation, early returns, avoid expensive operations

### Example: Efficient Hook

```python
import asyncio
from claude_agent_sdk import AgentHooks

class EfficientHooks(AgentHooks):
    def __init__(self):
        self._log_queue = asyncio.Queue()
        self._log_task = None

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        # Quick validation only
        if not self._is_valid_input(tool_input):
            raise ValueError("Invalid input")
        return None

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        # Queue log entry without blocking
        await self._log_queue.put({
            'tool': tool_name,
            'timestamp': time.time()
        })
        return None

    def _is_valid_input(self, tool_input: dict) -> bool:
        """Fast validation check."""
        # Simple checks only, < 10ms
        return len(str(tool_input)) < 1_000_000
```

See `modules/performance-guidelines.md` for detailed optimization techniques.

## Scope Selection

Choose the right location for your hooks based on audience and purpose:

### Decision Framework

```
Is this hook part of a plugin's core functionality?
├─ YES → Plugin hooks (hooks/hooks.json in plugin)
└─ NO ↓

Should all team members on this project have this hook?
├─ YES → Project hooks (.claude/settings.json)
└─ NO ↓

Should this hook apply to all my Claude sessions?
├─ YES → Global hooks (~/.claude/settings.json)
└─ NO → Reconsider if you need a hook at all
```

### Scope Comparison

| Scope | Location | Audience | Committed? | Example Use Case |
|-------|----------|----------|------------|------------------|
| **Plugin** | `hooks/hooks.json` | Plugin users | Yes (with plugin) | YAML validation in YAML plugin |
| **Project** | `.claude/settings.json` | Team members | Yes (in repo) | Block production config edits |
| **Global** | `~/.claude/settings.json` | Only you | Never | Personal audit logging |

See `modules/scope-selection.md` for detailed scope decision guidance.

## Common Patterns

### Validation Hook

Block dangerous operations before execution:

```python
async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Block dangerous patterns
        if any(pattern in command for pattern in ["rm -rf /", ":(){ :|:& };:"]):
            raise ValueError(f"Dangerous command blocked: {command}")

        # Block production access
        if "production" in command and not self._has_approval():
            raise ValueError("Production access requires approval")

    return None
```

### Logging Hook

Audit all tool operations:

```python
async def on_post_tool_use(
    self, tool_name: str, tool_input: dict, tool_output: str
) -> str | None:
    await self._log_entry({
        'timestamp': datetime.now().isoformat(),
        'tool': tool_name,
        'input_size': len(str(tool_input)),
        'output_size': len(tool_output),
        'success': True
    })
    return None
```

### Context Injection Hook

Add relevant context before user prompts:

```python
async def on_user_prompt_submit(self, message: str) -> str | None:
    # Inject project-specific context
    context = await self._load_project_context()
    enhanced_message = f"{context}\n\n{message}"
    return enhanced_message
```

## Testing Hooks

### Unit Testing

```python
import pytest
from my_hooks import ValidationHooks

@pytest.mark.asyncio
async def test_dangerous_command_blocked():
    hooks = ValidationHooks()

    with pytest.raises(ValueError, match="Dangerous command"):
        await hooks.on_pre_tool_use("Bash", {"command": "rm -rf /"})

@pytest.mark.asyncio
async def test_safe_command_allowed():
    hooks = ValidationHooks()
    result = await hooks.on_pre_tool_use("Bash", {"command": "ls -la"})
    assert result is None  # Allows execution
```

See `modules/testing-hooks.md` for detailed testing strategies.

## Module References

For detailed guidance on specific topics:

- **Hook Types**: `modules/hook-types.md` - Detailed event signatures and parameters
- **SDK Callbacks**: `modules/sdk-callbacks.md` - Python SDK implementation patterns
- **Security Patterns**: `modules/security-patterns.md` - detailed security guidance
- **Performance Guidelines**: `modules/performance-guidelines.md` - Optimization techniques
- **Scope Selection**: `modules/scope-selection.md` - Choosing plugin/project/global
- **Testing Hooks**: `modules/testing-hooks.md` - Testing strategies and fixtures

## Tools

- **hook_validator.py**: Validate hook structure and syntax (in `scripts/`)

## Related Skills

- **hook-scope-guide**: Decision framework for hook placement (existing)
- **modular-skills**: Design patterns for skill architecture
- **skills-eval**: Quality assessment and improvement framework

## Next Steps

1. Choose your hook type (JSON vs SDK) based on complexity needs
2. Select the appropriate scope (plugin/project/global)
3. Implement following security and performance best practices
4. Test thoroughly with unit and integration tests
5. Validate using `hook_validator.py` before deployment

## References

- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Agent SDK Documentation](https://docs.anthropic.com/en/docs/claude-agent-sdk)
- [Settings Configuration](https://docs.anthropic.com/en/docs/claude-code/settings)
