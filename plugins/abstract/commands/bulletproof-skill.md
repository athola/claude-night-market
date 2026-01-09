---
name: bulletproof-skill
description: Harden skills against rationalization and bypass behaviors
usage: /bulletproof-skill [skill-path]
---

# Bulletproof Skill Command

<identification>
triggers: bulletproof, harden skill, rationalization, loopholes, bypass, red flags, skill hardening, anti-bypass, skill compliance

use_when:
- Hardening skills against rationalization and bypass behaviors
- Identifying loopholes in skill language
- Generating rationalization tables
- Creating red flags lists
- Preparing skills for production

do_not_use_when:
- Testing skill functionality - use /test-skill instead
- Evaluating skill quality - use /skills-eval instead
- Creating new skills - use /create-skill instead
</identification>

Systematically hardens skills against rationalization and bypass behaviors. Identifies loopholes in skill language, generates detailed rationalization tables, and suggests explicit counters.

## Usage

```bash
# Analyze skill for loopholes and rationalizations
/bulletproof-skill skills/my-skill

# Generate full bulletproofing report
/bulletproof-skill skills/my-skill --report

# Apply suggested fixes automatically (interactive)
/bulletproof-skill skills/my-skill --interactive

# Check specific aspects only
/bulletproof-skill skills/my-skill --check loopholes
/bulletproof-skill skills/my-skill --check rationalizations
/bulletproof-skill skills/my-skill --check red-flags
```

## What is Bulletproofing?

**Problem**: LLMs (including Claude) tend to rationalize around constraints when not explicitly countered. Skills can be bypassed through:
- Vague language interpretation
- "Spirit vs letter" compliance
- Perceived simplicity exemptions
- Memory-based shortcuts

**Solution**: Bulletproofing makes implicit requirements explicit, adds specific counters for common rationalizations, and closes language loopholes.

## Workflow

### Step 1: Loophole Analysis

Scans skill content for weakness patterns:

#### Vague Language Detection

**Found**: "Usually follow these steps..."
**Issue**: "Usually" implies exceptions without defining them
**Fix**: "ALWAYS follow these steps. No exceptions."

**Found**: "Try to establish baseline first"
**Issue**: "Try to" suggests optional
**Fix**: "MUST establish baseline first. Do not proceed without it."

**Found**: "Generally use statistical methods"
**Issue**: "Generally" allows ad-hoc alternatives
**Fix**: "Use ONLY statistical methods. Define outlier thresholds explicitly."

#### Missing Exception Handling

**Found**: "Follow methodology when analyzing complex logs"
**Issue**: "Complex" is subjective; allows "simple" exemption
**Fix**: "Follow methodology for ALL log analysis, regardless of perceived complexity."

**Found**: "Use the framework for important decisions"
**Issue**: "Important" is subjective
**Fix**: "Use the framework for EVERY architectural decision, no matter how small."

#### Ambiguous Conditions

**Found**: "If time permits, add statistical analysis"
**Issue**: Allows skipping under time pressure
**Fix**: "Statistical analysis is MANDATORY. Budget time accordingly."

**Found**: "Consider using the checklist"
**Issue**: "Consider" allows ignoring
**Fix**: "USE the checklist. Check every item before proceeding."

#### Escape Hatches Without Constraints

**Found**: "Skip this step if unnecessary"
**Issue**: No criteria for "unnecessary"
**Fix**: "Skip this step ONLY IF: (1) condition A met, AND (2) documented in output, AND (3) alternative approach specified."

**Example Report**:

