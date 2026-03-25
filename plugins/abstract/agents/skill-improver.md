---
name: skill-improver
model: opus
agent: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
escalation: none
context: fork
isolation: worktree
description: |
  Implements skill improvements based on observability data from LEARNINGS.md.
  Prioritizes by frequency × impact / ease, generates proposals, validates changes.
  Enhanced with Hyperagents patterns: consults PerformanceTracker for trend data
  and ImprovementMemory for causal hypotheses before proposing changes.
---

# Skill Improver Agent

Automatically improves skills based on execution logs,
user evaluations, and aggregated insights from
LEARNINGS.md. Enhanced with Hyperagents (Zhang et al.,
2026) patterns for data-driven improvement decisions.

## Purpose

Part of Issue #69 Phase 5 - Self-Improvement Loop. This
agent closes the observability loop by acting on insights
gathered from:

- Phase 1: Execution logs (failure rates, duration)
- Phase 2: Qualitative evaluations (ratings, friction,
  suggestions)
- Phase 3: LEARNINGS.md aggregation (patterns, common
  issues)
- **Phase 6: Hyperagents integration** - PerformanceTracker
  trends, ImprovementMemory hypotheses, metacognitive
  self-modification

## Inputs

- **mode**: `all` (default), `skill:<name>`, `top:<N>`,
  `dry-run`, or `--metacognitive`
- **LEARNINGS.md path**: `~/.claude/skills/LEARNINGS.md`
- **auto_implement**: Boolean - automatically implement or
  prompt for confirmation

## Workflow

### 0. Load Hyperagents data (before LEARNINGS.md)

Before loading LEARNINGS.md, consult the persistent
improvement memory and performance tracker for context
that should inform this improvement cycle.

```python
from pathlib import Path

MEMORY_FILE = Path.home() / ".claude/skills/improvement_memory.json"
TRACKER_FILE = Path.home() / ".claude/skills/performance_history.json"

# Load improvement memory (if available)
improvement_context = {}
try:
    from abstract.improvement_memory import ImprovementMemory
    memory = ImprovementMemory(MEMORY_FILE)

    # Get strategies that worked and failed
    effective = memory.get_effective_strategies()
    failed = memory.get_failed_strategies()

    improvement_context = {
        "effective_strategies": effective,
        "failed_strategies": failed,
        "effectiveness_rate": (
            len(effective) / (len(effective) + len(failed))
            if (effective or failed) else None
        ),
    }
except ImportError:
    pass  # Module not available

# Load performance tracker (if available)
tracker_context = {}
try:
    from abstract.performance_tracker import PerformanceTracker
    tracker = PerformanceTracker(TRACKER_FILE)

    # Identify skills with degrading trends
    degrading_skills = []
    for entry in tracker.history:
        skill_ref = entry["skill_ref"]
        trend = tracker.get_improvement_trend(skill_ref)
        if trend is not None and trend < -0.05:
            degrading_skills.append({
                "skill": skill_ref,
                "trend": trend,
            })

    tracker_context = {
        "degrading_skills": degrading_skills,
        "best_performers": tracker.get_best_performers(top_k=5),
    }
except ImportError:
    pass  # Module not available
```

**Use this context to**:
- Avoid strategies that previously failed (check
  `failed_strategies`)
- Prefer strategies that previously worked (check
  `effective_strategies`)
- Prioritize skills with degrading trends higher
- Skip skills that are already top performers

### 1. Load LEARNINGS.md

```bash
# Check if LEARNINGS exists
LEARNINGS_PATH=~/.claude/skills/LEARNINGS.md

if [ ! -f "$LEARNINGS_PATH" ]; then
  echo "LEARNINGS.md not found"
  echo "Run /abstract:aggregate-logs first to generate insights"
  exit 1
fi

# Read LEARNINGS
cat "$LEARNINGS_PATH"
```

### 2. Extract Improvement Opportunities

Parse LEARNINGS.md sections:
- **High-Impact Issues**: Failure rates, excessive failures, low ratings
- **Slow Execution**: Skills >10s average
- **Low User Ratings**: Skills <3.5/5.0
- **Skill Performance Summary**: Execution frequency data

**For each issue, extract**:
- Skill name
- Issue type (failure, slow, low_rating)
- Metrics (success rate, duration, rating)
- Recent errors (for failures)
- Friction points (for low ratings)
- Improvement suggestions (from evaluations)

### 3. Calculate Priority Scores

