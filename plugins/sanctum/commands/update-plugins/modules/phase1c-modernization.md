# Phase 1c: Modernization Audit

Detect outdated hook patterns after registration sync.
Runs automatically unless `--skip-modernization` is passed.

## Static Pattern Check (always runs)

Run the modernization checker script:

```bash
python3 scripts/check_hook_modernization.py
```

For JSON output (programmatic):

```bash
python3 scripts/check_hook_modernization.py --json
```

### Patterns Detected

| Pattern | Severity | Description |
|---------|----------|-------------|
| `invalid-post-decision` | error | PostToolUse using `"ALLOW"` or `"approve"` instead of `"block"` or omitting |
| `deprecated-pre-decision` | warning | PreToolUse using `"decision"`/`"reason"` instead of `hookSpecificOutput.permissionDecision` |
| `missing-stdin-error-handling` | warning | Hook reads stdin without try/except for JSONDecodeError |
| `noisy-no-op` | warning | PostToolUse prints stdout on no-op paths (silent exit is preferred) |

### Interpreting Results

- **Errors** block the workflow. Fix before proceeding.
- **Warnings** are informational. Review and fix when convenient.

### Fixing Common Issues

**invalid-post-decision**: Replace `{"decision": "ALLOW"}` with `{}`
(empty dict). PostToolUse hooks signal "allow" by omitting the
decision field entirely, or by producing no stdout.

**deprecated-pre-decision**: Replace top-level `"decision"` and
`"reason"` with nested `hookSpecificOutput`:

```python
# Before (deprecated):
{"decision": "approve", "reason": "safe"}

# After (current):
{"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "safe",
}}
```

**missing-stdin-error-handling**: Wrap stdin reads:

```python
try:
    data = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    sys.exit(0)
```

## Tome Research Audit (runs by default)

After the static check, dispatch a tome:code-search agent
to verify hook patterns against current community practices.

### When to Run

- Default: runs on every `/update-plugins` invocation
- Skip with: `--skip-research`
- Useful after Claude Code SDK updates to catch new patterns

### Workflow

1. Collect the list of hook event types used in the project
2. Dispatch `tome:code-search` agent with query:
   ```
   Claude Code plugin hooks PostToolUse PreToolUse
   hookSpecificOutput best practices 2025 2026
   ```
3. Compare findings against local hook implementations
4. Report any modernization gaps not caught by static checks

### Agent Dispatch

```
Agent(tome:code-searcher)
Prompt: Search GitHub for current Claude Code plugin hook
patterns. Focus on PostToolUse and PreToolUse response
formats, hookSpecificOutput usage, and deprecated patterns.
Return structured findings with repo URLs and code snippets.
```

### Output

The agent returns findings in this structure:

```json
{
  "findings": [
    {
      "repo": "owner/repo",
      "pattern": "description of pattern",
      "relevance": "high|medium|low",
      "url": "https://github.com/..."
    }
  ]
}
```

Cross-reference against local hooks to identify gaps.
