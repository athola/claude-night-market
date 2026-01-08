# View Execution History

View recent skill executions with full details.

## Usage

```bash
/observability:history                      # Recent executions (last 50)
/observability:history --plugin <name>       # Filter by plugin
/observability:history --skill <name>        # Filter by skill
/observability:history --last <duration>     # Time window (1h, 24h, 7d)
/observability:history --failures-only       # Only failures
/observability:history --format json         # JSON output
```

## Examples

### Recent Executions

```bash
/observability:history --last 1h
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
/observability:history --failures-only --last 24h
```

Output:
```
Recent Failures (Last 24 Hours)
================================

2025-01-08 14:28:15  imbue:proof-of-work
  Error: Missing PROOF.md file
  Suggestion: Run /abstract:improve-skills --skill imbue:proof-of-work

2025-01-08 12:15:42  your-custom:my-skill
  Error: Failed to connect to database
  Suggestion: Check database connection string

2025-01-08 09:45:18  sanctum:pr-agent
  Error: Repository not found
  Suggestion: Verify repository URL
```

### JSON Output

```bash
/observability:history --format json --last 1h | jq
```

## Implementation

Reads from: `~/.claude/skills/logs/*/*/*.jsonl`

Parses JSONL files and formats output.
