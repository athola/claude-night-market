# Hook Reference

Hooks let you run scripts at specific lifecycle events (session start, before/after tool calls, session end). They're registered in YAML configuration and implemented in Bash or Python. Common uses: injecting context, caching web results, logging for observability, and enforcing policies.

**See also**: [Capabilities Reference](capabilities-reference.md) | [Commands](capabilities-commands.md) | [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Workflows](capabilities-workflows.md)

---

## Hook Event Types

| Event | Trigger | Use Cases |
|-------|---------|-----------|
| `SessionStart` | Session begins | Initialize state, load config |
| `UserPromptSubmit` | User sends message | Validate input, add context |
| `PreToolUse` | Before tool executes | Intercept, validate, inject context (2.1.9+) |
| `PostToolUse` | After tool completes | Process results, cache |
| `Stop` | Session ends | Cleanup, summarize, notify |

### Hook Output Capabilities

| Hook Type | additionalContext | Permission Control | Input Modification |
|-----------|-------------------|-------------------|-------------------|
| SessionStart | Yes | No | No |
| UserPromptSubmit | Yes | No | No |
| PreToolUse | Yes (2.1.9+) | Yes (allow/deny/ask) | Yes (updatedInput) |
| PostToolUse | Yes | No | No |
| Stop | Yes | No | No |

---

## Hook Configuration (YAML)

```yaml
# Hook registration in settings.json or hook config
hooks:
  PreToolUse:
    - matcher: "WebFetch|WebSearch"
      command: "python3 hooks/cache_lookup.py"
      timeout: 5000
  PostToolUse:
    - matcher: "Bash"
      command: "echo 'Bash executed'"
  SessionStart:
    - command: "bash hooks/init.sh"
  Stop:
    - command: "python3 hooks/cleanup.py"
```

---

## Implementation Patterns

### Bash Hook

```bash
#!/bin/bash
# hooks/session-start.sh
# SessionStart hook - initialize session state

# Read environment
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TMPDIR="${CLAUDE_CODE_TMPDIR:-/tmp}"

# Initialize session log
echo "[session-start] Session $SESSION_ID started at $(date)" >> "$TMPDIR/session.log"

# Output context (optional)
cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Session initialized with logging enabled"
  }
}
EOF
```

### Python Hook (PostToolUse)

```python
#!/usr/bin/env python3
"""PostToolUse hook for processing web content."""

import json
import sys
from pathlib import Path

def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    tool_response = payload.get("tool_response", {})

    # Fast path: not our target tool
    if tool_name != "WebFetch":
        sys.exit(0)

    # Process the response
    url = tool_input.get("url", "")
    content = tool_response.get("content", "")

    # Generate context
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"Processed content from {url} ({len(content)} chars)"
        }
    }

    print(json.dumps(response))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Python Hook (PreToolUse with Context Injection - 2.1.9+)

```python
#!/usr/bin/env python3
"""PreToolUse hook that injects context before tool execution."""

import json
import sys

def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Example: inject cached knowledge before WebFetch
    if tool_name == "WebFetch":
        url = tool_input.get("url", "")

        # Check if we have cached info about this URL
        cached_info = lookup_cache(url)  # Your cache logic

        if cached_info:
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": f"Cached info for {url}: {cached_info}"
                }
            }
            print(json.dumps(response))

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## Memory Palace Hooks

### `web_content_processor.py`
**Type**: PostToolUse
**Matcher**: `WebFetch|WebSearch`

Processes fetched web content for knowledge intake.

**Configuration** (`memory-palace-config.yaml`):
```yaml
enabled: true
research_mode: cache_first  # cache_only|cache_first|augment|web_only
feature_flags:
  auto_capture: true       # Auto-store to queue
  cache_intercept: true    # Enable cache lookup
safety:
  max_content_size_kb: 500
  detect_repetition_bombs: true
```

### `research_interceptor.py`
**Type**: PreToolUse
**Matcher**: `WebFetch|WebSearch`
**Uses additionalContext**: Yes (2.1.9+)

Checks knowledge corpus before web requests. Injects cached knowledge as visible context before tool execution.

**Modes**: `cache_only` blocks all web requests; `cache_first` checks the corpus then hits the web if nothing matches; `augment` always mixes corpus context into web responses.

### `url_detector.py`
**Type**: UserPromptSubmit

Detects URLs in user prompts for processing.

### `local_doc_processor.py`
**Type**: PostToolUse

Processes local documentation files.

---

## Conserve Hooks

### `context_warning.py`
**Type**: SessionStart

Monitors context utilization and warns at thresholds.

### `permission_request.py`
**Type**: PreToolUse

Automates permission decisions based on patterns.

---

## Sanctum Hooks

### `post_implementation_policy.py`
**Type**: SessionStart

Enforces documentation/test update requirements.

### `session_complete_notify.py`
**Type**: Stop

Sends completion notifications.

### `verify_workflow_complete.py`
**Type**: Stop

Verifies workflow completion before session end.

### `security_pattern_check.py`
**Type**: PreToolUse
**Matcher**: `Edit|Write|MultiEdit`
**Uses additionalContext**: Yes (2.1.9+)

Checks for security anti-patterns in code changes. Injects security warnings as visible context when risky patterns detected. Context-aware: distinguishes actual code from documentation examples.

### `stop_combined.py`
**Type**: Stop

Consolidated Stop hooks for performance.

---

## Abstract Hooks

### `skill_execution_logger.py`
**Type**: PostToolUse
**Matcher**: `Skill`

Logs skill executions for metrics.

### `pre_skill_execution.py`
**Type**: PreToolUse
**Matcher**: `Skill`
**Uses additionalContext**: Yes (2.1.9+)

Tracks skill executions and injects skill context before execution. Creates state files for PostToolUse duration calculation.

---

## Imbue Hooks

### `session-start.sh`
**Type**: SessionStart

Session initialization with scope metrics.

### `user-prompt-submit.sh`
**Type**: UserPromptSubmit

Scope validation on user input.

---

**See also**: [Commands](capabilities-commands.md) | [Skills](capabilities-skills.md) | [Agents](capabilities-agents.md) | [Workflows](capabilities-workflows.md)
