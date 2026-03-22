# Hook Reference

Hooks let you run scripts at specific lifecycle events (session start,
before/after tool calls, session end).
They're registered in YAML configuration and implemented in Bash or Python.
Common uses: injecting context, caching web results, logging for observability,
and enforcing policies.

**See also**: [Capabilities Reference][cap-ref] |
[Commands][cap-cmd] | [Skills][cap-skills] |
[Agents][cap-agents] | [Workflows][cap-wf]

---

## Hook Event Types

| Event | Trigger | Version | Use Cases |
|-------|---------|---------|-----------|
| `Setup` | Plugin installed/enabled | 2.1.0+ | One-time initialization |
| `SessionStart` | Session begins | 2.1.0+ | Initialize state, load config |
| `SessionEnd` | Session ends normally | 2.1.0+ | Cleanup, persist state |
| `UserPromptSubmit` | User sends message | 2.1.0+ | Validate input, add context |
| `PreToolUse` | Before tool executes | 2.1.0+ | Intercept, validate, inject context (2.1.9+) |
| `PostToolUse` | After tool completes | 2.1.0+ | Process results, cache |
| `PostToolUseFailure` | Tool execution fails | 2.1.20+ | Error handling, fallback logic |
| `PermissionRequest` | Permission prompt shown | 2.1.0+ | Auto-approve/deny patterns |
| `Notification` | System notification | 2.1.20+ | Forward alerts, log events |
| `SubagentStart` | Subagent spawned | 2.1.20+ | Track agent lifecycle |
| `SubagentStop` | Subagent finishes | 2.1.20+ | Collect results, cleanup |
| `Stop` | Session ends | 2.1.0+ | Cleanup, summarize, notify |
| `TeammateIdle` | Teammate agent idle | 2.1.33+ | Multi-agent coordination |
| `TaskCompleted` | Task finishes | 2.1.33+ | Multi-agent coordination |
| `ConfigChange` | Config modified | 2.1.49+ | React to settings changes |
| `InstructionsLoaded` | Instructions loaded | 2.1.33+ | Augment instructions |
| `PreCompact` | Before context compact | 2.1.20+ | Preserve critical context |
| `WorktreeCreate` | Git worktree created | 2.1.50+ | Initialize worktree state |
| `WorktreeRemove` | Git worktree removed | 2.1.50+ | Cleanup worktree state |

### Hook Output Capabilities

| Hook Type | additionalContext | Permission Control | Input Modification | Notes |
|-----------|-------------------|-------------------|-------------------|-------|
| Setup | Yes | No | No | |
| SessionStart | Yes | No | No | |
| SessionEnd | Yes | No | No | |
| UserPromptSubmit | Yes | No | No | |
| PreToolUse | Yes (2.1.9+) | Yes (allow/deny/ask) | Yes (updatedInput) | |
| PostToolUse | Yes | No | No | |
| PostToolUseFailure | Yes | No | No | |
| PermissionRequest | Yes | Yes (allow/deny) | No | |
| Notification | No | No | No | |
| SubagentStart | Yes | No | No | |
| SubagentStop | Yes | No | No | |
| Stop | Yes | No | No | |
| TeammateIdle | Yes | No | No | |
| TaskCompleted | Yes | No | No | |
| ConfigChange | Yes | No | No | |
| InstructionsLoaded | Yes | No | No | |
| PreCompact | Yes | No | Yes (summary) | |
| WorktreeCreate | Yes | No | No | command-only, stdout = worktree path |
| WorktreeRemove | Yes | No | No | command-only, cannot block removal |

### Hook Event Field Enrichment (2.1.69+)

All hook events now include `agent_id` (for subagent
sessions) and `agent_type` (for subagent and `--agent`
sessions) in the input JSON. Status line hook commands
gain a `worktree` field with `name`, `path`, `branch`,
and `originalRepoDir` in worktree sessions.

`TeammateIdle` and `TaskCompleted` hooks now support
returning `{"continue": false, "stopReason": "..."}` to
stop a teammate, matching `Stop` hook behavior.

Plugin-registered `WorktreeCreate` and `WorktreeRemove`
hooks were silently ignored before 2.1.69 and now fire
correctly.

### Cron Scheduling Tools (2.1.71+)

Three new built-in tools for session-scoped scheduled
tasks: `CronCreate`, `CronList`, `CronDelete`. These
appear as tool names in `PreToolUse`/`PostToolUse`
events. The `/loop` command uses `CronCreate`
internally. Sessions can hold up to 50 scheduled tasks.
Disable with `CLAUDE_CODE_DISABLE_CRON=1`.

### Bash Allowlist and Heredoc Fixes (2.1.71+)

Added `fmt`, `comm`, `cmp`, `numfmt`, `expr`, `test`,
`printf`, `getconf`, `seq`, `tsort`, `pr` to the bash
auto-approval allowlist. These no longer trigger
`PermissionRequest` events.

Compound bash commands containing heredoc commit
messages no longer trigger false-positive permission
prompts.

### HTTP Hooks (2.1.63+)

Hooks can POST JSON to a URL instead of running shell
commands. Use `"type": "http"` with a `"url"` field in
the hook configuration. The standard hook input is sent
as the POST body and the response must be standard hook
JSON. This enables hook integrations in environments
where shell execution is restricted.

