---
name: hook-authoring
description: 'Guide creating Claude Code hooks with security-first design. Use for validation and enforcement.'
alwaysApply: false
category: hook-development
tags:
- hooks
- sdk
- security
- performance
- automation
- validation
dependencies: []
estimated_tokens: 1200
complexity: intermediate
model_hint: standard
provides:
  patterns:
  - hook-authoring
  - security-patterns
  - performance-optimization
  infrastructure:
  - hook-validation
  - testing-framework
usage_patterns:
- writing-hooks
- hook-validation
- security-patterns
- performance-optimization
- sdk-integration
---

## When NOT To Use

- Auditing a hook that already exists (use `abstract:hooks-eval`)
- Choosing where a hook should live (use `abstract:hook-scope-guide`)
- Authoring a skill rather than a hook (use `abstract:skill-authoring`)

# Hook Authoring Guide

## Overview

Hooks are event interceptors that allow you to extend Claude Code and Claude Agent SDK behavior by executing custom logic at specific points in the agent lifecycle. They enable validation before tool use, logging after actions, context injection, workflow automation, and security enforcement.

This skill teaches you how to write effective, secure, and performant hooks for both declarative JSON (Claude Code) and programmatic Python (Claude Agent SDK) use cases.

### Key Capabilities

- **PreToolUse**: Validate, filter, or transform tool inputs before execution; inject context (2.1.9+)
- **PostToolUse**: Log, analyze, or modify tool outputs after execution
- **UserPromptSubmit**: Inject context or filter user messages before processing
- **Stop/SubagentStop**: Cleanup, final reporting, or result aggregation
- **TeammateIdle/TaskCompleted**: Multi-agent coordination and orchestration (2.1.33+)
- **PreCompact**: State preservation before context window compaction

> **New in 2.1.9**: PreToolUse hooks can now return `additionalContext` to inject information before a tool executes. This enables patterns like cache hints, security warnings, or relevant context injection.

## Quick Start

### Your First Hook (JSON - Claude Code)

Create a simple logging hook in `.claude/settings.json`:

```json
{
  "PostToolUse": [
    {
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "echo \"$(date): Executed $(jq -r '.tool_name')\" >> ~/.claude/audit.log"
      }]
    }
  ]
}
```

**Note**: Use string matchers (`"Bash"`) not object matchers (`{"toolName": "Bash"}`).

**Verification:** Run the command with `--help` flag to verify availability.

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
**Verification:** Run the command with `--help` flag to verify availability.

## Hook Event Types

Quick reference for the events most plugins use. Every event also
receives the common fields (`session_id`, `transcript_path`, `cwd`,
`hook_event_name`, and `permission_mode` where it applies). The full
roster of 33 events is `plugins/abstract/src/abstract/hook_events.py`,
and each event's input is in code.claude.com/docs/en/hooks.

| Event | Trigger Point | Parameters | Common Use Cases |
|-------|--------------|------------|------------------|
| **PreToolUse** | Before tool execution | `tool_name`, `tool_input`, `tool_use_id` | Validation, filtering, input transformation |
| **PostToolUse** | After a tool succeeds | `tool_name`, `tool_input`, `tool_response` | Logging, metrics, `updatedToolOutput` to replace the result |
| **PostToolUseFailure** | After a tool fails | `tool_name`, `tool_input`, `error` | Failure logging; the exit code is the first line of `error` |
| **UserPromptSubmit** | User sends message | `prompt` | Context injection, content filtering |
| **PermissionRequest** | Permission dialog shown | `tool_name`, `tool_input`, `permission_suggestions` | Auto-approve/deny with custom logic |
| **Notification** | Claude Code sends notification | `message`, `title`, `notification_type` | Custom notification handling |
| **Stop** | Main turn ends | `stop_hook_active`, `last_assistant_message`, `background_tasks`, `session_crons` | Final checks; read `background_tasks` before blocking |
| **SubagentStop** | Subagent completes | `agent_id`, `agent_type`, `agent_transcript_path`, `last_assistant_message` | Result processing, aggregation |
| **TeammateIdle** | Teammate agent becomes idle | `teammate_name`, `team_name` | Work assignment, load balancing |
| **TaskCompleted** | Task marked complete | `task_id`, `task_subject`, `task_description` | Coordination, chaining, reporting |
| **PreCompact** | Before context compact | `trigger`, `custom_instructions` | State preservation, checkpointing |
| **SessionStart** | Session starts/resumes | `source`, `model`, `agent_type` | Initialization, context loading |
| **SessionEnd** | Session terminates | `reason` | Cleanup, final logging |
| **WorktreeCreate** | Agent worktree created | `name` | Custom VCS setup, symlink .venv, pre-populate caches |
| **WorktreeRemove** | Agent worktree removed | `worktree_path` | Cleanup temp files, teardown worktree-scoped resources |

