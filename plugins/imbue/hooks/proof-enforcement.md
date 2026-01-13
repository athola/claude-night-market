---
name: proof-enforcement
description: |
  Enforces proof-of-work discipline and the Iron Law before completion claims.
  IMPLEMENTATION STATUS: Enforced via SessionStart governance injection
  and Stop hook checklist (see actual implementation below).

  The Iron Law: NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
  This prevents "Cargo Cult TDD" where tests validate pre-conceived implementations
  rather than driving design through uncertainty exploration.
triggers:
  - SessionStart (governance injection)
  - Stop (completion checklist)
priority: critical
---

# Proof Enforcement Hook

**Purpose:** Prevent completion claims without evidence and enforce the Iron Law for TDD compliance.

## Implementation Status

> **NOTE**: Claude Code does not support `PreMessageSend` hook type.
> Proof-of-work enforcement is implemented via:
>
> 1. **SessionStart** - `sanctum/hooks/post_implementation_policy.py`
>    - Injects proof-of-work as STEP 1 of governance protocol
>    - Includes red flags table for rationalization detection
>
> 2. **Stop** - `sanctum/hooks/verify_workflow_complete.py`
>    - End-of-session checklist includes proof-of-work items
>    - Warns if proof-of-work was skipped
>
> 3. **SessionStart** - `imbue/hooks/session-start.sh`
>    - Injects proof-of-work quick reference alongside scope-guard
>
> The patterns below remain useful as **guidance for self-enforcement**.

## Completion Signal Detection (Self-Enforcement Guide)

### Patterns That Should Trigger Self-Validation

**Direct Completion Claims:**
- "done", "finished", "complete", "completed"
- "ready to use", "all set", "you're good to go"
- "setup is complete", "configuration is done"
- "implemented", "built", "created", "added"

**Implicit Completion Claims:**
- "should work", "will work", "it'll work"
- "just restart", "simply run", "all you need to do"
- "this fixes", "this resolves", "this solves"
- "now you can", "you can now", "you're able to"

**Recommendation Patterns:**
- "recommend", "suggest", "advise", "propose"
- "the best approach", "the recommended way"
- "you should", "I'd recommend"

## Validation Rules

### Rule 1: Evidence Required

**If message contains completion signal AND lacks evidence markers:**

❌ **BLOCK MESSAGE**

**Evidence markers to look for:**
- `[E1]`, `[E2]`, etc. (evidence references)
- `` ```bash\n<command>\n``` `` (actual command execution)
- "Tested with:", "Verified by:", "Evidence:"
- "✅ PASS / ❌ FAIL" (test results)

**Enforcement:**
```
⚠️ PROOF-OF-WORK VIOLATION DETECTED

Message contains completion claim but lacks evidence.

Completion signal: "setup is complete"
Missing: Evidence references, command outputs, test results

REQUIRED BEFORE SENDING:
1. Invoke Skill(imbue:proof-of-work)
2. Run validation protocol for this scenario
3. Capture evidence with references
4. Update message with proof

DO NOT SEND MESSAGE WITHOUT EVIDENCE.
```

---

### Rule 2: Test Commands Required

**If message recommends commands/scripts AND hasn't run them:**

❌ **BLOCK MESSAGE**

**Test for:**
- Are there `bash` code blocks with commands?
- Is there output showing these commands were run?
- Are there error cases handled?

**Enforcement:**
```
⚠️ UNTESTED COMMANDS DETECTED

Message contains command recommendations but no evidence they were tested.

Commands found:
- `npm install -g cclsp`
- `export ENABLE_LSP_TOOL=1`

REQUIRED:
1. Run each command in test environment
2. Capture actual output
3. Document any errors or warnings
4. Verify expected behavior

Example:
[E1] Testing installation:
$ npm install -g cclsp
<actual output>
Result: ✅ Installed successfully
```

---

### Rule 3: Known Issues Research

**If message recommends approach AND hasn't researched issues:**

⚠️ **WARNING** (not blocking, but strongly recommended)

**Check for:**
- Web search results cited
- GitHub issues referenced
- Version compatibility mentioned
- Known limitations documented

