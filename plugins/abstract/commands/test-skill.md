---
name: test-skill
description: TDD testing workflow for skills. Runs baseline test without skill, documents failures, runs with skill, and compares results. Use when developing or validating skills to ensure they address real failure modes.
usage: /test-skill [skill-path] [--phase red|green|refactor]
---

# Test Skill Command

Implements test-driven development workflow for Claude Code skills. Compares Claude's behavior with and without the skill to validate effectiveness and identify rationalizations.

## Usage

```bash
# Run full TDD cycle (all phases)
/test-skill skills/my-skill

# Run specific phase
/test-skill skills/my-skill --phase red
/test-skill skills/my-skill --phase green
/test-skill skills/my-skill --phase refactor

# Run with custom scenario file
/test-skill skills/my-skill --scenarios custom-tests.md

# Generate report without running tests
/test-skill skills/my-skill --report-only
```

## TDD Phases

### RED Phase (Baseline Testing)

**Goal**: Document Claude's failures WITHOUT the skill

**Process**:

1. **Temporarily disable skill**
   ```bash
   # Command automatically unloads skill from context
   # or prompts user to remove from plugin.json
   ```

2. **Run pressure scenarios**
   - Present challenging tasks that the skill should address
   - Use real-world scenarios that expose gaps
   - Include edge cases and ambiguous situations
   - Test for known failure modes

3. **Document exact responses**
   - Capture verbatim output
   - Note rationalization patterns
   - Identify failure modes
   - Record workarounds attempted

4. **Generate baseline report**

**Example Baseline Documentation**:

```markdown
## RED Phase: Baseline Test Results

Test Date: 2025-12-06
Skill: skills/analyzing-logs/SKILL.md
Status: SKILL NOT LOADED

---

### Scenario 1: Complex Multi-Service Log Analysis

**Input**: "We have logs from 3 services showing intermittent 503 errors. The errors spike every 15 minutes. Analyze and find the root cause."

**Expected Behavior**: Systematic analysis of temporal patterns, service dependencies, and correlation

**Actual Response**:
```
Let me look at those logs. The 503 errors are probably just temporary issues.
Have you tried restarting the services? That usually fixes these kinds of problems.
I can help you write a script to restart them automatically.
```

**Failure Mode**:
- Jumped to solution without analysis
- No temporal pattern investigation
- Ignored multi-service correlation
- No systematic debugging approach

**Rationalization Detected**:
- "This is a simple problem" (dismissed complexity)
- "Usually fixes these" (generalized without evidence)
- "Let me just..." (skipped methodology)

**Severity**: HIGH - Completely skipped systematic analysis

---

### Scenario 2: Log Pattern Recognition

**Input**: "Find anomalies in this 10MB log file: [attachment]"

**Expected Behavior**: Define baseline, identify statistical outliers, flag unusual patterns

**Actual Response**:
```
I'll grep for "ERROR" in the logs... [proceeds with ad-hoc searching]
```

**Failure Mode**:
- No baseline establishment
- No statistical analysis
- Ad-hoc pattern matching instead of systematic approach

**Rationalization Detected**:
- None (just didn't use methodology)

**Severity**: MEDIUM - Partial approach, missed key steps

---

### Summary

**Total Scenarios**: 5
**Complete Failures**: 2
**Partial Failures**: 3
**Passes**: 0

**Common Rationalization Patterns**:
1. "This is simple/quick" (3 occurrences)
2. "Let me just..." (2 occurrences)
3. "Usually..." generalizations (2 occurrences)

**Root Causes**:
- No systematic methodology enforced
- Tendency to jump to solutions
- Missing statistical analysis framework
- No temporal/correlation analysis patterns
```

### GREEN Phase (With Skill Testing)

**Goal**: Validate skill addresses documented failures

**Process**:

1. **Enable skill**
   ```bash
   # Command loads skill into context
   # or prompts user to add to plugin.json
   ```

2. **Run identical scenarios**
   - Use exact same inputs as RED phase
   - Same context and constraints
   - Same success criteria