### SessionStart Input Schema (Claude Code 2.1.2+)

The SessionStart hook receives JSON input via stdin with these fields:

```json
{
  "session_id": "abc123",
  "source": "startup",
  "agent_type": "my-agent"
}
```

Fields: `source` is one of `"startup"`, `"resume"`, `"clear"`, or `"compact"`. `agent_type` is populated when the `--agent` flag is used.

**`agent_type` field**: When Claude Code is launched with `--agent my-agent`, this field contains the agent name, enabling agent-specific initialization:

```python
# Python example: Agent-aware SessionStart hook
input_data = json.loads(sys.stdin.read())
agent_type = input_data.get("agent_type", "")

if agent_type in ["code-reviewer", "quick-query"]:
    # Skip heavy context injection for lightweight agents
    print(json.dumps({"hookSpecificOutput": {"additionalContext": "Minimal context"}}))
else:
    # Full initialization for implementation agents
    print(json.dumps({"hookSpecificOutput": {"additionalContext": full_context}}))
```

```bash
# Bash example: Agent-aware SessionStart hook
HOOK_INPUT=$(cat)
AGENT_TYPE=$(echo "$HOOK_INPUT" | jq -r '.agent_type // empty')

case "$AGENT_TYPE" in
    code-reviewer|quick-query)
        echo '{"hookSpecificOutput": {"additionalContext": "Minimal context"}}'
        ;;
    *)
        echo '{"hookSpecificOutput": {"additionalContext": "Full context"}}'
        ;;
esac
```

## Hooks in Frontmatter (Claude Code 2.1.0+)

**New in 2.1.0:** Define hooks directly in skill, command, or agent frontmatter. These hooks are scoped to the component's lifecycle.

### Skill/Command/Agent Frontmatter Hooks

```yaml
---
name: validated-skill
description: Skill with lifecycle hooks
hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "./validate-command.sh"
      once: true  # NEW: Run only once per session
    - matcher: "Write|Edit"
      command: "./pre-edit-check.sh"
  PostToolUse:
    - matcher: "Write|Edit"
      command: "./format-on-save.sh"
  Stop:
    - command: "./cleanup-and-report.sh"
---
```

### The `once: true` Configuration

**New in 2.1.0:** Use `once: true` to execute a hook only once per session, ideal for:
- One-time setup/initialization
- Resource allocation that shouldn't repeat
- Session-level configuration

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "./setup-environment.sh"
      once: true  # Runs only on first Bash call
  SessionStart:
    - command: "./initialize-session.sh"
      once: true  # Runs only once at session start