### Security: Workspace Trust (2.1.51+)

Hook commands that emit `statusLine` or `fileSuggestion`
now require workspace trust acceptance in interactive
mode. Untrusted hooks cannot execute these output types
until the user accepts workspace trust for the project.

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
    - command: "python3 hooks/session_cleanup.py"
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

## Worktree Hooks (2.1.50+)

WorktreeCreate and WorktreeRemove are command-only hooks.
They have no Python SDK callback support and do not
support matchers.

**WorktreeCreate** must print the absolute path to the
created worktree directory on stdout. If the hook fails
or produces no output, worktree creation fails.

```bash
#!/bin/bash
# hooks/worktree-create.sh
# WorktreeCreate hook - receives JSON on stdin
INPUT=$(cat)
NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])")
WORKTREE_DIR="/tmp/worktrees/$NAME"
mkdir -p "$WORKTREE_DIR"
echo "$WORKTREE_DIR"
```

**WorktreeRemove** receives `worktree_path` in its input
and fires for cleanup purposes (removing VCS state,
archiving changes). It cannot block the removal.

```bash
#!/bin/bash
# hooks/worktree-remove.sh
# WorktreeRemove hook - cleanup after worktree removal
INPUT=$(cat)
WORKTREE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['worktree_path'])")
# Archive any uncommitted changes, remove temp state, etc.
rm -rf "$WORKTREE_PATH/.session-state" 2>/dev/null
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

Checks knowledge corpus before web requests.
Injects cached knowledge as visible context before tool execution.

**Modes**: `cache_only` blocks all web requests;
`cache_first` checks the corpus then hits the web if nothing matches;
`augment` always mixes corpus context into web responses.

### `url_detector.py`
**Type**: UserPromptSubmit

Detects URLs in user prompts for processing.

### `local_doc_processor.py`
**Type**: PostToolUse
**Matcher**: `Read`

Processes local documentation files.

### `skill_tracker_pre.py`
**Type**: PreToolUse
**Matcher**: `Skill`

Tracks skill execution start for metrics collection.

### `skill_tracker_post.py`
**Type**: PostToolUse
**Matcher**: `Skill`

Records skill execution completion and metrics.

---

## Conserve Hooks

### `context_warning.py`
**Type**: PreToolUse
**Matcher**: `.*`

Monitors context utilization and alerts at thresholds.
At EMERGENCY (80%+), directs Claude to delegate via
`Skill(conserve:clear-context)`
and a continuation agent rather than wrapping up.
Uses tail-based JSONL parsing to avoid false alerts from compressed history.

### `permission_request.py`
**Type**: PermissionRequest

Automates permission decisions based on safe/dangerous
command patterns.
Rejects commands containing shell chaining metacharacters
(`;`, `|`, `&&`, backticks, `$()`) even when the prefix
matches a safe pattern, preventing auto-approval of
payloads like `ls; rm -rf /`.

### `session-start.sh`
**Type**: SessionStart

Session initialization with context optimization.

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

### `session_complete_notify.py`
**Type**: Stop

Cross-platform toast notifications when Claude awaits input.
Supports Linux (notify-send), macOS (osascript), Windows (PowerShell), and WSL.
Shows terminal context (Zellij, tmux, project name).
Non-blocking background execution. Disable with `CLAUDE_NO_NOTIFICATIONS=1`.

### `security_pattern_check.py`
**Type**: PreToolUse
**Matcher**: `Edit|Write|MultiEdit`
**Uses additionalContext**: Yes (2.1.9+)

Checks for security anti-patterns in code changes.
Injects security warnings as visible context when risky patterns detected.
Context-aware: distinguishes actual code from documentation examples.

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

Tracks skill executions and injects skill context before execution.
Creates state files for PostToolUse duration calculation.

---

## Leyline Hooks

### `detect-git-platform.sh`
**Type**: SessionStart

Detects the git hosting platform (GitHub, GitLab,
Bitbucket) and sets session context variables used by downstream skills
and hooks.

### `fetch-recent-discussions.sh`
**Type**: SessionStart
**Timeout**: 3 seconds

Queries the 5 most recent "Decisions" discussions from GitHub Discussions
and injects a summary into session context.
Enables cross-session discovery of prior deliberations.
Skips silently when `gh` CLI is unavailable, unauthenticated,
or the repository lacks Discussions. Token budget: <600 tokens.

---

## Imbue Hooks

### `session-start.sh`
**Type**: SessionStart

Session initialization with scope metrics.

### `user-prompt-submit.sh`
**Type**: UserPromptSubmit

Scope validation on user input.

---

**See also**: [Commands][cap-cmd] |
[Skills][cap-skills] | [Agents][cap-agents] |
[Workflows][cap-wf]

[cap-ref]: capabilities-reference.md
[cap-cmd]: capabilities-commands.md
[cap-cmd-ext]: capabilities-commands-extended.md
[cap-skills]: capabilities-skills.md
[cap-agents]: capabilities-agents.md
[cap-hooks]: capabilities-hooks.md
[cap-wf]: capabilities-workflows.md