3. **Compare results**
   - Did skill prevent failures?
   - Is methodology followed?
   - Are rationalizations countered?
   - Any new issues introduced?

4. **Document improvements and gaps**

**Example GREEN Documentation**:

```markdown
## GREEN Phase: With Skill Results

Test Date: 2025-12-06
Skill: skills/analyzing-logs/SKILL.md v0.2.0
Status: SKILL LOADED

---

### Scenario 1: Complex Multi-Service Log Analysis

**Response** (with skill):
```
Following systematic log analysis methodology:

1. Temporal Analysis
   - Establishing baseline: Normal request rate 1000/min
   - Spike pattern: Every 15min ±30sec
   - Duration: 2-3 minutes per spike

2. Service Correlation
   - Service A: 503 errors during spikes
   - Service B: Connection pool exhaustion 30s before
   - Service C: Scheduled task running every 15min

3. Root Cause Hypothesis
   - Service C batch job overwhelms Service B
   - Service B pool exhaustion cascades to Service A

4. Validation Steps
   - Check Service C schedule: CONFIRMED 15min cron
   - Check Service B pool config: CONFIRMED undersized
   - Check Service A retry logic: CONFIRMED no backoff

Root Cause: Service C batch job configuration + undersized Service B pool
```

**Improvement**:
✓ Systematic methodology followed
✓ Temporal patterns analyzed
✓ Service correlation investigated
✓ Root cause identified with evidence

**Remaining Issues**:
⚠ Could add confidence levels to hypotheses
⚠ No prioritization of multiple possible causes

**Rationalization Check**: NONE DETECTED

**Severity Improvement**: HIGH → RESOLVED

---

### Scenario 2: Log Pattern Recognition

**Response** (with skill):
```
Anomaly Detection Methodology:

1. Baseline Establishment (first 1000 lines)
   - INFO: 87%
   - WARN: 11%
   - ERROR: 2%

2. Statistical Analysis
   - Mean response time: 145ms
   - Std dev: 23ms
   - Outlier threshold: 145 + (2 * 23) = 191ms

3. Detected Anomalies
   - Response time spike: Lines 4523-4598 (avg 847ms, 6.7σ)
   - Error rate spike: Lines 8821-8834 (34%, 16x baseline)
   - Unusual endpoint: /internal/debug hit 47 times (0 in baseline)

4. Correlation Analysis
   - All anomalies co-occur in 15min window
   - Suggests single root cause event
```

**Improvement**:
✓ Baseline established
✓ Statistical analysis performed
✓ Systematic anomaly detection

**Remaining Issues**:
⚠ Still used grep in output (habit)
⚠ Could explain why 2σ chosen for threshold

**Rationalization Check**: NONE DETECTED

**Severity Improvement**: MEDIUM → MOSTLY RESOLVED

---

### Summary

**Total Scenarios**: 5
**Complete Failures**: 0 (was 2)
**Partial Failures**: 2 (was 3)
**Passes**: 3 (was 0)

**Improvement Rate**: 60% → 100% compliance

**Remaining Issues**:
- Some explanatory details could be expanded
- Occasional tool choice not optimal
- No rationalizations detected (good!)

**Recommendation**: Proceed to REFACTOR phase to address partial failures
```

### REFACTOR Phase (Bulletproofing)

**Goal**: Eliminate remaining gaps and harden against rationalizations

**Process**:

1. **Identify new rationalizations**
   - Review GREEN phase results
   - Look for subtle bypasses
   - Check for "letter vs spirit" compliance

2. **Add explicit counters**
   - For each rationalization, add specific counter-language
   - Close loopholes with concrete constraints
   - Make implicit requirements explicit

3. **Create rationalization table**
   - Document all observed rationalizations
   - Provide counter for each
   - Add to skill documentation

4. **Re-test scenarios**
   - Run full test suite again
   - Verify bulletproofing works
   - Iterate until perfect

**Example Rationalization Table**:

```markdown
## Rationalization Table

| Rationalization | Why It's Wrong | Counter in Skill |
|-----------------|----------------|------------------|
| "This is a simple log issue" | Simple logs become complex; methodology prevents escalation | "ALWAYS follow full methodology regardless of perceived simplicity" |
| "I can just grep for errors" | Misses patterns, context, correlation | "NEVER use ad-hoc searching. Establish baseline first." |
| "Let me quickly check..." | Skips systematic approach | "Complete temporal analysis BEFORE investigating specifics" |
| "Usually X means Y" | Generalizes without evidence | "Form hypotheses from THIS data, not past experience" |
| "I remember the skill says..." | Skills evolve; memory outdated | "READ and FOLLOW current skill version verbatim" |
```

**Example Bulletproofing Edits**:

```markdown
# Before (GREEN phase)
When analyzing logs, follow these steps:
1. Establish baseline
2. Identify patterns
3. Form hypotheses

# After (REFACTOR phase)
When analyzing logs, you MUST follow ALL steps in order.
Do NOT skip steps even if the issue seems simple or obvious.

**MANDATORY STEPS** (no exceptions):
1. **Establish Baseline** - Sample first 1000 lines minimum
   - Calculate error rate distribution
   - Measure timing statistics
   - NO SKIPPING even for "obviously wrong" logs

2. **Identify Patterns** - Use statistical methods only
   - Define outlier thresholds explicitly (e.g., 2σ)
   - NEVER use "grep ERROR" as pattern detection
   - Document why thresholds chosen

3. **Form Hypotheses** - Based on THIS data only
   - NO generalizations from past experience
   - NO "usually this means..." statements
   - Each hypothesis needs evidence from current logs

**RED FLAGS** - If you catch yourself saying:
- "This is simple/quick..." → STOP. Use full methodology.
- "Let me just..." → STOP. Follow steps in order.
- "Usually..." → STOP. Use current data only.
```

**Re-test Output**:

```markdown
## REFACTOR Phase: Re-test Results

Test Date: 2025-12-06
Skill: skills/analyzing-logs/SKILL.md v0.3.0
Status: BULLETPROOFED

---

All 5 scenarios: PASS ✓
Rationalizations detected: 0
Methodology compliance: 100%

**New behaviors observed**:
- Explicit acknowledgment of mandatory steps
- No shortcuts even for "obvious" issues
- Statistical rigor maintained throughout
- Red flag self-checks working

**Status**: READY FOR PRODUCTION
```

## Output Reports

### RED Phase Report

```
=================================================
RED PHASE: Baseline Testing Report
=================================================
Skill: skills/analyzing-logs/SKILL.md
Date: 2025-12-06 14:23:18
Status: SKILL NOT LOADED

SCENARIO RESULTS
-------------------------------------------------
✗ Scenario 1: Complex Multi-Service Analysis (FAIL)
  Severity: HIGH
  Failure: Skipped systematic methodology
  Rationalization: "This is simple", "Let me just..."

✗ Scenario 2: Log Pattern Recognition (FAIL)
  Severity: MEDIUM
  Failure: No baseline, ad-hoc searching
  Rationalization: None

✓ Scenario 3: Temporal Correlation (PARTIAL)
  Issues: Incomplete correlation analysis

✗ Scenario 4: Anomaly Detection (FAIL)
  Severity: HIGH
  Failure: No statistical approach
  Rationalization: "Usually means...", "Quick check"

✗ Scenario 5: Root Cause Analysis (FAIL)
  Severity: MEDIUM
  Failure: Jumped to conclusion without evidence

SUMMARY
-------------------------------------------------
Total Scenarios:     5
Complete Failures:   2 (40%)
Partial Failures:    3 (60%)
Passes:              0 (0%)

Top Rationalizations:
  1. "This is simple/quick" (3×)
  2. "Let me just..." (2×)
  3. "Usually..." (2×)

RECOMMENDATION
-------------------------------------------------
Skill needed. Focus on:
  - Enforcing systematic methodology
  - Countering "simplicity" rationalizations
  - Adding statistical analysis framework
  - Preventing solution-jumping

Next: Write minimal skill content, then run GREEN phase
Command: /test-skill skills/analyzing-logs --phase green
```