```

### Frontmatter vs Settings Hooks

| Aspect | Frontmatter Hooks | Settings Hooks |
|--------|-------------------|----------------|
| Scope | Component lifecycle | Global/project |
| Location | In skill/agent/command | settings.json |
| Persistence | Active only when component runs | Always active |
| Use case | Component-specific validation | Cross-cutting concerns |

### PreToolUse updatedInput (2.1.0 Fix)

PreToolUse hooks can now return `updatedInput` when returning `ask` permission decision, enabling hooks to act as middleware while still requesting user consent:

```json
{
  "decision": "ask",
  "updatedInput": {
    "command": "modified-command --safe-flag"
  }
}
```

## Claude Code vs SDK

### JSON Hooks (Claude Code)

**Declarative configuration** in `.claude/settings.json`, project `.claude/settings.json`, or plugin `hooks/hooks.json`:

```json
{
  "PreToolUse": [
    {
      "matcher": "Edit",
      "hooks": [{
        "type": "command",
        "command": "echo 'WARNING: Editing production file' >&2"
      }]
    }
  ]
}
```

**Important**: Use string matchers (regex patterns), not object matchers. The object format `{"toolName": "Edit"}` is deprecated.

**Matcher patterns**:
- `"Edit"` - Match single tool
- `"Read|Write|Edit"` - Match multiple tools (regex OR)
- `".*"` - Match all tools

**Verification:** Run the command with `--help` flag to verify availability.

**Pros:** Simple, no code required, easy to version control
**Cons:** Limited logic capabilities, shell command only

### HTTP Hooks (Claude Code 2.1.63+)

**New in 2.1.63:** Hooks can POST JSON to a URL and receive JSON responses instead of running shell commands. Use `"type": "http"` with a `"url"` field:

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [{
        "type": "http",
        "url": "https://my-service.example.com/hooks/validate-bash"
      }]
    }
  ]
}
```

The hook POSTs the standard hook input as JSON and expects a standard hook response JSON body.

**When to use HTTP hooks over command hooks:**
- Enterprise environments where shell execution is restricted
- Centralized hook logic shared across teams via a web service
- Sandboxed or containerized setups without local script access
- Integration with external validation/logging services

**Pros:** No local scripts needed, centralized logic, works in sandboxed environments
**Cons:** Network latency, requires running HTTP service, external dependency

### Python SDK Hooks

**Programmatic callbacks** using the `AgentHooks` base class, for logic
that needs full Python, complex validation or state. The base class,
callback signatures and implementation patterns are in
`modules/sdk-callbacks.md`.

## Bash Permission Matching Notes

### Environment Variable Wrappers (2.1.38+)

Permission rules now correctly match commands prefixed with environment variable assignments. Before 2.1.38, `NODE_ENV=production npm test` would not match a rule for `Bash(npm *)`.

```
# These now all match `Bash(npm *)`:
npm test
NODE_ENV=production npm test
FORCE_COLOR=1 CI=true npm test
```

When writing PreToolUse hooks that inspect bash commands, be aware that the permission system strips env var prefixes for matching, but your hook receives the full command string including prefixes.

### Heredoc Delimiter Security (2.1.38+)

Claude Code now validates heredoc delimiters to prevent command smuggling. The recommended pattern `<<'EOF'` (single-quoted) remains the safest approach. Always use single-quoted delimiters in heredoc patterns to prevent variable expansion.

## Security Essentials

Validate tool input, never log secrets, respect sandbox boundaries,
fail safe, rate-limit and sanitize logged content. The six rules and a
secret-redacting logging hook are in `modules/security-essentials.md`.

## Performance Guidelines

Keep hooks non-blocking and fail fast. The hook timeout is 10 minutes
(increased from 60s in 2.1.3), and most hooks should finish in under
30s. Budgets, async I/O, batching, bounded state and profiling are in
`modules/performance-guidelines.md`.

## Scope Selection

Plugin hooks live in `hooks/hooks.json`, which auto-loads when the
plugin is enabled. Listing it again in `plugin.json` causes duplicate
load errors. Project hooks live in `.claude/settings.json` and
global hooks in `~/.claude/settings.json`. The decision framework is
`modules/scope-selection.md`, also served as `abstract:hook-scope-guide`.

## Common Patterns

Validation, logging, context injection and PreToolUse
`additionalContext` injection (2.1.9+) are written out in
`modules/common-patterns.md`.

## Testing Hooks

Unit-test each callback directly: assert a dangerous input raises and a
safe input returns `None`. Test categories, fixtures and the security
test checklist are in `modules/testing-hooks.md`.

## Hook Exit Codes

