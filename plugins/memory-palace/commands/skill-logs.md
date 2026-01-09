# Skill Execution Logs

View and manage skill execution memories stored by memory-palace.

## Usage

```bash
/skill-logs                           # Show recent skill executions
/skill-logs --plugin <name>           # Filter by plugin
/skill-logs --skill <plugin:skill>    # Filter by specific skill
/skill-logs --last <duration>         # Time window (1h, 24h, 7d)
/skill-logs --failures-only           # Only failures
/skill-logs --format json             # JSON output
/skill-logs cleanup --older-than 90d  # Remove old logs
```

## Examples

### Recent Executions

```bash
/skill-logs --last 1h
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

### By Plugin

```bash
/skill-logs --plugin abstract --last 24h
```

### Failures Only

```bash
/skill-logs --failures-only --last 24h
```

Output:
```
Recent Failures (Last 24 Hours)
================================

2025-01-08 14:28:15  imbue:proof-of-work
  Error: Missing PROOF.md file
  Suggestion: Run /pensive:skill-review --skill imbue:proof-of-work

2025-01-08 12:15:42  your-custom:my-skill
  Error: Failed to connect to database
  Suggestion: Check database connection string
```

### JSON Export

```bash
/skill-logs --format json --last 1h | jq
```

### Cleanup Old Logs

```bash
# Remove logs older than 90 days
/skill-logs cleanup --older-than 90d

# Preview what would be removed
/skill-logs cleanup --older-than 90d --dry-run
```

## Storage Structure

Skill execution memories are stored in:

```
~/.claude/skills/logs/
├── .history.json              # Aggregated continual metrics
├── abstract/
│   ├── skill-auditor/
│   │   └── 2025-01-08.jsonl   # Daily log files (JSONL format)
│   └── plugin-validator/
│       └── 2025-01-08.jsonl
├── sanctum/
│   └── pr-review/
│       └── 2025-01-08.jsonl
└── <your-plugin>/
    └── <your-skill>/
        └── YYYY-MM-DD.jsonl
```

## Integration

Skill execution tracking is automatic via memory-palace hooks:
- **PreToolUse**: Records start time when `Skill` tool is invoked
- **PostToolUse**: Logs completion, calculates metrics, stores memory

Use `/pensive:skill-review` to analyze metrics and identify unstable skills.

## What It Does

1. **Reads JSONL logs**: Parses skill execution memories
2. **Filters by criteria**: Plugin, skill, time, outcome
3. **Formats output**: Markdown tables or JSON
4. **Manages storage**: Cleanup old logs to save disk space
