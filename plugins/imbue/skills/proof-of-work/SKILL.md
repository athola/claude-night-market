---
name: proof-of-work
description: |

Triggers: validation, definition-of-done, proof, acceptance-criteria, testing
  Enforces "prove before claim" discipline - validation, testing, and evidence
  requirements before declaring work complete.

  Triggers: completion, finished, done, working, should work, configured,
  ready to use, implemented, fixed, improvement validated, workflow optimized,
  performance improved, issue resolved

  Use when: claiming ANY work is complete, recommending solutions, stating
  something will work, finishing implementations, validating improvements,
  completing improvement analysis

  DO NOT use when: explicitly asking questions or requesting clarification
  DO NOT use when: work is clearly in-progress and not claiming completion

  CRITICAL: This skill is MANDATORY before any completion claim. Violations
  result in wasted time and eroded trust.
category: workflow-methodology
tags: [validation, testing, proof, definition-of-done, acceptance-criteria]
dependencies:
  - imbue:evidence-logging
tools: []
usage_patterns:
  - completion-validation
  - acceptance-testing
  - proof-generation
complexity: intermediate
estimated_tokens: 3000
modules:
  - modules/validation-protocols.md
  - modules/acceptance-criteria.md
  - modules/red-flags.md
  - modules/iron-law-enforcement.md
---
## Table of Contents