Hooks communicate decisions to Claude Code via exit codes:

| Exit Code | Meaning | stdout | stderr |
|-----------|---------|--------|--------|
| **0** | Success/allow | Shown to Claude as system context | Ignored |
| **2** | Block/deny | Ignored | Shown to user as explanation (2.1.39+ fix) |
| **Other** | Error | Ignored | Shown to user as error message |

### Blocking with Exit Code 2 (2.1.39+)

Use exit code 2 to block an action and display a message to the user:

```bash
#!/bin/bash
# Example: Block force pushes with user-facing message
command=$(echo "$1" | jq -r '.tool_input.command // empty')
if echo "$command" | grep -q 'push.*--force'; then
  echo "Force push blocked: use --force-with-lease instead" >&2
  exit 2
fi
exit 0
```

**Important**: Before Claude Code 2.1.39, stderr from exit code 2 was silently swallowed ([#10964](https://github.com/anthropics/claude-code/issues/10964)). Users would see a generic "hook error" instead of the custom message. This is now fixed: stderr is properly displayed to the user.

**Plugin hooks**: Before 2.1.39, plugin-installed hooks had a separate code path that also failed to show stderr for exit code 2 ([#10412](https://github.com/anthropics/claude-code/issues/10412)). Both plugin and project hooks now work correctly.

## Environment Variables (Claude Code 2.1.2+)

### `FORCE_AUTOUPDATE_PLUGINS`

Forces plugin auto-update even when the main Claude Code auto-updater is disabled.

**Use cases**:
- CI/CD pipelines that need latest plugin versions
- Development environments testing plugin updates
- Controlled update rollouts in enterprise settings

```bash
# Enable forced plugin updates
export FORCE_AUTOUPDATE_PLUGINS=1
claude

# Or inline
FORCE_AUTOUPDATE_PLUGINS=1 claude --agent my-agent
```

**Note**: This only affects plugin updates, not Claude Code core updates.

## Troubleshooting

### Common Issues

**Hook not firing**
Verify hook pattern matches the event. Check hook logs for errors

**Syntax errors**
Validate JSON/Python syntax before deployment

**Permission denied**
Check hook file permissions and ownership

**Hook blocking message not shown (pre-2.1.39)**
If using exit code 2 to block with a user-facing message and the message isn't appearing, upgrade to Claude Code 2.1.39+. In older versions, use exit 0 with stdout as a workaround.

## Module References

For detailed guidance on specific topics:

- **Hook Types**: `modules/hook-types.md` - Detailed event signatures and parameters
- **SDK Callbacks**: `modules/sdk-callbacks.md` - Python SDK implementation patterns
- **Security Essentials**: `modules/security-essentials.md` - security rules and a secret-redacting hook
- **Common Patterns**: `modules/common-patterns.md` - validation, logging and context injection hooks
- **Performance Guidelines**: `modules/performance-guidelines.md` - Optimization techniques
- **Scope Selection**: `modules/scope-selection.md` - Choosing plugin/project/global
- **Testing Hooks**: `modules/testing-hooks.md` - Testing strategies and fixtures
- **Observability Warnings**: `modules/observability-warnings.md` - Copy-pasteable resolution pattern for binary-actionable drift hooks

## Tools

- **hook_validator.py**: Validate hook structure and syntax (at
  `plugins/abstract/scripts/hook_validator.py`)

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

## Exit Criteria

- [ ] The authored hook file exists at a valid scope location (`hooks/hooks.json`,
  `.claude/settings.json`, or `~/.claude/settings.json`) with correct JSON or Python syntax.
- [ ] The hook fires on the target event: a test invocation of the matching tool call triggers
  the hook command or callback without error.
- [ ] The hook contains no secret logging: no field names matching `api[_-]?key`, `password`,
  `token`, `secret`, or `credential` appear in log output paths.
- [ ] Blocking hooks exit with code 2 and write the user-facing explanation to stderr (not stdout).
- [ ] If `abstract:validate-hook` is available, it exits 0 on the authored hook file.
