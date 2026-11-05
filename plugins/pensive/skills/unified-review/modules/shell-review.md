# Shell Script Review

Audit shell scripts for correctness, safety, and portability. Load this
module from `Skill(pensive:unified-review)` when shell scripts are in
scope, or run it alone with `/shell-review` or `/full-review shell`.

After review, run `shellcheck <script>` to verify fixes address the
identified issues. Run
`pytest plugins/pensive/tests/skills/test_shell_review.py -v` to
validate the review patterns.

## When To Use

- CI/CD pipeline scripts
- Git hook scripts
- Wrapper scripts (run-*.sh)
- Build automation scripts
- Pre-commit hook implementations

## When NOT To Use

- Non-shell scripts (Python, JS, etc.)
- One-liner commands that don't need review

## Required Progress Items

1. `shell-review:context-mapped`
2. `shell-review:exit-codes-checked`
3. `shell-review:portability-checked`
4. `shell-review:safety-patterns-verified`
5. `shell-review:structure-checked`
6. `shell-review:evidence-logged`
7. `shell-review:findings-verified`

## Workflow

### Step 1: Map Context (`shell-review:context-mapped`)

Identify shell scripts:
```bash
# Find shell scripts
find . -not -path "*/.venv/*" -not -path "*/__pycache__/*" \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -name "*.sh" -type f | head -20
# Check shebangs
rg -l "^#!/" scripts/ hooks/ 2>/dev/null | head -10
# fallback: grep -l "^#!/" scripts/ hooks/ 2>/dev/null | head -10
```

Document:
- Script purpose and trigger context
- Integration points (make, pre-commit, CI)
- Expected inputs and outputs

### Step 2: Exit Code Audit (`shell-review:exit-codes-checked`)

@include modules/shell-exit-codes.md

### Step 3: Portability Check (`shell-review:portability-checked`)

@include modules/shell-portability.md

### Step 4: Safety Patterns (`shell-review:safety-patterns-verified`)

@include modules/shell-safety-patterns.md

### Step 5: Structure Patterns (`shell-review:structure-checked`)

@include modules/shell-structure-patterns.md

### Step 6: Evidence Log (`shell-review:evidence-logged`)

Use `imbue:proof-of-work` to record findings with file:line references.

Summarize:
- Critical issues (failures masked, security risks)
- Major issues (portability, maintainability)
- Minor issues (style, documentation)

## Output Format

```markdown
## Summary
Shell script review findings

## Scripts Reviewed
- [list with line counts]

## Exit Code Issues
### [E1] Pipeline masks failure
- Location: script.sh:42
- Anchor: `verbatim source text at file:line`
- Pattern: `cmd | grep` loses exit code
- Fix: Use pipefail or capture separately

## Portability Issues
[cross-platform concerns]

## Safety Issues
[unquoted variables, missing set flags]

## Recommendation
Approve / Approve with actions / Block
```

## Verify Findings Are Grounded (`shell-review:findings-verified`)

Write findings to `.review/findings.json`, run the citation verifier
(`Skill(imbue:review-core)` Step 5), and drop or label `UNVERIFIED` any
the verifier rejects.

## Exit Criteria

- [ ] Exit code propagation verified (pipelines checked for pipefail or
  capture-and-check)
- [ ] Portability issues documented (Bash-isms in `#!/bin/sh` scripts flagged)
- [ ] Safety patterns verified (no echo, braced vars, `:?` expansion, cd in
  subshells, no basename/dirname)
- [ ] Structure patterns verified (library/executable distinction, main call,
  preamble, depcheck, shfmt formatting)
- [ ] Evidence logged with file:line references via `imbue:proof-of-work`
- [ ] Every reported finding carries a `Location` + verbatim `Anchor`
  confirmed by `citation_verifier.py` (exit `0`), or unverified findings
  were dropped or labeled `UNVERIFIED`
