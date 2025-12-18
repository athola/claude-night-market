---
name: create-hook
description: Guided hook creation with brainstorming and security-first design. Refines hook concepts through Socratic questioning, scaffolds proper structure, and validates against security best practices. Use when creating new hooks.
usage: /create-hook [hook-description] [--skip-brainstorm] [--plugin <name>] [--event <type>]
---

# Create Hook Command

Creates new hooks through a structured workflow: **brainstorm → design → scaffold → validate**. Uses Socratic questioning to refine rough ideas into well-designed, secure hooks before generating any files.

## Usage

```bash
# Start with brainstorming (recommended)
/create-hook "detect when user shares sensitive files"

# Skip brainstorming if design is clear
/create-hook secret-detector --skip-brainstorm --event PreToolUse

# Create in specific plugin
/create-hook "auto-format on save" --plugin sanctum --event PostToolUse
```

## Hook Event Types

| Event | When It Fires | Common Use Cases |
|-------|---------------|------------------|
| `UserPromptSubmit` | User submits a prompt | Input validation, context injection |
| `PreToolUse` | Before tool execution | Security checks, blocking dangerous ops |
| `PostToolUse` | After tool completes | Logging, post-processing, notifications |
| `Notification` | Claude sends notification | Custom alerts, sound effects |
| `Stop` | Session/task ends | Cleanup, summaries, checkpoints |
| `SubagentStop` | Subagent completes | Aggregation, reporting |
| `PreCompact` | Before context compaction | Backup, preservation |
| `SessionStart` | Session begins | Context loading, initialization |

## Workflow

### Phase 0: Brainstorming (Default)

Before creating any files, refine the hook concept through collaborative dialogue.

**Invoke the brainstorming skill:**
```
Use superpowers:brainstorming to refine this hook idea before scaffolding.
```

The brainstorming phase will:

1. **Understand the purpose** - One question at a time:
   - What behavior do you want to intercept or modify?
   - Which hook event is appropriate? (present options with trade-offs)
   - Should this block, modify, or observe?
   - What data do you need from the hook payload?

2. **Explore security implications**:
   - What could go wrong if this hook misbehaves?
   - What input validation is needed?
   - Are there timeout considerations?
   - Should this hook be blocking or non-blocking?

3. **Design the implementation**:
   - JSON declarative hook vs. executable script?
   - If script: Python, Bash, or other?
   - What shared utilities might this need?
   - How will errors be handled?

4. **Validate the design** - Present in sections:
   - Hook configuration (JSON structure)
   - Script logic (if applicable)
   - Error handling approach
   - Testing strategy

5. **Document the design**:
   - Write to `docs/plans/YYYY-MM-DD-<hook-name>-design.md`
   - Include security considerations
   - Commit the design document

**Skip brainstorming** with `--skip-brainstorm` only when:
- You have a written design document already
- The hook is a simple copy of an existing pattern
- You're making a minor modification to existing hooks

### Phase 1: Gather Requirements

After brainstorming (or with `--skip-brainstorm`), the command prompts for:

1. **Hook name** (if not provided)
   - Must be kebab-case
   - Descriptive of function (e.g., `secret-detector`, `format-on-save`)
   - No generic names (`my-hook`, `test-hook`)

2. **Hook event type**:
   - One of the 8 supported events
   - Explain the choice based on timing needs

3. **Hook type**:
   - `declarative` (JSON only): Simple matchers and conditions
   - `script` (Python): Complex logic, external dependencies
   - `script` (Bash): Shell operations, simple transformations

4. **Matcher pattern** (for PreToolUse/PostToolUse):
   - Tool name regex (e.g., `Read|Write|Edit`)
   - Leave empty for all tools

5. **Timeout** (for scripts):
   - Default: 10 seconds
   - Maximum: 60 seconds (with justification)

### Phase 2: Security Review

Before scaffolding, validate security considerations:

```
Security Checklist:
  [ ] Input validation for all payload fields
  [ ] No shell injection vulnerabilities
  [ ] No path traversal vulnerabilities
  [ ] Timeout configured appropriately
  [ ] Error handling doesn't leak secrets
  [ ] Logging doesn't capture sensitive data
```

### Phase 3: Create Hook Structure

**For declarative hooks:**
```bash
hooks/
├── hooks.json           # Add hook configuration
└── ${hook_name}.json    # Or inline in hooks.json
```

**For script hooks:**
```bash
hooks/
├── hooks.json           # Hook registration
├── ${hook_name}.py      # Main hook script
└── shared/              # Optional shared utilities
    ├── __init__.py
    └── ${utility}.py
```

### Phase 4: Generate Hook Files

**hooks.json entry:**
```json
{
  "${EventType}": [
    {
      "matcher": "${matcher_pattern}",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/hooks/${hook_name}.py",
          "timeout": ${timeout}
        }
      ]
    }
  ]
}
```