### GREEN Phase Report

```
=================================================
GREEN PHASE: With Skill Testing Report
=================================================
Skill: skills/analyzing-logs/SKILL.md v0.2.0
Date: 2025-12-06 15:47:33
Status: SKILL LOADED

COMPARISON RESULTS
-------------------------------------------------
✓ Scenario 1: HIGH → RESOLVED
  Improvement: Full methodology followed
  Remaining: Minor detail expansion needed

✓ Scenario 2: MEDIUM → MOSTLY RESOLVED
  Improvement: Baseline + statistical analysis
  Remaining: Some tool choice issues

✓ Scenario 3: PARTIAL → RESOLVED
  Improvement: Complete correlation analysis

~ Scenario 4: HIGH → PARTIAL
  Improvement: Statistical approach added
  Remaining: Threshold selection not explained

✓ Scenario 5: MEDIUM → RESOLVED
  Improvement: Evidence-based conclusions

SUMMARY
-------------------------------------------------
Total Scenarios:     5
Resolved:            3 (60%)
Mostly Resolved:     1 (20%)
Partial:             1 (20%)
New Failures:        0 (0%)

Improvement Rate: 80% overall

Rationalization Status:
  Detected in GREEN: 0 (good!)
  Subtle bypasses: 2 (tool choice, threshold explanation)

RECOMMENDATION
-------------------------------------------------
Significant improvement. Proceed to REFACTOR phase to:
  - Address partial resolution in Scenario 4
  - Add threshold selection guidance
  - Bulletproof against subtle bypasses
  - Add rationalization table

Next: Bulletproof skill content
Command: /bulletproof-skill skills/analyzing-logs
```

### REFACTOR Phase Report

```
=================================================
REFACTOR PHASE: Bulletproofing Report
=================================================
Skill: skills/analyzing-logs/SKILL.md v0.3.0
Date: 2025-12-06 16:32:09
Status: BULLETPROOFED

RE-TEST RESULTS
-------------------------------------------------
✓ Scenario 1: RESOLVED (maintained)
✓ Scenario 2: RESOLVED (improved from MOSTLY)
✓ Scenario 3: RESOLVED (maintained)
✓ Scenario 4: RESOLVED (improved from PARTIAL)
✓ Scenario 5: RESOLVED (maintained)

BULLETPROOFING ADDITIONS
-------------------------------------------------
✓ Rationalization table added (7 entries)
✓ RED FLAGS section added
✓ Mandatory steps made explicit
✓ Anti-bypass language strengthened
✓ Threshold selection guidance added

SUMMARY
-------------------------------------------------
Total Scenarios:     5
Resolved:            5 (100%)
New Failures:        0 (0%)

Rationalization Status:
  Detected: 0
  Countered: 7 patterns
  Self-checks: Working

FINAL STATUS
-------------------------------------------------
✓ All scenarios pass
✓ No rationalizations detected
✓ Methodology compliance: 100%
✓ Bulletproofing effective

STATUS: PRODUCTION READY

Recommend:
  - Update version to 1.0.0
  - Remove 'draft' status
  - Run final validation: /validate-plugin
```

## Integration with Workflow

Part of the complete TDD skill development cycle:

1. `/create-skill` → Scaffold with baseline-scenarios.md
2. **RED Phase** → Document failures without skill
3. **GREEN Phase** → Validate skill addresses failures
4. **REFACTOR Phase** → Bulletproof against rationalizations
5. `/bulletproof-skill` → Systematic loophole analysis
6. `/validate-plugin` → Final structure validation

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_tdd_tester.py \
  --skill "${1}" \
  --phase "${2:-all}" \
  --scenarios "${3:-baseline-scenarios.md}"
```

## See Also

- `/create-skill` - Skill scaffolding with TDD setup
- `/bulletproof-skill` - Anti-rationalization hardening
- `/validate-plugin` - Structure and compliance validation
- `docs/modular-skills/guide.md` - Testing methodology details