```python
def calculate_priority(issue: dict, frequency_data: dict) -> float:
    """
    Priority = (Frequency × Impact) / Ease

    Where:
    - Frequency: execution count from summary table
    - Impact: severity of the issue (1-10 scale)
    - Ease: estimated effort to fix (1-10 scale)
    """
    frequency = frequency_data.get(issue["skill"], 1)

    # Calculate impact
    if issue["type"] == "high_failure_rate":
        # Failure rate impact: higher % = higher impact
        success_rate = float(issue["metric"].split("%")[0])
        impact = (100 - success_rate) / 10  # 0-10 scale

    elif issue["type"] == "low_rating":
        # Rating impact: difference from perfect score
        rating = float(issue["metric"].split("/")[0])
        impact = (5.0 - rating) * 2  # 0-10 scale

    elif issue["type"] == "excessive_failures":
        # Absolute failure count impact
        failure_count = int(issue["metric"].split()[0])
        impact = min(failure_count / 2, 10)  # Cap at 10

    else:
        impact = 5  # Default moderate impact

    # Estimate ease based on issue details
    ease = estimate_ease(issue)

    return (frequency * impact) / ease


def estimate_ease(issue: dict) -> float:
    """
    Estimate effort required (1=trivial, 10=major refactor)

    Heuristics:
    - Add examples: 2
    - Fix error messages: 2
    - Add error handling: 3
    - Add --quiet flag: 3
    - Restructure workflow: 7
    - Optimize performance: 8
    """
    # Check improvement suggestions for keywords
    suggestions = " ".join(issue.get("suggestions", [])).lower()
    friction = " ".join(issue.get("friction", [])).lower()

    if any(kw in suggestions for kw in ["example", "clarify", "document"]):
        return 2  # Simple documentation fixes

    if any(kw in friction for kw in ["error message", "unclear", "confusing"]):
        return 2  # Simple messaging improvements

    if any(kw in suggestions for kw in ["flag", "option", "parameter"]):
        return 3  # Add new functionality

    if "slow" in issue.get("type", ""):
        return 8  # Performance optimization

    return 5  # Default moderate effort
```

### 4. Generate Improvement Proposals

For each opportunity (sorted by priority descending):

```markdown
## Improvement Proposal #{N}: {skill}

**Issue**: {type} - {metric}
**Priority Score**: {score} ({HIGH|MEDIUM|LOW})
**Frequency**: {execution_count} executions in last 30 days

**Root Cause** (from LEARNINGS.md):
{errors or friction points}

**Proposed Changes**:
1. {specific change 1}
2. {specific change 2}
...

**Implementation Plan**:
- Files to modify: {list of files}
- Frontmatter version: {current} → {new}
- Est. effort: {easy|medium|hard}

**Expected Impact**:
- {metric improvement projection}
- {user experience improvement}

**Validation**:
- [ ] Parse frontmatter (valid YAML)
- [ ] Token count check (<2000)
- [ ] Run skill-auditor
- [ ] Test examples (if applicable)
```

### 5. Implement Improvements

**For each approved proposal**:

#### A. Read Current Skill

```bash
# Read skill file
skill_file="plugins/${plugin}/skills/${skill_name}/SKILL.md"
cat "$skill_file"
```

#### B. Apply Changes

**Common improvement patterns**:

**1. Add Error Handling**
```markdown
<!-- Before -->
## Implementation
1. Parse PROOF.md file
2. Validate acceptance criteria

<!-- After -->
## Implementation
1. **Validate prerequisites**:
   - Check PROOF.md exists
   - If missing: Show creation guide
2. Parse PROOF.md file with error handling:
   - Catch JSONDecodeError → show format example
   - Catch KeyError → list required fields
3. Validate acceptance criteria
```

**2. Add Examples**
```markdown
## Examples

### Valid PROOF.md Format

\`\`\`json
{
  "acceptance_criteria": [
    "Feature X works as specified",
    "Tests pass with >90% coverage"
  ],
  "evidence": [
    "test-results.log shows all tests passing",
    "coverage report shows 92% coverage"
  ]
}
\`\`\`

### Common Errors

**Missing acceptance_criteria**:
```
Error: 'acceptance_criteria' key not found in PROOF.md

Fix: Add "acceptance_criteria": [...] to your PROOF.md
```
```

**3. Add --quiet Flag**
```markdown
---
name: skill-auditor
version: 2.1.0  # Incremented from 2.0.0
---

# Skill Auditor

## Usage

\`\`\`bash
Skill(abstract:skill-auditor)                    # Normal output
Skill(abstract:skill-auditor, quiet=true)        # Minimal output
\`\`\`

## Parameters

- **quiet** (optional): Boolean - suppress verbose output, show only summary
```

