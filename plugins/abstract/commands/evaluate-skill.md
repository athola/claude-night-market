# Evaluate Skill Execution

Manually evaluate a recent skill execution for qualitative feedback.

## Usage

```bash
/abstract:evaluate-skill <skill-name>              # Evaluate most recent execution
/abstract:evaluate-skill <skill-name> --all        # Evaluate all recent executions
/abstract:evaluate-skill <skill-name> --date YYYY-MM-DD  # Evaluate specific date
```

## Purpose

Captures human-in-loop qualitative feedback about skill effectiveness to improve the self-improvement loop. This data feeds into:
- Log aggregation (Phase 3)
- LEARNINGS.md pattern detection
- `/improve-skills` prioritization (Phase 5)

## What It Does

1. **Loads recent executions** from `~/.claude/skills/logs/<plugin>/<skill>/`
2. **Presents execution summary** (timestamp, duration, outcome, context preview)
3. **Prompts for evaluation**:
   - Effectiveness rating (1-5)
   - Friction points encountered
   - Improvement suggestions
4. **Updates log entry** with evaluation metadata
5. **Tracks evaluation completion** (prevents duplicate evaluations)

## Evaluation Questions

### 1. Effectiveness Rating (1-5)

- **5 - Exceptional**: Skill exceeded expectations, no friction
- **4 - Effective**: Skill achieved goal with minor friction
- **3 - Adequate**: Skill worked but had noticeable inefficiencies
- **2 - Poor**: Skill partially failed or required significant workarounds
- **1 - Failed**: Skill did not achieve intended outcome

### 2. Friction Points

What slowed you down or caused issues?
- Skill missing key information?
- Instructions unclear or incomplete?
- Wrong tool recommendations?
- Excessive token usage?
- Outdated information?
- Missing error handling?

### 3. Improvement Suggestions

What would make this skill better?
- Add examples?
- Simplify language?
- Update workflow steps?
- Add error recovery guidance?
- Split into smaller skills?
- Add context-specific variations?

## Output

Updates the log entry with:
```json
{
  "qualitative_evaluation": {
    "evaluated_at": "2026-01-08T04:00:00Z",
    "rating": 4,
    "friction_points": ["Missing error handling for X", "Y was unclear"],
    "improvement_suggestions": ["Add example for Z", "Simplify step 3"],
    "evaluator_notes": "Worked well but needed clarification on..."
  }
}
```

## Examples

### Evaluate Recent Execution

```bash
/abstract:evaluate-skill proof-of-work

# Output:
# Found 3 executions of imbue:proof-of-work in the last 7 days
#
# Most recent execution:
# - Timestamp: 2026-01-08 03:15:23 UTC
# - Duration: 2.3s
# - Outcome: success
# - Context: Validated POW for PR #84
#
# Rate effectiveness (1-5): _
```

### Evaluate All Recent

```bash
/abstract:evaluate-skill proof-of-work --all

# Evaluates all unevaluated executions from the last 7 days
```

### Evaluate Specific Date

```bash
/abstract:evaluate-skill proof-of-work --date 2026-01-07

# Evaluates executions from 2026-01-07
```

## Integration

**Phase 3** (Log Aggregation):
- Aggregator reads `qualitative_evaluation` field
- Calculates average ratings by skill
- Identifies common friction points
- Generates improvement recommendations

**Phase 5** (Self-Improvement):
- `/improve-skills` prioritizes low-rated skills
- Improvement suggestions guide skill updates
- Version tracking shows rating improvements over time

## Related

- `Skill(abstract:skill-execution-logger)` - Captures initial execution data
- `/abstract:aggregate-logs` - Rolls up evaluations to LEARNINGS.md (Phase 3)
- `/abstract:improve-skills` - Acts on evaluation insights (Phase 5)

## Hooks

None (manual invocation only).

## Permissions

- **allowed-tools**: `["Read", "Write", "Grep"]`
- **permission-mode**: `"default"`

## Version

1.0.0 (Phase 2 implementation)