```
=================================================
LOOPHOLE ANALYSIS
=================================================
Skill: skills/analyzing-logs/SKILL.md v0.2.0

VAGUE LANGUAGE (4 instances)
-------------------------------------------------
Line 23: "Usually follow these steps"
  Issue: Implies optional usage
  Severity: HIGH
  Fix: "ALWAYS follow these steps in order"

Line 47: "Try to establish baseline"
  Issue: Suggests best-effort, not mandatory
  Severity: HIGH
  Fix: "MUST establish baseline before analysis"

Line 89: "Generally use statistical methods"
  Issue: Allows ad-hoc alternatives
  Severity: MEDIUM
  Fix: "Use ONLY statistical methods"

Line 134: "Should document findings"
  Issue: "Should" vs "must"
  Severity: LOW
  Fix: "MUST document findings"

MISSING EXCEPTIONS (3 instances)
-------------------------------------------------
Line 34: "Follow methodology for complex logs"
  Issue: "Complex" undefined, allows "simple" bypass
  Severity: CRITICAL
  Fix: "Follow methodology for ALL logs"

Line 78: "For important patterns..."
  Issue: "Important" subjective
  Severity: HIGH
  Fix: "For ALL patterns..."

AMBIGUOUS CONDITIONS (2 instances)
-------------------------------------------------
Line 56: "If time permits, add correlation analysis"
  Issue: Allows skipping under pressure
  Severity: HIGH
  Fix: "Correlation analysis is MANDATORY"

ESCAPE HATCHES (1 instance)
-------------------------------------------------
Line 102: "Skip if not needed"
  Issue: No criteria provided
  Severity: CRITICAL
  Fix: Add explicit skip criteria or remove

SUMMARY
-------------------------------------------------
Total Issues: 10
Critical: 2
High: 5
Medium: 1
Low: 1

Recommendation: Address all CRITICAL and HIGH issues before production
```

### Step 2: Rationalization Detection

Identifies common bypass patterns and generates counters:

#### Common Rationalization Patterns

1. **Simplicity Bypass**
   - "This is just a simple task"
   - "This is quick and obvious"
   - "No need for the full methodology here"

2. **Memory Shortcut**
   - "I remember what the skill says"
   - "I've done this before"
   - "The skill is basically X"

3. **Overkill Excuse**
   - "The skill is overkill for this"
   - "This doesn't warrant the full process"
   - "Too much overhead for a small task"

4. **Deferral Rationalization**
   - "Let me just do this one thing first"
   - "I'll check the skill after this quick step"
   - "I'll apply the skill to the next one"

5. **Spirit vs Letter**
   - "The spirit of the skill is X"
   - "The skill means Y in this context"
   - "Technically following the approach"

**Example Detection Report**:

```
=================================================
RATIONALIZATION DETECTION
=================================================
Skill: skills/analyzing-logs/SKILL.md v0.2.0

Based on testing and common LLM bypass patterns:

SIMPLICITY BYPASS (High Risk)
-------------------------------------------------
Trigger: Perception that task is "simple" or "obvious"
Pattern: "This is just a simple log check..."
Why It Happens: LLMs assess complexity and rationalize methodology as excessive
Current Counter: NONE FOUND
Suggested Counter: "Use full methodology regardless of perceived simplicity. Simple tasks become complex; methodology prevents this."

MEMORY SHORTCUT (High Risk)
-------------------------------------------------
Trigger: Recalling skill content from training
Pattern: "I remember the skill says..."
Why It Happens: Conflates training data with current skill version
Current Counter: NONE FOUND
Suggested Counter: "READ and FOLLOW current skill version. Do not rely on memory. Skills evolve."

OVERKILL EXCUSE (Medium Risk)
-------------------------------------------------
Trigger: Methodology seems excessive for small task
Pattern: "The skill is overkill for..."
Why It Happens: Optimizing for speed over correctness
Current Counter: NONE FOUND
Suggested Counter: "The skill exists BECAUSE shortcuts fail. Use it fully, every time."

DEFERRAL (Medium Risk)
-------------------------------------------------
Trigger: Desire to do "one quick thing" first
Pattern: "Let me just...", "I'll check the skill after..."
Why It Happens: Incremental bypass that compounds
Current Counter: PARTIALLY ADDRESSED (line 23)
Suggested Counter: "Check and apply skills BEFORE taking any action, no exceptions."

SUMMARY
-------------------------------------------------
High Risk Patterns: 2 (need explicit counters)
Medium Risk Patterns: 2 (partial coverage)
Low Risk Patterns: 0

Recommendation: Add Rationalization Table section to skill
```