**Enforcement:**
```
⚠️ INSUFFICIENT RESEARCH DETECTED

Message recommends solution but doesn't cite known issues research.

Recommendation: "Use cclsp MCP server for LSP"

RECOMMENDED:
1. Search for known bugs in this approach
2. Check GitHub issues for project + version
3. Verify version compatibility
4. Document any limitations found

Example:
[E3] Known issues research:
$ <web search: "claude code cclsp issues 2.0.76">
Found: Issue #14803 - LSP broken in 2.0.69-2.0.76
Impact: Blocks recommended approach
```

---

### Rule 4: Iron Law TDD Compliance

**If message claims implementation complete AND lacks TDD evidence:**

❌ **BLOCK MESSAGE**

**Check for Iron Law compliance:**
- Is there evidence of a failing test BEFORE implementation?
- Did the test drive the design, or was design pre-planned?
- Are there RED/GREEN/REFACTOR commits in git history?

**Evidence markers to look for:**
- `proof:iron-law-red` - Failing test evidence
- `proof:iron-law-green` - Minimal implementation evidence
- `[E-TDD1]`, `[E-TDD2]`, `[E-TDD3]` - TDD phase evidence
- Git commit references showing test-before-implementation

**Enforcement:**
```
IRON LAW VIOLATION DETECTED

Message claims implementation complete but lacks TDD evidence.

Missing:
- No evidence of failing test BEFORE implementation
- No RED/GREEN/REFACTOR commit pattern
- No coverage gate evidence

REQUIRED:
1. Show evidence of failing test written FIRST
2. Show minimal implementation to pass test
3. Show refactoring with tests still green
4. Include coverage evidence (line/branch/mutation)

If TDD was NOT followed:
- Acknowledge the violation
- Explain what rationalization led to it
- Add comprehensive tests retroactively
- Update configuration to prevent future violations
```

---

### Rule 5: Acceptance Criteria Defined

**If message claims "done" AND lacks acceptance criteria:**

❌ **BLOCK MESSAGE**

**Required format:**
```markdown
## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Test Evidence
- Criterion 1: [E1] → ✅ PASS
- Criterion 2: [E2] → ❌ FAIL

## Status
❌ BLOCKED / ⚠️ PARTIAL / ✅ COMPLETE
```

**Enforcement:**
```
⚠️ MISSING ACCEPTANCE CRITERIA

Message claims completion but doesn't define success criteria.

Claim: "LSP setup is complete"

REQUIRED:
1. Define testable acceptance criteria
2. Test each criterion
3. Provide evidence for each
4. Report status (COMPLETE/PARTIAL/BLOCKED)

Use Skill(imbue:proof-of-work) acceptance-criteria template.
```

---

## Actual Enforcement Mechanism

> **NOTE**: Claude Code cannot intercept outgoing messages. Enforcement works via:
>
> 1. **SessionStart Injection** - Governance policy reminds about proof-of-work
> 2. **Stop Hook Checklist** - End-of-session reminder if proof-of-work was skipped
> 3. **Self-Enforcement** - Claude recognizes completion patterns and self-validates

**Self-enforcement triggers when Claude detects:**

1. **Completion claim patterns** in the response being composed
2. **Lack of evidence markers** (`[E1]`, `[E2]`, test results)
3. **Self-invoke:** `Skill(imbue:proof-of-work)` before claiming completion
4. **Capture evidence** and report status before proceeding

## Exemptions

**These message types bypass proof-enforcement:**

1. **Questions** - Asking for clarification
   - "What version of Claude Code are you using?"
   - "Can you show me your .mcp.json file?"

2. **In-Progress Updates** - Explicit work-in-progress
   - "Working on this now..."
   - "In progress: testing configuration..."
   - "Still investigating..."

3. **Exploratory Analysis** - Presenting findings, not claiming completion
   - "Found these potential issues..."
   - "Analysis shows..."
   - "Evidence suggests..." (when used for analysis, not completion)

4. **Explicit User Request** - User explicitly waives proof
   - User: "Skip validation, just give me your best guess"
   - Note: Should still warn user, but can proceed

## Detection Logic