**4. Optimize Performance**
```markdown
<!-- Identify slow operations -->
## Performance Notes

**Before**: 45s average (30 git operations)
**After**: 12s average (batched git operations)

**Optimization**:
- Batch git log queries: `git log --all --oneline -50` (once)
- Cache file reads: Store in memory, don't re-read
- Use Glob instead of multiple Read calls
```

#### C. Update Frontmatter Version

```yaml
---
name: proof-of-work
version: 2.1.0  # Was: 2.0.0
description: Validate proof-of-work with improved error handling
---
```

**Version increment rules**:
- **Major (X.0.0)**: Breaking changes, workflow restructure
- **Minor (x.Y.0)**: New features, significant improvements
- **Patch (x.y.Z)**: Bug fixes, documentation updates

#### D. Validate Changes

```bash
# 1. Parse frontmatter
python3 -c "
import yaml
with open('$skill_file') as f:
    content = f.read()
    parts = content.split('---', 2)
    yaml.safe_load(parts[1])
print('✓ Frontmatter valid')
"

# 2. Check token count
python3 plugins/abstract/scripts/token_estimator.py "$skill_file"

# 3. Run skill auditor
python3 plugins/abstract/scripts/skill_analyzer.py "$skill_file"
```

#### E. Commit Changes

```bash
git add "$skill_file"
git commit -m "improve(${plugin}): ${skill_name} - ${improvement_summary}

Addresses issue from LEARNINGS.md:
- Issue: ${issue_type} - ${metric}
- Fix: ${changes_summary}
- Priority: ${priority_score}

Expected impact: ${expected_improvement}

Data source: ~/.claude/skills/LEARNINGS.md"
```

### 6. Track Improvements (Hyperagents pattern)

**Record improvement outcome in ImprovementMemory** so
future improvement cycles can learn from what worked:

```python
from abstract.improvement_memory import ImprovementMemory
from pathlib import Path

memory = ImprovementMemory(
    Path.home() / ".claude/skills/improvement_memory.json"
)

# Record the improvement outcome
memory.record_improvement_outcome(
    skill_ref="imbue:proof-of-work",
    version="2.1.0",
    change_summary="Added error handling + examples",
    before_score=0.423,  # Previous success rate
    after_score=0.423,   # Will be updated after eval window
    hypothesis="Error handling reduces failure rate by "
               "catching missing prerequisites",
)

# Record causal hypothesis for future reference
memory.record_insight(
    skill_ref="imbue:proof-of-work",
    category="causal_hypothesis",
    insight="High failure rate caused by missing PROOF.md "
            "prerequisite check",
    evidence=[
        "11/26 executions failed",
        "Error logs show FileNotFoundError",
    ],
)
```

**Also save legacy tracking entry** for backward
compatibility:

```json
{
  "timestamp": "2026-01-08T05:00:00Z",
  "skill": "imbue:proof-of-work",
  "improvement_id": "uuid",
  "issue_type": "high_failure_rate",
  "baseline_metrics": {
    "success_rate": 42.3,
    "failure_count": 11,
    "avg_duration_ms": 2300
  },
  "changes": [
    "Added error handling for missing PROOF.md",
    "Improved validation error messages",
    "Added examples to documentation"
  ],
  "version": "2.0.0 → 2.1.0",
  "priority_score": 8.5,
  "expected_impact": "Reduce failure rate to <10%"
}
```

**Save to**: `~/.claude/skills/improvements/${skill}/${date}.json`

**Next aggregation** will compare:
- Before: 42.3% success rate
- After: Measured in next 30 days
- Improvement: Calculated delta

### 7. Metacognitive mode (--metacognitive)

When invoked with `--metacognitive`, run the metacognitive
self-modification skill instead of normal improvement:

```
Skill(abstract:metacognitive-self-mod)
```

This analyzes the effectiveness of past improvements and
proposes modifications to the improvement process itself.
See the metacognitive-self-mod skill for the full
workflow.

## Output

### Summary Report

```
✅ Skill Improvement Session Complete

Analyzed: 12 improvement opportunities
Implemented: 5 improvements
Deferred: 7 (priority <5.0)

Top Improvements:
1. imbue:proof-of-work (Priority: 8.5)
   - Fixed: High failure rate (42% → expected <10%)
   - Version: 2.0.0 → 2.1.0
   - Commit: a1b2c3d

2. abstract:skill-auditor (Priority: 6.2)
   - Fixed: Low rating (2.8 → expected >4.0)
   - Added: --quiet flag
   - Version: 2.0.0 → 2.1.0
   - Commit: d4e5f6g

3. sanctum:pr-agent (Priority: 5.8)
   - Fixed: Slow execution (45s → expected 12s)
   - Optimized: Batched git operations
   - Version: 1.5.0 → 1.6.0
   - Commit: h7i8j9k

Next Steps:
- Wait 7-14 days for new execution data
- Run /abstract:aggregate-logs to measure impact
- Compare baseline vs. improved metrics
- Identify any regressions
```