### Step 3: Generate Rationalization Table

Creates detailed table for inclusion in skill:

```markdown
## Rationalization Table

This skill may trigger rationalization behaviors. If you catch yourself thinking any of these, STOP and follow the counter.

| Rationalization | Why It's Wrong | Counter |
|-----------------|----------------|---------|
| "This is just a simple log issue" | Simple problems compound without methodology. "Simple" is how critical issues start. | Use the FULL methodology regardless of perceived simplicity. |
| "I can just grep for ERROR" | Ad-hoc searching misses context, patterns, and correlations. | MUST establish baseline with statistical methods first. No shortcuts. |
| "Let me quickly check X first" | "One quick thing" becomes many. Bypassing methodology at the start cascades. | Apply skill BEFORE any analysis. No "quick checks" without baseline. |
| "Usually this pattern means Y" | Generalizing from past data without evidence from CURRENT logs. | Form hypotheses from THIS data only. No "usually" statements. |
| "I remember the skill says Z" | Skills evolve. Memory may be outdated or conflated with training data. | READ the current skill version. Follow it verbatim. |
| "The skill is overkill for this" | The skill exists because shortcuts fail in exactly these "small" cases. | Use the full skill. It's not overkill; it's prevention. |
| "The spirit of the skill is..." | Interpreting intent allows bypassing explicit requirements. | Follow the LETTER of the skill, not your interpretation. |
| "I'll apply it to the next one" | Deferral becomes permanent. "Next time" never comes. | Apply NOW. Every time. No deferrals. |
| "This doesn't warrant full analysis" | Wrong. If it warranted calling you, it warrants proper methodology. | If asked to analyze, use full methodology. Period. |

### Red Flag Self-Check

If you catch yourself about to say ANY of these, STOP immediately:
- "This is simple/quick/obvious..."
- "Let me just..."
- "Usually/Generally/Typically..."
- "I remember..."
- "The skill basically says..."
- "This doesn't really need..."
- "I'll use the skill next time..."
- "The spirit of the skill..."
- "Quick check before..."
```

### Step 4: Create Red Flags List

Identifies trigger phrases indicating potential bypass:

```
=================================================
RED FLAGS ANALYSIS
=================================================
Skill: skills/analyzing-logs/SKILL.md v0.2.0

TRIGGER PHRASES (9 identified)
-------------------------------------------------
These phrases often precede skill bypass. Add self-check.

FLAG: "Let me just quickly..."
   Context: Attempting shortcut before methodology
   Counter: "No 'quick' actions. Use methodology first."

FLAG: "This doesn't really need..."
   Context: Judging necessity subjectively
   Counter: "If asked to analyze, use full methodology."

FLAG: "I'll use the skill next time..."
   Context: Deferral rationalization
   Counter: "Use the skill NOW. Every time."

FLAG: "The spirit of the skill is..."
   Context: Interpreting vs following literally
   Counter: "Follow the LETTER of the skill."

FLAG: "This is obviously..."
   Context: Assuming without analysis
   Counter: "No assumptions. Establish baseline first."

FLAG: "Usually this means..."
   Context: Generalizing from past experience
   Counter: "Use THIS data only. No 'usually' statements."

FLAG: "Simple check before..."
   Context: Pre-methodology shortcut
   Counter: "No checks before baseline. Follow order."

FLAG: "I remember the skill says..."
   Context: Memory vs current version
   Counter: "READ current skill. Don't rely on memory."

FLAG: "Overkill for..."
   Context: Dismissing methodology as excessive
   Counter: "Use full skill. It exists for a reason."

RECOMMENDATION
-------------------------------------------------
Add "Red Flag Self-Check" section to skill:
- List all trigger phrases
- Instruct to STOP if detected
- Reference counter for each
```

