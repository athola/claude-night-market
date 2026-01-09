# Improve Skills from Observability Data

Automatically identify and implement skill improvements based on execution logs and user evaluations.

## Usage

```bash
/abstract:improve-skills                          # Analyze all skills
/abstract:improve-skills --skill proof-of-work    # Improve specific skill
/abstract:improve-skills --top 5                  # Top 5 improvement opportunities
/abstract:improve-skills --dry-run                # Preview without implementing
```

## Purpose

Part of Issue #69 Phase 5, this command closes the self-improvement loop by:
1. Reading LEARNINGS.md for improvement opportunities
2. Prioritizing by severity (frequency × impact × ease)
3. Generating skill update proposals
4. Optionally implementing changes with validation

## What It Does

1. **Loads LEARNINGS.md** from `~/.claude/skills/LEARNINGS.md`
2. **Identifies opportunities**:
   - High-impact issues (failure rates, excessive failures)
   - Slow execution times
   - Low user ratings with specific friction points
3. **Prioritizes improvements**:
   - Frequency: How often is this skill used?
   - Impact: How much does the issue hurt?
   - Ease: How simple is the fix?
4. **Generates proposals**:
   - What to change (specific file/section)
   - Why (data from evaluations)
   - How (implementation approach)
5. **Optionally implements**:
   - Updates skill files
   - Increments version in frontmatter
   - Runs validation tests
   - Creates commit

## Prioritization Formula

```
Priority Score = (Frequency × Impact) / Ease

Where:
- Frequency: Execution count in analysis period
- Impact:
  - High failure rate: 10
  - Low rating: rating_diff × 2 (e.g., 2.5 vs 5.0 = 5.0 impact)
  - Slow execution: seconds_over_threshold / 10
- Ease:
  - Simple text update: 1
  - Add examples: 2
  - Restructure workflow: 5
  - Refactor logic: 10
```

**Threshold**: Priority > 5.0 = implement now, 2.0-5.0 = discuss, <2.0 = defer

## Examples

### Analyze All Skills

```bash
/abstract:improve-skills

# Output:
# Reading LEARNINGS.md...
# Found 12 improvement opportunities
#
# Top 5 by priority:
# 1. imbue:proof-of-work (Priority: 8.5)
#    Issue: 42% failure rate (11/26 executions)
#    Fix: Add error handling for missing PROOF.md
#    Ease: Simple (add try/catch)
#
# 2. abstract:skill-auditor (Priority: 6.2)
#    Issue: 2.8/5.0 rating - "too verbose"
#    Fix: Add --quiet flag
#    Ease: Medium (new parameter)
# ...
#
# Implement top 5? (y/n):
```

### Improve Specific Skill

```bash
/abstract:improve-skills --skill proof-of-work

# Focuses only on imbue:proof-of-work
# Shows all identified issues for that skill
# Proposes fixes in priority order
```

### Preview Mode

```bash
/abstract:improve-skills --dry-run

# Shows what would be changed without implementing
# Useful for review before committing
```

### Top N Opportunities

```bash
/abstract:improve-skills --top 3

# Only processes top 3 highest-priority improvements
# Useful for focused improvement sessions
```

## Improvement Types

### High Failure Rate

**Example**: `imbue:proof-of-work` fails 42% of the time

**Typical Fixes**:
- Add error handling for common failure modes
- Add validation before execution
- Improve error messages
- Add troubleshooting section

### Slow Execution

**Example**: `sanctum:pr-agent` averages 45s (threshold: 10s)

**Typical Fixes**:
- Optimize slow operations (e.g., git commands)
- Add caching
- Remove redundant steps
- Parallelize independent operations

### Low User Rating

**Example**: `abstract:skill-auditor` rated 2.8/5.0 - "too verbose output"

**Typical Fixes**:
- Add --quiet flag
- Improve output formatting
- Add progress indicators
- Simplify language

### Common Friction

**Example**: Users report "unclear what 'evidence' means"

**Typical Fixes**:
- Add examples
- Clarify terminology
- Add inline help
- Link to documentation

## Implementation Workflow

For each improvement (if not --dry-run):

1. **Read skill file** (SKILL.md or skill module)
2. **Apply changes**:
   - Update frontmatter (increment version)
   - Modify content (add examples, fix errors, etc.)
   - Update changelog entry
3. **Validate**:
   - Parse frontmatter (ensure valid YAML)
   - Check token count (warn if >2000 tokens)
   - Run skill-auditor validation
4. **Test** (if applicable):
   - For skills with examples, validate examples still work
5. **Commit**:
   - Create commit with improvement details
   - Reference LEARNINGS.md insights

## Output

### Improvement Proposal

```markdown
## Improvement Proposal: imbue:proof-of-work

**Issue**: High failure rate (42.3% - 11/26 executions)
**Priority**: 8.5 (High)

**Root Cause** (from LEARNINGS.md):
- Missing PROOF.md file (5 occurrences)
- Invalid acceptance_criteria field (3 occurrences)
- KeyError on 'evidence' (3 occurrences)

**Proposed Fix**:
1. Add validation at start:
   - Check PROOF.md exists before parsing
   - Validate required fields with clear error messages
2. Add error recovery:
   - Suggest creating PROOF.md if missing
   - Show example of valid acceptance_criteria
3. Update frontmatter version: 2.0.0 → 2.1.0

**Expected Impact**:
- Reduce failure rate from 42% to <10%
- Improve error messages for remaining failures
- Better user experience

**Files to modify**:
- plugins/imbue/skills/proof-of-work/SKILL.md
- plugins/imbue/skills/proof-of-work/modules/validation-protocols.md

Implement this improvement? (y/n):
```

## Integration

**Phase 1-3 Data Sources**:
- Execution logs (Phase 1): Failure rates, duration metrics
- Qualitative evaluations (Phase 2): User ratings, friction points, suggestions
- LEARNINGS.md (Phase 3): Aggregated patterns and insights

**Phase 4 Feedback Loop**:
- `/fix-workflow` surfaces historical issues during workflow analysis
- Improvements target skills identified as problematic in workflows

## Metrics Tracking

After implementing improvements, the observability infrastructure tracks:
- **Version comparison**: Rating before/after, failure rate before/after
- **Improvement effectiveness**: Did the fix work?
- **Regression detection**: Did the fix introduce new issues?

These metrics feed back into future LEARNINGS.md reports.

## Related

- `/abstract:aggregate-logs` - Generates LEARNINGS.md (Phase 3)
- `/abstract:evaluate-skill` - Captures qualitative feedback (Phase 2)
- `Skill(abstract:skill-execution-logger)` - Raw data capture (Phase 1)
- `/fix-workflow` - Uses LEARNINGS for workflow analysis (Phase 4)

## Version

1.0.0 (Phase 5 implementation)
