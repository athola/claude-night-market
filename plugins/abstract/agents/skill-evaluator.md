---
name: skill-evaluator
model: sonnet
agent: true
allowed-tools:
  - Read
  - Write
  - Grep
  - Bash
escalation: opus-when-stuck
context: fork
---

# Skill Execution Evaluator

Facilitates human-in-loop qualitative evaluation of skill executions.

## Purpose

Part of the skill observability infrastructure (Issue #69 Phase 2), this agent helps capture qualitative feedback about skill effectiveness that cannot be detected programmatically.

## Inputs

- **skill_name**: Skill to evaluate (format: `plugin:skill-name`)
- **mode**: `recent` (default), `all`, or `date`
- **date**: Specific date to evaluate (YYYY-MM-DD format)
- **batch**: Boolean - evaluate multiple executions interactively

## Workflow

### 1. Load Execution Logs

```python
# Read from ~/.claude/skills/logs/<plugin>/<skill>/
# Parse JSONL files
# Filter for unevaluated entries (qualitative_evaluation == null)
```

### 2. Present Execution Summary

For each unevaluated execution, show:
- Timestamp (human-readable)
- Duration (ms → seconds conversion)
- Outcome (success/failure/partial)
- Context preview (first 200 chars of output)
- Session information

### 3. Collect Evaluation

Prompt user with structured questions:

**Q1: Effectiveness Rating (1-5)**
```
How effective was this skill execution?
5 - Exceptional (exceeded expectations)
4 - Effective (achieved goal with minor friction)
3 - Adequate (worked but had inefficiencies)
2 - Poor (partial failure or workarounds needed)
1 - Failed (did not achieve intended outcome)

Rating: _
```

**Q2: Friction Points** (optional, multi-line)
```
What friction did you encounter? (Press Enter twice to finish)
Examples:
- Missing information about X
- Unclear instructions for Y
- Excessive token usage
- Outdated guidance

Friction: _
```

**Q3: Improvement Suggestions** (optional, multi-line)
```
What would make this skill better? (Press Enter twice to finish)
Examples:
- Add examples for X
- Simplify language in section Y
- Split into smaller skills
- Add error recovery steps

Suggestions: _
```

**Q4: Additional Notes** (optional, single line)
```
Any other observations?

Notes: _
```

### 4. Update Log Entry

```python
# Load original log entry
entry = json.loads(line)

# Add evaluation metadata
entry["qualitative_evaluation"] = {
    "evaluated_at": datetime.now(timezone.utc).isoformat(),
    "rating": rating,
    "friction_points": friction_list,
    "improvement_suggestions": suggestions_list,
    "evaluator_notes": notes,
    "evaluator": "human"  # vs "automated" in future
}

# Write back to log file (replace line)
# Maintain JSONL format integrity
```

### 5. Summary Report

```
✅ Evaluation Complete

Skill: imbue:proof-of-work
Executions Evaluated: 3
Average Rating: 4.0/5.0

Next Steps:
- Run `/abstract:aggregate-logs` to update LEARNINGS.md
- High-rated skills: Consider for examples
- Low-rated skills: Prioritize for improvement

Evaluations saved to: ~/.claude/skills/logs/imbue/proof-of-work/
```

## Implementation Notes

### Log File Handling

**Challenge**: JSONL files require line-by-line updates
**Solution**:
1. Read entire file into memory
2. Parse each line
3. Update matching entry
4. Write entire file back atomically

**Code Pattern**:
```python
import json
from pathlib import Path

def update_evaluation(log_file: Path, invocation_id: str, evaluation: dict):
    lines = log_file.read_text().splitlines()
    updated_lines = []

    for line in lines:
        entry = json.loads(line)
        if entry["invocation_id"] == invocation_id:
            entry["qualitative_evaluation"] = evaluation
        updated_lines.append(json.dumps(entry))

    # Atomic write
    log_file.write_text("\n".join(updated_lines) + "\n")
```

### Multi-Line Input Collection

**Challenge**: Claude Code command-line input is single-line by default
**Solution**: Use Bash tool with heredoc for multi-line input

```bash
# Prompt user
echo "Enter friction points (Ctrl+D to finish):"
friction=$(cat)
```

### Batch Mode

When `--all` flag is used:
1. Load all unevaluated executions
2. Present them one at a time
3. Allow "skip" option
4. Show progress (e.g., "Evaluating 2/5...")
5. Provide summary at end

### Date Filtering

```python
from datetime import datetime, timedelta

def filter_by_date(entries, target_date=None, days_back=7):
    if target_date:
        # Exact date match
        return [e for e in entries if e["timestamp"].startswith(target_date)]
    else:
        # Last N days
        cutoff = datetime.now() - timedelta(days=days_back)
        return [e for e in entries
                if datetime.fromisoformat(e["timestamp"]) > cutoff]
```

## Error Handling

### Log File Missing

```
⚠️  No execution logs found for skill: {skill_name}

This skill may not have been executed yet, or logging is not enabled.

Check:
- Skill name format (should be plugin:skill-name)
- Log directory: ~/.claude/skills/logs/<plugin>/<skill>/
- PostToolUse hook is installed (plugins/abstract/hooks/hooks.json)
```

### Already Evaluated

```
ℹ️  All recent executions already evaluated

Run with --all to re-evaluate, or wait for new executions.
```

### Invalid Rating

```
❌ Invalid rating: must be 1-5

Please enter a number between 1 and 5.
```

## Performance Considerations

- **Log File Size**: JSONL files grow daily; Phase 3 aggregation will archive old entries
- **Memory Usage**: Load one log file at a time, not entire log directory
- **I/O**: Batch updates to minimize file writes

## Testing Checklist

- [ ] Load logs from real skill execution
- [ ] Filter unevaluated entries correctly
- [ ] Collect multi-line input (friction, suggestions)
- [ ] Update JSONL atomically
- [ ] Handle missing log files gracefully
- [ ] Verify evaluation metadata format
- [ ] Test batch mode with multiple executions
- [ ] Validate date filtering logic

## Example Execution

```bash
# User invokes command
/abstract:evaluate-skill proof-of-work

# Agent loads logs
$ Read ~/.claude/skills/logs/imbue/proof-of-work/2026-01-08.jsonl

# Agent presents summary
Found 2 unevaluated executions from today:

1. Execution at 03:15:23 UTC (2.3s, success)
   Context: Validated POW requirements for PR #84

2. Execution at 04:22:11 UTC (1.8s, success)
   Context: Checked acceptance criteria compliance

# Agent prompts for evaluation (first execution)
Evaluate execution #1:

How effective was this skill? (1-5): 4

What friction did you encounter? (Enter twice to finish):
> Needed to clarify what "evidence" meant
>
[submitted]

Improvement suggestions? (Enter twice to finish):
> Add examples of valid evidence formats
>
[submitted]

Additional notes:
> Otherwise worked well
[submitted]

✅ Evaluation saved

# Agent continues to execution #2
Evaluate execution #2:
[... repeat ...]

# Final summary
✅ 2 evaluations completed

Skill: imbue:proof-of-work
Average Rating: 4.0/5.0
Common Friction: "evidence" definition unclear

Next: Run `/abstract:aggregate-logs` to update insights
```

## Integration Points

**Command**: `/abstract:evaluate-skill` (powers the user-facing command)

**Phase 3 Dependencies**:
- Log aggregator reads `qualitative_evaluation` field
- Calculates metrics: average rating, common friction, top suggestions

**Phase 5 Dependencies**:
- `/improve-skills` uses ratings to prioritize improvements
- Evaluator notes provide context for skill updates

## Related Skills

- `abstract:skill-execution-logger` - Captures raw execution data (Phase 1)
- `abstract:log-aggregator` - Processes evaluations into insights (Phase 3)
- `abstract:skill-improver` - Acts on evaluation feedback (Phase 5)

## Metrics

Track evaluation coverage:
- % of executions evaluated within 7 days
- Average rating by skill
- Most common friction points
- Evaluation response rate

Target: 20%+ of skill executions evaluated (sufficient for pattern detection)

## Version

1.0.0 (Phase 2 - Qualitative Evaluation Framework)