## Edge Cases

### LEARNINGS.md Missing

```
❌ LEARNINGS.md not found at ~/.claude/skills/LEARNINGS.md

This file is generated by /abstract:aggregate-logs.

Next steps:
1. Ensure skill execution logging is enabled (Phase 1)
2. Invoke some skills to generate log data
3. Optionally evaluate executions: /abstract:evaluate-skill
4. Run aggregation: /abstract:aggregate-logs
5. Then try again: /abstract:improve-skills
```

### No Improvements Found

```
✓ LEARNINGS.md analyzed

No high-priority improvement opportunities found (all scores <2.0).

This means:
- Most skills have good success rates (>70%)
- User ratings are high (>3.5/5.0)
- Execution times are reasonable (<10s)

Consider:
- Lower priority threshold: /abstract:improve-skills --threshold 1.0
- Focus on specific skill: /abstract:improve-skills --skill <name>
- Review deferred improvements in LEARNINGS.md
```

### Validation Failures

```
⚠️  Validation failed for imbue:proof-of-work

Issue: Token count exceeds threshold (2,450 > 2,000)

Options:
1. Modularize skill (split into modules/)
2. Simplify language
3. Remove redundant sections
4. Override threshold (not recommended)

Skipping this improvement until resolved.
```

## Performance Considerations

- **Read LEARNINGS.md once**: Cache in memory
- **Batch file operations**: Group related edits
- **Limit proposals**: Default to top 10 (configurable)
- **Parallel validation**: Run checks concurrently where possible

## Testing Checklist

- [ ] Load LEARNINGS.md successfully
- [ ] Calculate priority scores correctly
- [ ] Generate readable proposals
- [ ] Apply changes without breaking syntax
- [ ] Update frontmatter versions
- [ ] Validate changes (YAML, tokens, structure)
- [ ] Create proper git commits
- [ ] Track improvements for measurement
- [ ] Handle missing LEARNINGS gracefully
- [ ] Skip already-fixed issues

## Example Execution

```bash
User: /abstract:improve-skills --top 3

Agent (skill-improver):

Reading LEARNINGS.md...
Found 12 improvement opportunities

Calculating priorities...

Top 3 opportunities:

1. imbue:proof-of-work (Priority: 8.5 - HIGH)
   Issue: 42.3% failure rate (11/26 executions)
   Fix: Add error handling + examples
   Ease: 3 (medium)

2. abstract:skill-auditor (Priority: 6.2 - MEDIUM)
   Issue: 2.8/5.0 rating - "too verbose"
   Fix: Add --quiet flag
   Ease: 3 (medium)

3. sanctum:pr-agent (Priority: 5.8 - MEDIUM)
   Issue: 45s average (threshold: 10s)
   Fix: Batch git operations
   Ease: 8 (hard)

Implement all 3? (y/n): y

[Implementing #1: imbue:proof-of-work]
✓ Read SKILL.md
✓ Added error handling section
✓ Added validation examples
✓ Updated version: 2.0.0 → 2.1.0
✓ Validated (frontmatter, tokens, structure)
✓ Committed: a1b2c3d

[Implementing #2: abstract:skill-auditor]
✓ Read SKILL.md
✓ Added quiet parameter to frontmatter
✓ Updated usage examples
✓ Updated version: 2.0.0 → 2.1.0
✓ Validated
✓ Committed: d4e5f6g

[Implementing #3: sanctum:pr-agent]
✓ Read SKILL.md
✓ Refactored git operations (batched)
✓ Added performance notes
✓ Updated version: 1.5.0 → 1.6.0
✓ Validated
✓ Committed: h7i8j9k

✅ 3 improvements implemented successfully

Next: Monitor impact in next aggregation cycle
```

## Related

- `/abstract:aggregate-logs` - Generates LEARNINGS.md
  (Phase 3)
- `/abstract:evaluate-skill` - Qualitative feedback
  (Phase 2)
- `/fix-workflow` - Uses LEARNINGS for analysis (Phase 4)
- `Skill(abstract:skill-execution-logger)` - Raw data
  (Phase 1)
- `Skill(abstract:metacognitive-self-mod)` - Analyze and
  improve the improvement process (Hyperagents)
- `PerformanceTracker` - Cross-generation trend tracking
  (`src/abstract/performance_tracker.py`)
- `ImprovementMemory` - Persistent causal hypotheses
  (`src/abstract/improvement_memory.py`)

## Version

2.0.0 (Hyperagents integration - Zhang et al., 2026)