```python
def requires_proof_of_work(message: str) -> bool:
    """Check if message requires proof-of-work validation."""

    # Completion signals
    completion_patterns = [
        r'\b(done|finished|complete|completed)\b',
        r'\bready to (use|go|test)\b',
        r'\b(setup|configuration|installation) is (done|complete)\b',
        r'\b(should|will|would) work\b',
        r'\bjust (restart|run|install|enable)\b',
        r'\b(implemented|built|created|added|fixed)\b',
        r'\byou can now\b',
        r'\ball set\b',
    ]

    has_completion_signal = any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in completion_patterns
    )

    if not has_completion_signal:
        return False  # No completion claim, no proof needed

    # Check for exemptions
    question_patterns = [r'\?$', r'^(what|how|why|when|where|which|can you)\b']
    is_question = any(
        re.search(pattern, message, re.IGNORECASE | re.MULTILINE)
        for pattern in question_patterns
    )

    in_progress_patterns = [r'\bin progress\b', r'\bworking on\b', r'\bstill\b']
    is_in_progress = any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in in_progress_patterns
    )

    if is_question or is_in_progress:
        return False  # Exempted

    # Check for evidence markers
    evidence_patterns = [
        r'\[E\d+\]',  # Evidence references
        r'```bash\n.*\n```.*\nResult:',  # Command with result
        r'✅ (PASS|COMPLETE)|❌ (FAIL|BLOCKED)',  # Test results
        r'(Tested|Verified|Evidence):',  # Explicit markers
    ]

    has_evidence = any(
        re.search(pattern, message, re.IGNORECASE | re.DOTALL)
        for pattern in evidence_patterns
    )

    if not has_evidence:
        return True  # Completion claim WITHOUT evidence = violation

    return False  # Has evidence, validation passed
```

## Integration with Other Hooks

**Coordinates with:**

- `scope-guard-integration.md` - Handles feature evaluation
- `imbue:evidence-logging` - Handles evidence format
- `superpowers:using-superpowers` - Works within skill system

**Execution order:**
1. `scope-guard` (before implementation) - SessionStart injection
2. Implementation work
3. `proof-of-work` (self-invoke before completion claim)
4. Completion with evidence

## Configuration

**Enforcement is automatic** when imbue and sanctum plugins are installed:

1. **Governance injection**: `sanctum/hooks/post_implementation_policy.py`
   - Proof-of-work is Step 1 of the mandatory protocol
   - Includes red flags table for rationalization detection

2. **Stop checklist**: `sanctum/hooks/verify_workflow_complete.py`
   - End-of-session reminder includes proof-of-work items

3. **Session reminder**: `imbue/hooks/session-start.sh`
   - Proof-of-work quick reference alongside scope-guard

**Disable via environment variable:**
```bash
# Skip proof-of-work enforcement (not recommended)
export PROOF_OF_WORK_DISABLE=1
```

## Metrics

**Track violations to improve discipline:**

```markdown
## Proof-of-Work Violations Log

| Date | Violation Type | Message | Resolution |
|------|---------------|---------|------------|
| 2025-12-31 | Missing evidence | "LSP is configured, restart to use" | Added testing evidence [E1-E5] |
| 2025-12-31 | Untested commands | "Run `npm install cclsp`" | Tested command, found issue |
```

## Example: Full Enforcement Flow

**Attempted message:**
> "I've configured LSP for you. The .cclsp.json file is set up correctly and cclsp is in your MCP config. Just restart Claude Code and the LSP tools will be available."

**Hook detection:**
```
⚠️ PROOF-OF-WORK VIOLATION DETECTED

Completion signals found:
- "configured LSP for you"
- "set up correctly"
- "just restart"
- "will be available"

Evidence markers found: NONE

BLOCKING MESSAGE - INSUFFICIENT EVIDENCE
```

**Auto-invoke:**
```
Invoking Skill(imbue:proof-of-work)...

Validation protocol: Configuration Validation
Required steps:
1. Test cclsp starts
2. Verify language servers connect
3. Confirm LSP tools exposed
4. Research known issues
```

**After validation:**
> "I attempted to validate your LSP configuration and discovered a critical issue:
>
> [E1] Testing cclsp startup:
> ```bash
> $ CCLSP_CONFIG_PATH=config.json npx cclsp@latest
> # Output shows language servers timeout
> ```
> Result: ⚠️ Starts but servers don't initialize
>
> [E2] Research of known issues:
> Web search found Issue #14803: LSP broken in Claude Code 2.0.69-2.0.76
> Source: https://github.com/anthropics/claude-code/issues/14803
>
> ## Status
> ❌ BLOCKED - Cannot claim LSP is ready due to version bug
>
> ## Options
> 1. Downgrade to Claude Code 2.0.67 (proven working)
> 2. Wait for fix in future release"

**Result:** Message now contains evidence and accurate status. ✅ Allowed to send.