### Step 5: Suggest Counters

For each identified issue, provides specific remediation:

```
=================================================
SUGGESTED COUNTERS
=================================================
Skill: skills/analyzing-logs/SKILL.md v0.2.0

CLOSING LOOPHOLES
-------------------------------------------------

Issue #1 (Line 23): "Usually follow these steps"
Current: Usually follow these steps: baseline, analysis, hypothesis
Suggested:
  ALWAYS follow these steps in exact order:
  1. Establish baseline (MANDATORY)
  2. Statistical analysis (MANDATORY)
  3. Form hypotheses (MANDATORY)

  Do NOT skip steps even if issue seems simple or obvious.

Issue #2 (Line 34): "Follow methodology for complex logs"
Current: Follow this methodology when analyzing complex logs
Suggested:
  Follow this methodology for ALL log analysis without exception.

  "Complex" vs "simple" is subjective and leads to bypassing.
  Use the FULL methodology regardless of your perception of complexity.

ADDING RATIONALIZATION COUNTERS
-------------------------------------------------

Add new section after "Core Principles":

## Rationalization Prevention

You may be tempted to bypass this methodology. Common rationalizations:

**"This is simple"** → Wrong. Use full methodology anyway.
**"I'll just grep"** → Wrong. Establish baseline first.
**"I remember the skill"** → Wrong. Read current version.
**"Let me quickly..."** → Wrong. Follow methodology before any action.
**"Usually means X"** → Wrong. Use current data only.

If you catch yourself thinking ANY of these, STOP and restart from step 1.

STRENGTHENING EXISTING LANGUAGE
-------------------------------------------------

Replace weak directive words:
- "should" → "MUST"
- "try to" → "ALWAYS"
- "consider" → "USE"
- "generally" → "ONLY"
- "usually" → "ALWAYS"
- "if possible" → "MANDATORY"

Add emphasis to critical requirements:
- Use CAPITALS for absolute requirements
- Use "No exceptions" where appropriate
- Add "MANDATORY" labels to steps
- Use "Do NOT" instead of "Avoid"

ADDING EXPLICIT EXCEPTIONS
-------------------------------------------------

Issue #3 (Line 102): "Skip if not needed"
Current: Skip correlation analysis if not needed
Suggested:
  Skip correlation analysis ONLY IF ALL conditions met:
  1. Single service in scope (not multi-service)
  2. Temporal pattern already isolated to single cause
  3. Documented in output why correlation skipped

  Default: ALWAYS do correlation analysis unless above criteria met.

SUMMARY
-------------------------------------------------
Total Suggested Edits: 12
  Loophole Closures: 5
  Rationalization Counters: 4
  Language Strengthening: 3

Estimated Token Impact: +450 tokens (15% increase)
Worth it: YES - prevents systematic bypassing
```

## Output

### Summary Report

```
=================================================
BULLETPROOFING REPORT
=================================================
Skill: skills/analyzing-logs/SKILL.md v0.2.0
Analysis Date: 2025-12-06 16:15:42

VULNERABILITY ASSESSMENT
-------------------------------------------------
Loopholes Found: 10
  Critical: 2
  High: 5
  Medium: 1
  Low: 1

Rationalization Risks: 9 patterns
  High Risk: 2
  Medium Risk: 2
  Low Risk: 0

Red Flags: 9 trigger phrases

Overall Vulnerability: HIGH
Recommendation: Apply bulletproofing before production use

SUGGESTED ADDITIONS
-------------------------------------------------
OK Rationalization Table (9 entries)
OK Red Flag Self-Check section
OK 12 language edits
OK 3 explicit exception definitions

Estimated Changes:
  Lines added: ~45
  Tokens added: ~450 (+15%)
  Hardening level: Bulletproof

NEXT STEPS
-------------------------------------------------
1. Review suggested edits: bulletproof-report.md
2. Apply changes to SKILL.md
3. Re-run tests: /test-skill skills/analyzing-logs --phase refactor
4. Validate: /validate-plugin
5. Update version: 0.2.0 → 0.3.0 (bulletproofed)

Files Generated:
  - bulletproof-report.md (full analysis)
  - rationalization-table.md (for inclusion)
  - suggested-edits.diff (for review)
```

