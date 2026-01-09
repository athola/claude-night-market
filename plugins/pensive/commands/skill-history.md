# Skill Execution History

View recent skill executions with full context and error details for review.

## Usage

```bash
/skill-history                          # Recent executions (last 50)
/skill-history --plugin <name>          # Filter by plugin
/skill-history --skill <plugin:skill>   # Filter by skill
/skill-history --last <duration>        # Time window (1h, 24h, 7d)
/skill-history --failures-only          # Only failures
/skill-history --context                # Include full context
/skill-history --format json            # JSON output
```

## Examples

### Recent Executions

```bash
/skill-history --last 1h
```

Output:
```
Recent Skill Executions (Last Hour)
===================================

2025-01-08 14:32:15  abstract:skill-auditor      ✓  137ms
2025-01-08 14:30:42  sanctum:pr-review          ✓  2.1s
2025-01-08 14:28:15  imbue:proof-of-work       ✗  1.9s  Error: Missing PROOF.md
2025-01-08 14:25:33  abstract:plugin-validator  ✓  89ms
2025-01-08 14:22:10  memory-palace:knowledge-intake ✓  450ms
```

### Failures Only

```bash
/skill-history --failures-only --last 24h
```

Output:
```
Recent Failures (Last 24 Hours)
================================

2025-01-08 14:28:15  imbue:proof-of-work
  Duration: 1.9s
  Error: Missing PROOF.md file
  Session: abc123

  Context:
    Tool input: {"skill": "imbue:proof-of-work", "args": {"path": "/project"}}
    Output preview: "Error: Required file PROOF.md not found in project root..."

  Recommendation:
    - Check that PROOF.md exists before invoking
    - See /skill-review --skill imbue:proof-of-work for stability analysis

---

2025-01-08 12:15:42  your-custom:my-skill
  Duration: 3.2s
  Error: Failed to connect to database
  Session: def456

  Context:
    Tool input: {"skill": "your-custom:my-skill", "args": {"query": "SELECT..."}}
    Output preview: "ConnectionError: Unable to establish connection..."

  Recommendation:
    - Verify database connection string
    - Check network connectivity
```

### Full Context Mode

```bash
/skill-history --skill abstract:skill-auditor --context --last 24h
```

Shows complete tool input/output for debugging.

### JSON Output

```bash
/skill-history --format json --last 1h | jq '.[] | select(.outcome == "failure")'
```

## What It Shows

### Per Execution

| Field | Description |
|-------|-------------|
| **Timestamp** | When the skill was invoked |
| **Skill** | Plugin:skill reference |
| **Outcome** | ✓ success, ✗ failure, ⚠ partial |
| **Duration** | Execution time |
| **Error** | Error message (if failed) |
| **Session** | Claude session ID |
| **Context** | Tool input and output preview |

### Filtering

- **By plugin**: Show only skills from one plugin
- **By skill**: Focus on specific skill
- **By time**: Recent executions only
- **By outcome**: Failures, successes, or all

## Integration

### Data Source

Reads from execution logs stored by memory-palace:
- **Location**: `~/.claude/skills/logs/<plugin>/<skill>/YYYY-MM-DD.jsonl`
- **Format**: One JSON object per line (JSONL)

### Related Commands

| Command | Focus | Use When |
|---------|-------|----------|
| `/skill-history` | Recent executions | Debugging a specific failure |
| `/skill-review` | Metrics & stability | Understanding overall health |
| `/skill-logs` | Raw log access | Data export or cleanup |

## Use Cases

### Debugging a Failure

```bash
# 1. See recent failures
/skill-history --failures-only --last 1h

# 2. Get full context for the problematic skill
/skill-history --skill imbue:proof-of-work --context

# 3. Check if it's a pattern
/skill-review --skill imbue:proof-of-work
```

### Understanding Usage Patterns

```bash
# What skills are being used most?
/skill-history --last 7d --format json | jq 'group_by(.skill) | map({skill: .[0].skill, count: length}) | sort_by(-.count)'
```

### Session Reconstruction

```bash
# What skills ran in a specific session?
/skill-history --format json | jq 'select(.context.session_id == "abc123")'
```

## Performance

- Scans JSONL files by date to minimize I/O
- Limits output to prevent context overflow
- Use `--last` to narrow time range for faster results
