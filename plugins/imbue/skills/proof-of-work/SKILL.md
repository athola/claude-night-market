---
name: proof-of-work
description: |
  Enforces "prove before claim" discipline - validation, testing, and evidence requirements before declaring work complete.
  Triggers: validation, definition-of-done, proof, acceptance-criteria, testing, completion, finished, done, working, should work, configured, ready to use, implemented, fixed, improvement validated, workflow optimized, performance improved, issue resolved.
  Use when claiming work is complete, recommending solutions, or finishing implementations.
  Do not use when asking questions or for work clearly in-progress.
  MANDATORY: This skill is required before any completion claim.
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

- [Overview](#overview)
- [The Iron Law](#the-iron-law)
- [Usage Standards](#usage-standards)
- [Validation Protocol](#validation-protocol)
- [Definition of Done](#definition-of-done)
- [Integration with Other Skills](#integration-with-other-skills)
- [Validation Checklist](#validation-checklist-before-claiming-done)
- [Red Flag Self-Check](#red-flag-self-check)
- [Module Reference](#module-reference)
- [Related Skills](#related-skills)
- [Exit Criteria](#exit-criteria)


# Proof of Work

## Overview

The "Proof of Work" methodology prevents premature completion claims by requiring technical verification before stating that a task is finished. For example, rather than assuming an LSP configuration will work after a restart, we verify that the server starts and that tools respond correctly. This approach ensures that the user is not left to perform the final validation and avoids inaccurate status updates.

Before claiming completion, you must provide reproducible evidence that the solution works and that edge cases have been addressed. All claims must be backed by actual command output captured in the current environment.

## The Iron Law

**NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST**
**NO COMPLETION CLAIM WITHOUT EVIDENCE FIRST**
**NO CODE WITHOUT UNDERSTANDING FIRST**

The Iron Law prevents testing from becoming a perfunctory exercise. If an implementation is planned before tests are written, the RED phase fails to drive the design. You must understand WHY an approach was selected and what its limitations are before declaring it done. Before writing any code, confirm that you have documented evidence of the failure you are trying to solve, and ensure that your tests are driving the implementation rather than merely validating pre-conceived logic.

### Verification and TDD Workflow

Before claiming completion, verify you understand the fundamentals of the implementation and why it was chosen over alternatives. Identifying where a solution might fail is more important than stating it should always work. The TDD cycle follows these mandatory steps:

1. **RED**: Write a failing test before implementation.
2. **GREEN**: Create a minimal implementation that passes the test.
3. **REFACTOR**: Improve the code without changing its behavior.

### Iron Law TodoWrite Items

- `proof:iron-law-red` - Failing test written BEFORE implementation
- `proof:iron-law-green` - Minimal implementation passes test
- `proof:iron-law-refactor` - Code improved without behavior change
- `proof:iron-law-coverage` - Coverage gates passed (line/branch/mutation)

### Iron Law Self-Check

| Self-Check Question | If Answer Is Wrong | Action |
|---------------------|-------------------|--------|
| Do I have documented evidence of failure/need? | No | STOP - document failure first |
| Am I testing pre-conceived implementation? | Yes | STOP - let test DRIVE design |
| Am I feeling uncertainty about the design? | No | STOP - uncertainty is GOOD, explore it |
| Did the test drive the implementation? | No | STOP - doing it backwards |

Verify that your work passes all line, branch, and mutation coverage gates. For detailed enforcement patterns, including git history analysis and pre-commit hooks, see [iron-law-enforcement.md](modules/iron-law-enforcement.md).

## Usage Standards

This skill is required before any statement that work is "done," "finished," or "ready." You must apply it before recommending solutions without testing them or telling users that a configuration "should work."

Stop immediately if you find yourself assuming a configuration is correct without testing it, or if you are about to recommend a fix without first reproducing the problem. Red flags include thinking "this looks correct" or "it should work after a restart" without actual verification. If you cannot explain each line of a configuration or why a specific best practice applies to your current context, you are likely skipping the necessary validation steps.

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
[E1] Command: `pensive:skill-review --plugin sanctum --recommendations`
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

If you cannot reproduce the problem (Step 1), verify your environment matches the user's (e.g., check `node --version`, `python --version`). If validation fails (Step 2), capture the full error output rather than summarizing. If known issues are not found (Step 3) but the error persists, check recent GitHub issues or forum discussions for similar reports.