**Python hook template:**
```python
#!/usr/bin/env python3
"""${hook_name} hook for ${EventType}.

${description}
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def main() -> None:
    """Main hook entry point."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input, exit silently

    # Fast path checks
    ${fast_path_logic}

    # Main logic (lazy imports for slow path)
    ${main_logic}

    # Output response (if modifying behavior)
    response = {
        "hookSpecificOutput": {
            "hookEventName": "${EventType}",
            "additionalContext": "${context_message}"
        }
    }
    print(json.dumps(response))
    sys.exit(0)


if __name__ == '__main__':
    main()
```

### Phase 5: Initial Validation

Runs security and compliance checks:

```bash
# Validate hook structure
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hooks_eval/hook_analyzer.py \
  hooks/${hook_name}.py --security-scan

# Check for common issues
/analyze-hook hooks/${hook_name}.py --compliance-check
```

Output:
```
Validation Results:
  OK Hook structure valid
  OK Security checks passed
  OK Timeout configured
  [WARN] Consider adding unit tests

Status: READY FOR TESTING
```

### Phase 6: Testing Guide

Provides testing instructions:

```
OK Hook scaffolding complete: hooks/${hook_name}.py

Next Steps:

1. MANUAL TESTING
   - Test with sample payload:
     echo '{"tool_name": "Read", ...}' | python3 hooks/${hook_name}.py
   - Verify expected output/behavior

2. UNIT TESTS
   - Create tests/hooks/test_${hook_name}.py
   - Test fast path (no-op cases)
   - Test main logic paths
   - Test error handling

3. INTEGRATION TESTING
   - Reload Claude Code to pick up new hook
   - Trigger the hook event manually
   - Verify hook executes correctly

4. SECURITY AUDIT
   - Run: /analyze-hook hooks/${hook_name}.py --security-scan
   - Address any findings before deployment
```

## Examples

### Example 1: UserPromptSubmit Hook

```bash
/create-hook "warn when user mentions production deployment"

Creating hook: deployment-warner
Event: UserPromptSubmit
Type: Python script

Brainstorming questions:
  Q: What keywords indicate production deployment?
  A: "deploy to prod", "production release", "push to main"

  Q: Should this block or just warn?
  A: Warn only - add context message

Created:
  OK hooks/deployment-warner.py (45 lines)
  OK hooks/hooks.json (updated)
  OK tests/hooks/test_deployment_warner.py

Security: PASSED
Next: Test manually, then reload Claude Code
```

### Example 2: PostToolUse Hook with Shared Utilities

```bash
/create-hook "track all file modifications for audit log" --event PostToolUse

Creating hook: file-audit-logger
Event: PostToolUse
Matcher: Write|Edit|NotebookEdit
Type: Python script

Design decisions:
  - Uses shared/audit_utils.py for logging
  - Writes to ~/.claude/audit/file-changes.jsonl
  - Non-blocking (fire and forget)

Created:
  OK hooks/file-audit-logger.py (78 lines)
  OK hooks/shared/audit_utils.py (42 lines)
  OK hooks/hooks.json (updated)

Security: PASSED (1 warning about log rotation)
```

### Example 3: Declarative Hook

```bash
/create-hook "simple tool matcher" --skip-brainstorm --event PreToolUse

Creating hook: tool-matcher
Event: PreToolUse
Type: Declarative (JSON only)

Created:
  OK hooks/hooks.json (updated with inline config)

No script needed - pure JSON configuration
```

## Security Requirements

All hooks MUST:

1. **Validate all inputs** - Never trust payload data
2. **Use timeouts** - Prevent hanging operations
3. **Handle errors gracefully** - Exit cleanly, don't crash Claude
4. **Avoid shell injection** - Never pass unsanitized input to shell
5. **Protect secrets** - Don't log sensitive data
6. **Use safe file operations** - Validate paths, use atomic writes

## Integration with Existing Infrastructure

This command integrates with:

- `hooks/shared/` - Reusable utilities (see memory-palace hooks for example)
- `/analyze-hook` - Security and compliance scanning
- `/hooks-eval` - Full plugin hook evaluation
- `/validate-plugin` - Overall plugin validation

## Implementation

```bash
# Interactive creation workflow
# Uses brainstorming skill, then scaffolds based on responses

# If --skip-brainstorm:
# Direct scaffolding with prompts for required fields
```

## See Also

- `/analyze-hook` - Security and performance analysis
- `/hooks-eval` - Comprehensive hook evaluation
- `/validate-plugin` - Plugin structure validation
- `/create-skill` - Similar workflow for skills
- `skills/hook-authoring/SKILL.md` - Hook development best practices
