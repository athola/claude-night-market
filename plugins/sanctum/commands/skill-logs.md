# Skill Logs

Surface recent skill execution failures and patterns from memory-palace logs.

## Arguments

- `--plugin <name>` - Filter logs for a specific plugin
- `--skill <name>` - Filter logs for a specific skill
- `--failures-only` - Show only failed executions
- `--last <duration>` - Time window (e.g., "7d", "24h", "30d")
- `--format <type>` - Output format: "summary", "detailed", "json"

## What It Does

1. **Queries skill execution logs** from memory-palace knowledge base
2. **Filters by criteria** (plugin, skill, time window, status)
3. **Extracts patterns** from failures:
   - Common error messages
   - Environmental dependencies
   - Recurring failure conditions
4. **Generates actionable insights** for remediation

## Workflow

### Basic Usage

```bash
# View recent failures for a plugin
/skill-logs --plugin conserve --failures-only --last 7d

# View all execution history for a skill
/skill-logs --skill bloat-detector --last 30d

# Get detailed failure analysis
/skill-logs --failures-only --last 7d --format detailed
```

### Manual Log Analysis

If automated tooling isn't available, check these sources:

#### Step 1: Check Git History for Fixes

Recent fixes often indicate previous failures:

```bash
git log --oneline --grep="fix" --since="30 days ago" -- plugins/<plugin>/skills/
```

#### Step 2: Check Issue Tracker

```bash
gh issue list --label "skill" --state all --limit 20
```

#### Step 3: Search for Error Patterns

```bash
# Search for TODO/FIXME in skills
grep -r "TODO\|FIXME\|BUG" plugins/<plugin>/skills/
```

### Log Entry Format

When logging skill executions (for memory-palace integration):

```yaml
skill_execution:
  timestamp: "2024-01-17T10:30:00Z"
  skill: "conserve:bloat-detector"
  status: "success|failure|partial"
  duration_ms: 1234
  tokens_used: 850
  error_message: null  # or error string
  context:
    trigger: "manual|auto|hook"
    session_id: "abc123"
```

### Failure Categories

| Category | Description | Common Causes |
|----------|-------------|---------------|
| **Parse Error** | Skill failed to load | Invalid frontmatter, syntax errors |
| **Tool Error** | Required tool unavailable | MCP not configured, missing dependency |
| **Timeout** | Execution exceeded limit | Large codebase, slow operations |
| **Logic Error** | Wrong output produced | Bug in skill logic |
| **Environment** | Missing prerequisites | Wrong directory, missing files |

## Output Format

### Summary Format (default)

```
## Skill Execution Logs: conserve (last 7 days)

### Overview
- Total executions: 45
- Successes: 42 (93%)
- Failures: 3 (7%)

### Recent Failures

| Timestamp | Skill | Error |
|-----------|-------|-------|
| 2024-01-15 14:30 | bloat-detector | FileNotFoundError: pyproject.toml |
| 2024-01-14 09:15 | context-optimization | Timeout after 30s |
| 2024-01-12 16:45 | bloat-detector | ModuleNotFoundError: ast |

### Patterns Detected
- bloat-detector: 2 failures - missing project files
- context-optimization: 1 failure - performance issue
```

### Detailed Format

Includes full error traces and context for debugging.

### JSON Format

Machine-readable output for integration with other tools.

## Integration

This command is invoked automatically by `/update-plugins` Phase 2.

Related commands:
- `pensive:skill-review` - Analyze runtime metrics and stability
- `abstract:skill-auditor` - Deep skill quality analysis
- `/update-plugins` - Full plugin registration audit
- `memory-palace:knowledge-capture` - Log skill executions

## Future Enhancements

When memory-palace logging is fully integrated:
- Automatic execution logging via hooks
- Trend analysis over time
- Alerting for degrading skills
- Performance benchmarking

## See Also

- `memory-palace:auto-capture` - Automatic knowledge logging
- `imbue:proof-of-work` - Evidence logging framework