- [The Problem This Solves](#the-problem-this-solves)
- [Core Principle](#core-principle)
- [The Iron Law](#the-iron-law)
- [When to Use](#when-to-use)
- [MANDATORY Usage (Non-Negotiable)](#mandatory-usage-(non-negotiable))
- [Red Flags (You're About to Violate This)](#red-flags-(you're-about-to-violate-this))
- [Required TodoWrite Items](#required-todowrite-items)
- [Validation Protocol](#validation-protocol)
- [Step 1: Reproduce the Problem (`proof:problem-reproduced`)](#step-1:-reproduce-the-problem-(proof:problem-reproduced))
- [Step 2: Test the Solution (`proof:solution-tested`)](#step-2:-test-the-solution-(proof:solution-tested))
- [Step 3: Check for Known Issues (`proof:edge-cases-checked`)](#step-3:-check-for-known-issues-(proof:edge-cases-checked))
- [Step 4: Capture Evidence (`proof:evidence-captured`)](#step-4:-capture-evidence-(proof:evidence-captured))
- [Step 5: Prove Completion (`proof:completion-proven`)](#step-5:-prove-completion-(proof:completion-proven))
- [Definition of Done](#definition-of-done)
- [Acceptance Criteria](#acceptance-criteria)
- [Test Evidence](#test-evidence)
- [Conclusion](#conclusion)
- [Integration with Other Skills](#integration-with-other-skills)
- [With `scope-guard`](#with-scope-guard)
- [With `evidence-logging`](#with-evidence-logging)
- [With `superpowers:execute-plan`](#with-superpowers:execute-plan)
- [Validation Checklist (Before Claiming "Done")](#validation-checklist-(before-claiming-"done"))
- [Pre-Completion Validation](#pre-completion-validation)
- [Completion Statement Format](#completion-statement-format)
- [Red Flag Self-Check](#red-flag-self-check)
- [Module Reference](#module-reference)
- [Related Skills](#related-skills)
- [Exit Criteria](#exit-criteria)


# Proof of Work

**Philosophy:** "Trust, but verify" is wrong. "Verify, THEN trust" is correct.

## The Problem This Solves

**Anti-Pattern:**
> "I've configured LSP for you. Just restart your session and it will work!"
>
> *Reality: Didn't test if cclsp starts, didn't verify tools are exposed, didn't check for known bugs.*

**Correct Pattern:**
> "Let me verify LSP configuration works..."
> ```bash
> # Test cclsp starts
> CCLSP_CONFIG_PATH=... npx cclsp@latest &
> # Verify language servers respond
> pylsp --help
> # Check for known issues
> <web search for bugs in current version>
> ```
> "Found critical issue: Claude Code 2.0.76 has broken LSP (Issue #14803). Here's proof..."

## Core Principle

Before claiming completion, you must provide evidence that the solution actually works (tested), edge cases are handled (validated), claims are accurate (proven), and future verification is possible (reproducible).

## The Iron Law

```
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
NO COMPLETION CLAIM WITHOUT EVIDENCE FIRST
```

The Iron Law prevents **Cargo Cult TDD** - going through the motions of testing without achieving the design benefits. When implementation is pre-planned before tests, the RED phase becomes theater.

**Iron Law Self-Check (Before Writing Code):**

| Question | If "No" or "Yes" | Action |
|----------|------------------|--------|
| Do I have documented evidence of a failure/need? | No | STOP - document failure first |
| Am I about to write a test that validates a pre-conceived implementation? | Yes | STOP - let test DRIVE design |
| Am I feeling uncertainty about the design? | No | STOP - uncertainty is GOOD, explore it |
| Have I let the test drive the implementation? | No | STOP - you're doing it backwards |

**Extended TodoWrite Items for TDD:**
- `proof:iron-law-red` - Failing test written BEFORE implementation
- `proof:iron-law-green` - Minimal implementation passes test
- `proof:iron-law-refactor` - Code improved without behavior change
- `proof:iron-law-coverage` - Coverage gates passed (line/branch/mutation)

See [iron-law-enforcement.md](modules/iron-law-enforcement.md) for adversarial verification, git history analysis, and pre-commit hook enforcement patterns.

## When to Use

### MANDATORY Usage (Non-Negotiable)

This skill is required before any statement like "this will work", "should work", or "is ready". Apply it before claiming configuration or setup is complete, before recommending solutions without testing them, before saying "done" or "finished", and before telling users to "try this" or "restart and test".

### Red Flags (You're About to Violate This)

| Thought Pattern | Reality Check |
|----------------|---------------|
| "This configuration looks correct" | Did you TEST it works? |
| "After restart it should work" | Did you VERIFY the restart fixes it? |
| "The setup is complete" | Did you PROVE each component functions? |
| "Just enable X and Y" | Did you CHECK for known issues? |
| "This will fix your problem" | Did you REPRODUCE the problem first? |
| "The language servers are installed" | Did you CONFIRM they respond correctly? |

## Required TodoWrite Items

When applying this skill, create these todos:

1. `proof:problem-reproduced` - Verified the issue exists
2. `proof:solution-tested` - Tested proposed solution works
3. `proof:edge-cases-checked` - Validated common failure modes
4. `proof:evidence-captured` - Logged evidence per evidence-logging skill
5. `proof:completion-proven` - Demonstrated acceptance criteria met

## Validation Protocol

### Step 1: Reproduce the Problem (`proof:problem-reproduced`)

**BEFORE proposing a solution:**

```bash
# Example: User says LSP doesn't work
# FIRST: Verify current state
ps aux | grep cclsp                    # Is it running?
echo $ENABLE_LSP_TOOL                 # Is env var set?
cat ~/.claude/.mcp.json | grep cclsp   # Is it configured?
```
**Verification:** Run the command with `--help` flag to verify availability.

**Evidence Required:**
- Command output showing current state
- Error messages or logs confirming the issue
- Environment verification (versions, paths, configs)

### Step 2: Test the Solution (`proof:solution-tested`)

**BEFORE claiming "this will work":**

```bash
# Example: Testing if cclsp can start
CCLSP_CONFIG_PATH=/path/to/config npx cclsp@latest 2>&1 &
sleep 3
ps aux | grep cclsp | grep -v grep

# Did it actually start? Capture the output
tail /tmp/cclsp-test-output.log
```
**Verification:** Run `pytest -v` to verify tests pass.

**Evidence Required:**
- Successful execution of proposed solution
- Actual output (not assumed output)
- Confirmation of expected behavior

### Step 3: Check for Known Issues (`proof:edge-cases-checked`)

**BEFORE recommending approach:**

```bash
# Example: Research known bugs
<web search for "claude code LSP 2.0.76 issues">
<check GitHub issues for current version>
<verify language server compatibility>
```
**Verification:** Run the command with `--help` flag to verify availability.

**Evidence Required:**
- Search results for known issues
- Version compatibility checks
- Common gotchas or limitations

### Step 4: Capture Evidence (`proof:evidence-captured`)

Use `imbue:evidence-logging` to document:

```markdown
[E1] Command: ps aux | grep cclsp
     Output: <no cclsp processes found>
     Timestamp: 2025-12-31T22:07:00Z
     Conclusion: cclsp not running despite config

[E2] Web Search: "claude code 2.0.76 LSP bugs"
     Finding: Issue #14803 - LSP broken in 2.0.69-2.0.76
     Source: https://github.com/anthropics/claude-code/issues/14803
     Impact: User's version is affected by known bug

[E3] Command: CCLSP_CONFIG_PATH=... npx cclsp@latest
     Output: "configPath is required when CCLSP_CONFIG_PATH not set"
     Conclusion: Environment variable not being passed correctly
```
**Verification:** Run `pytest -v` to verify tests pass.

### Step 5: Prove Completion (`proof:completion-proven`)

**Acceptance Criteria Format:**

```markdown
## Definition of Done

User can successfully use LSP tools after following these steps:

### Acceptance Criteria
- [ ] cclsp MCP server starts without errors
- [ ] Language servers (pylsp, typescript-language-server) respond
- [ ] LSP tools (find_definition, find_references) are callable
- [ ] No known bugs in current Claude Code version block functionality

### Test Evidence
- [E1] cclsp process running: PASS (see evidence)
- [E2] pylsp responds: PASS (see evidence)
- [E3] LSP tools available: FAIL - **BLOCKED by bug #14803**

### Conclusion
Cannot claim completion due to fundamental blocker identified. Can provide: diagnosis with evidence, workaround options, and next steps.
```
**Verification:** Run `pytest -v` to verify tests pass.

## Integration with Other Skills

### With `scope-guard`

**Before implementation:**
- scope-guard: "Should we build this?"
- proof-of-work: (not yet applicable)

**After implementation:**
- proof-of-work: "Did we actually complete it?"

### With `evidence-logging`

- evidence-logging: HOW to capture evidence
- proof-of-work: WHEN to capture evidence (always, before completion)

### With `superpowers:execute-plan`

**During execution:**
- Execute task step
- proof-of-work: Validate step completed successfully
- evidence-logging: Document proof
- Move to next step

### With Improvement Workflows (`/update-plugins`, `/fix-workflow`)

**Critical Integration:** proof-of-work is MANDATORY for validating continuous improvement changes.

#### /update-plugins Phase 2 Validation

When `/update-plugins` identifies improvement opportunities, use proof-of-work to validate:

```markdown
## Proof-of-Work: Improvement Analysis Validation

### Problem Reproduced (`proof:problem-reproduced`)
[E1] Command: `/skill-review --plugin sanctum --recommendations`
Output:
```
sanctum:workflow-improvement
  Stability gap: 0.35 ⚠️ (unstable)
  5 failures in 7 days
  Common error: "Missing validation in Step 2"
```
Conclusion: Unstable skill identified with concrete metrics

### Solution Tested (`proof:solution-tested`)
[E2] Command: `git log --oneline --grep="fix\|improve" --since="30 days ago" -- plugins/sanctum/skills/workflow-improvement/`
Output: 8 commits found
Conclusion: High churn rate confirms instability signal

### Edge Cases Checked (`proof:edge-cases-checked`)
[E3] Web Search: "workflow-improvement skill best practices"
Finding: Early validation reduces iteration by 30% (from PR #42 lesson)
Conclusion: Known pattern that should be applied

### Completion Proven (`proof:completion-proven`)
✓ Unstable skill identified with quantitative metrics
✓ Root cause traced through git history
✓ Improvement recommendation generated with evidence
✓ TodoWrite item created: `improvement:sanctum:workflow-improvement-validation`
```

#### /fix-workflow Phase 0 Validation

When `/fix-workflow` gathers improvement context, use proof-of-work to validate data sources:

```markdown
## Proof-of-Work: Context Gathering Validation

### Data Sources Verified (`proof:problem-reproduced`)
[E1] Skill logs accessible:
Command: `ls ~/.claude/skills/logs/`
Output: abstract/ .history.json
Conclusion: Logging infrastructure functional

[E2] Git history available:
Command: `git log --oneline --since="30 days ago" | wc -l`
Output: 47 commits
Conclusion: Sufficient history for pattern analysis

[E3] Memory-palace integration:
Command: `[ -d ~/.claude/skills/logs ] && echo "exists" || echo "missing"`
Output: exists
Conclusion: Can query skill execution history

### Analysis Validated (`proof:solution-tested`)
[E4] Recent failures identified:
Command: `/skill-logs --failures-only --last 7d`
Output: 3 failure patterns found
Conclusion: Concrete issues to address

### Implementation Proven (`proof:completion-proven`)
✓ All data sources accessible and functional
✓ Context gathering steps verified
✓ Improvement vectors identified with evidence
✓ Ready to proceed with retrospective analysis
```

#### /fix-workflow Step 7 Validation

When closing the loop after improvements, use proof-of-work to validate impact:

```markdown
## Proof-of-Work: Improvement Impact Validation

### Before Metrics Captured (`proof:problem-reproduced`)
[E1] Baseline metrics:
- Step count: 15
- Failure rate: 20% (3/15)
- Duration: 8.5 minutes

### After Metrics Captured (`proof:solution-tested`)
[E2] Post-improvement metrics:
Command: Re-run workflow with changes
- Step count: 11 (-27%)
- Failure rate: 0% (-100%)
- Duration: 5.2 minutes (-39%)

### Impact Validated (`proof:completion-proven`)
✓ Quantitative improvement demonstrated
✓ Failure modes eliminated with evidence
✓ Performance gain verified
✓ Lesson stored for future reference
```

## Validation Checklist (Before Claiming "Done")

```markdown
### Pre-Completion Validation

- [ ] Problem reproduced with evidence
- [ ] Solution tested in actual environment
- [ ] Known issues researched (web search, GitHub, docs)
- [ ] Edge cases considered (what could go wrong?)
- [ ] Evidence captured in reproducible format
- [ ] Acceptance criteria defined and met
- [ ] User can independently verify claims

### Completion Statement Format

Instead of: "LSP is configured. Restart and it will work."

Required:
"I've verified your LSP configuration with these tests:
- [PASS] cclsp installed and configured in .mcp.json [E1]
- [PASS] Language servers installed and responsive [E2]
- [FAIL] LSP tools unavailable - discovered bug #14803 [E3]

**Proven Status:** Blocked by known issue in Claude Code 2.0.76
**Evidence:** See [E3] web search results
**Options:** 1) Downgrade to 2.0.67, 2) Wait for bug fix
**Cannot claim:** 'LSP will work after restart' (proven false)"
```
**Verification:** Run `pytest -v` to verify tests pass.

## Red Flag Self-Check

**Before sending completion message, ask:**

1. **Did I actually RUN the commands I'm recommending?**
   - No → STOP, test them first
   - Yes → Capture output as evidence

2. **Did I search for known issues with this approach?**
   - No → STOP, research first
   - Yes → Document findings

3. **Can the user reproduce my validation steps?**
   - No → STOP, make it reproducible
   - Yes → Include steps in response

4. **Am I assuming vs. proving?**
   - Assuming → STOP, test your assumptions
   - Proving → Show the proof

5. **Would I accept this level of validation from a coworker?**
   - No → STOP, raise the bar
   - Yes → Proceed with completion claim

## Module Reference

- **[validation-protocols.md](modules/validation-protocols.md)** - Detailed test protocols
- **[acceptance-criteria.md](modules/acceptance-criteria.md)** - Definition of Done templates
- **[red-flags.md](modules/red-flags.md)** - Common anti-patterns and violations
- **[iron-law-enforcement.md](modules/iron-law-enforcement.md)** - TDD enforcement patterns, adversarial verification, git history analysis, and coverage gates

### Cross-Skill Modules

- **[iron-law-interlock.md](../../../abstract/shared-modules/iron-law-interlock.md)** - Hard gate for creation workflows (commands, skills, hooks)

## Related Skills

- `imbue:evidence-logging` - How to capture and format evidence
- `imbue:scope-guard` - Prevents building wrong things (complements this)
- `pensive:code-reviewer` - Uses proof-of-work for validation claims

## Exit Criteria

- All TodoWrite items completed
- Evidence log created with reproducible proofs
- Acceptance criteria defined and validated
- User can independently verify all claims
- Known blockers identified and documented
## Troubleshooting

### Common Issues

**Command not found**
Ensure all dependencies are installed and in PATH

**Permission errors**
Check file permissions and run with appropriate privileges

**Unexpected behavior**
Enable verbose logging with `--verbose` flag
