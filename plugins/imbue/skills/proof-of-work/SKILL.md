---
name: proof-of-work
description: |
  Enforces "prove before claim" discipline - validation, testing, and evidence
  requirements before declaring work complete.

  Triggers: completion, finished, done, working, should work, configured,
  ready to use, implemented, fixed

  Use when: claiming ANY work is complete, recommending solutions, stating
  something will work, finishing implementations

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
---

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
echo $ENABLE_LSP_TOOLS                 # Is env var set?
cat ~/.claude/.mcp.json | grep cclsp   # Is it configured?
```

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