### Interactive Mode

```bash
/bulletproof-skill skills/analyzing-logs --interactive

=================================================
Bulletproofing: skills/analyzing-logs/SKILL.md
=================================================

Analyzing... [████████████████████] 100%

Found 10 loopholes, 9 rationalization risks, 9 red flags

Apply suggested fixes? (y/n/review): review

--- Loophole #1 ---
Line 23: "Usually follow these steps"
Severity: HIGH

Suggested fix:
  ALWAYS follow these steps in exact order...

Apply? (y/n/edit/skip): y OK

--- Loophole #2 ---
Line 34: "Follow methodology for complex logs"
Severity: CRITICAL

Suggested fix:
  Follow this methodology for ALL log analysis...

Apply? (y/n/edit/skip): y OK

[... continues for all issues ...]

Summary:
  Applied: 8
  Skipped: 2
  Edited: 0

Generate rationalization table? (y/n): y OK
Add red flag section? (y/n): y OK

Bulletproofing complete!
New version: 0.3.0
Re-test recommended: /test-skill skills/analyzing-logs --phase refactor
```

## Severity Levels

### Critical
Issues that allow complete methodology bypass. Must fix.

Examples:
- "For complex cases..." (allows "simple" exemption)
- "Skip if not needed" (no criteria)
- No anti-rationalization language at all

### High
Issues that significantly weaken skill compliance.

Examples:
- "Usually follow..." (implies exceptions)
- "Try to use..." (suggests optional)
- Vague conditions without definitions

### Medium
Issues that create minor loopholes or ambiguity.

Examples:
- "Should consider..." (weak directive)
- "Generally prefer..." (allows alternatives)
- Incomplete exception handling

### Low
Issues that could be clearer but unlikely to cause bypass.

Examples:
- Inconsistent terminology
- Missing examples for edge cases
- Could add emphasis

## Integration

Part of the TDD bulletproofing workflow:

1. `/create-skill` → Initial scaffold
2. `/test-skill --phase red` → Document baseline failures
3. `/test-skill --phase green` → Validate basic skill
4. **`/bulletproof-skill`** → Systematic hardening
5. `/test-skill --phase refactor` → Validate bulletproofing
6. `/validate-plugin` → Final checks

## Best Practices

### When to Bulletproof

- After GREEN phase shows improvement but partial compliance
- Before releasing skill to production
- After observing bypass behaviors in practice
- Periodically for critical skills (quarterly review)

### What Makes Good Bulletproofing

1. **Specific counters**: Address exact rationalization patterns
2. **Explicit requirements**: No ambiguity in "must" vs "should"
3. **Self-check triggers**: Red flags LLM can catch itself saying
4. **Defined exceptions**: If allowing skip, specify criteria exactly

### Common Mistakes

 Over-bulletproofing simple skills (adds noise)
 Generic counters ("follow the skill" - not specific enough)
 Adding counters without testing (may not address real patterns)
 Bulletproofing without rationalization table (miss common patterns)

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skill_bulletproofer.py \
  --skill "${1}" \
  --report \
  --interactive="${2:-false}"
```

## See Also

- `/test-skill` - TDD testing workflow (use before bulletproofing)
- `/create-skill` - Skill scaffolding
- `/validate-plugin` - Final validation
- `docs/modular-skills/modules/antipatterns-and-migration.md` - Rationalization patterns
