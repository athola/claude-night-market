---
name: fixit
description: Fix broken functionality from pasted error output, stack traces, or
  failing-behavior descriptions using research, TDD, and proof-of-work evidence.
usage: /fixit <pasted-error-or-description> [--file <path>] [--scope auto|minor|medium|major]
  [--from <step>] [--to <step>] [--research|--no-research] [--strict|--quick]
  [--commit] [--dry-run]
extends: "imbue:proof-of-work"
---

# Fix It

A progressive workflow for fixing broken functionality from a pasted body of
output: error codes, stack traces, failing test logs, incorrect program output,
or a freeform description of "this is wrong, here's what I expected." Follows
the sanctum pattern:

**triage** → **reproduce** → **research** → **hypothesize** → **test (RED)** →
**fix (GREEN)** → **verify** → **report**

## When To Use

Use this command when you need to:

- Take a pasted block of error output, stack trace, or broken behavior and
  drive it to a verified fix
- Reproduce a defect, write a failing test, then fix it under the Iron Law
- Fix something where you do not yet know the root cause and need a stepwise
  diagnostic path

## When NOT To Use

- The fix is in a PR review thread: use `/sanctum:fix-pr` instead
- The work is tracked in a GitHub or GitLab issue: use `/sanctum:do-issue`
- The retrospective is about a slow or fragile workflow itself, not a code
  defect: use `/sanctum:fix-workflow`
- You are exploring code without a known failure: use `/feature-dev:feature-dev`
  or read the code directly

## Quick Reference

```bash
/fixit "TypeError: 'NoneType' object is not subscriptable at parser.py:88"
/fixit --file /tmp/build.log              # Read input from a file
/fixit --scope minor --quick              # Skip research, allow direct fix
/fixit --from hypothesize                 # Already reproduced, jump to ladder
/fixit --to test                          # Stop after RED test (dry-run-ish)
/fixit --strict                           # Force Iron Law even with --quick
/fixit --research                         # Force tome:research even on minor
/fixit --commit                           # Auto-commit via sanctum:acp on green
/fixit --dry-run                          # Plan only, no edits or commands
```

## Workflow Steps Overview

| # | Step | Purpose | Skill invoked | Skip when |
|---|------|---------|---------------|-----------|
| 1 | Triage | Parse input, classify failure type, extract artifacts | inline classifier (see below) | `--from` overrides |
| 2 | Reproduce | Capture failing state as evidence `[E1]` | `Skill(imbue:proof-of-work)` | failure already running |
| 3 | Research | Find prior art for novel errors | `Skill(tome:code-search)` or `Skill(tome:research)` | scope=minor or `--no-research` |
| 4 | Hypothesize | Build hypothesis ladder, pick most-likely cause | `Skill(superpowers:systematic-debugging)` | cause is obvious from triage |
| 5 | Test (RED) | Write the failing test that captures the bug | `Skill(superpowers:test-driven-development)` and `Skill(imbue:proof-of-work)` iron-law-red | never (Iron Law) |
| 6 | Fix (GREEN) | Smallest change to make the test pass | `Skill(imbue:karpathy-principles)` (surgical-edits) | never |
| 7 | Verify | Run tests and capture evidence `[E2]`; confirm regression-free | `Skill(superpowers:verification-before-completion)` and `Skill(imbue:proof-of-work)` iron-law-green | never |
| 8 | Report | Summarize fix with evidence; optional commit | `Skill(sanctum:commit-messages)` and `/sanctum:acp` (with `--commit`) | default no-commit |

## The Iron Law (non-negotiable)

```
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
```

This command always enforces Iron Law. The only flag that softens it is
`--quick`, and even that requires the RED test. `--quick` only skips Research
and lets Triage feed Hypothesize directly; it does not skip the test.

If you find yourself wanting to skip the test, consult
`Skill(imbue:proof-of-work)` module `iron-law-enforcement.md` and
`Skill(imbue:rigorous-reasoning)` to check whether you are rationalizing.

## Intelligent Step-Skipping

Auto-detected scope shapes which phases run. Override with `--scope`.

**Minor scope** (typo, single-character fix, obvious signature mismatch,
trivial off-by-one):

- Skip: Research
- Run: Triage to Reproduce to Hypothesize to Test (RED) to Fix to Verify

**Medium scope** (logic bug with clear repro, single-file scope, known library
behavior):

- Skip: nothing by default
- Run: all phases

**Major scope** (novel error, unfamiliar library, multi-file blast radius,
concurrency or platform issue):

- Skip: nothing
- Run: all phases with extra emphasis on Research and Hypothesize

```bash
/fixit "..." --scope auto         # Detect from triage signals
/fixit "..." --scope minor        # Force minor
/fixit "..." --scope medium
/fixit "..." --scope major
```

## Step 1: Triage

**Purpose**: Parse the pasted input and classify it into a failure shape that
points the RED test at a specific assertion.

### 1.1 Parse the input

The input is `$ARGUMENTS` (a paste) or the contents of `--file <path>`. Strip
ANSI color codes and trim trailing whitespace. Identify and record:

- **Failure type**: compile error, type error, test failure, runtime crash,
  wrong output, hang or timeout, resource error, behavior mismatch
- **Language and framework signals**: file extensions, error message patterns,
  toolchain names (rustc, pytest, tsc, cargo, go, mypy, etc.)
- **Artifacts**: file paths, line numbers, error codes (E0382, TS2345, EPERM),
  stack frames, function or symbol names
- **Reproduction surface**: command that produced the output (if visible),
  inputs that triggered it (if visible)

### 1.2 Classify scope

Score the failure on three dimensions, then pick the scope:

| Signal | Minor | Medium | Major |
|--------|-------|--------|-------|
| Files touched (estimate) | 1 | 1 to 3 | 4 or more |
| Familiar error code? | yes | yes | no or rare |
| Library or platform involved? | std-lib only | known dep | unfamiliar dep, OS, FFI |

Two or more "minor" signals: scope is `minor`. Two or more "major" signals:
scope is `major`. Otherwise: `medium`.

### 1.3 Input classification rules (USER-AUTHORED)

The rules below are the user-authored heuristic that shapes how the rest of
the workflow runs. They map common pasted shapes (Python tracebacks, Rust
compiler diagnostics, pytest output, JSON parse errors, frontend console
output, build logs, etc.) to a triage record.

This is a customization point: tune the rules below to the failure shapes
you paste most often. Each rule produces a triage record with:

```text
  failure_type:    one of [compile, type, test, runtime, output, hang, resource, behavior]
  language:        e.g., python | rust | typescript | go | shell | unknown
  framework:       e.g., pytest | cargo | tsc | jest | unknown
  artifacts:       { files: [...], lines: [...], codes: [...], symbols: [...] }
  scope_signals:   counts for the table in 1.2
  red_test_hint:   one-sentence shape of the failing test to write in step 5

Starter rules (usable as-is; extend with the shapes you paste most):

  if input matches /Traceback \(most recent call last\)/:
      failure_type = "runtime"
      language     = "python"
      framework    = detect_from_paths(artifacts.files)
      red_test_hint = "call <last_user_frame_function> with the inputs from the
                       traceback; assert it does not raise <exception_type>."

  if input matches /error\[E\d{4}\]/:
      failure_type = "compile"
      language     = "rust"
      framework    = "cargo"
      red_test_hint = "construct the value the borrow checker rejected; assert it
                       compiles and returns the expected type."

  if input matches /FAILED .+::.+ - assert/:
      failure_type = "test"
      language     = "python"
      framework    = "pytest"
      red_test_hint = "isolate the failing assertion; assert the value the test
                       expects, then watch it go red before fixing."

Add rules for the formats you actually paste. Do not add rules for shapes
you have never seen; speculative coverage is bloat. Three to five solid
rules cover most days.
```

When triage cannot classify, fall back to `failure_type=behavior`,
`scope=medium`, and ask the user one clarifying question before continuing.

## Step 2: Reproduce

**Purpose**: Establish a reproducible failing state and capture evidence.

`Skill(imbue:proof-of-work)` requires a TodoWrite item
`proof:problem-reproduced` before any fix attempt. The reproduction must be a
single command or a short script that exits non-zero (or produces the wrong
output) every time.

Capture the run as `[E1]` with:

- The exact command
- The full failing output (or a representative slice)
- The environment (toolchain version, OS) if relevant

If the input is a paste with no command, derive a command from the artifacts
(for example, a pytest stack frame yields `pytest <file>::<test>`). If you
cannot derive one, ask the user.

**Stop condition**: the failure is reproducible from a captured command. If
not, do not proceed; ask the user for the missing piece.

## Step 3: Research (conditional)

**Purpose**: Find prior art for novel errors before guessing.

Run when scope is `medium` or `major` and `--no-research` is not set. Skip
when scope is `minor` or `--quick` is set, unless `--research` is set
explicitly.

- Unfamiliar error code or library: `Skill(tome:code-search)` for existing
  implementations and known fixes
- Cross-cutting design or paradigm question: `Skill(tome:research)` for a
  multi-source survey
- Known library, novel use: `Skill(tome:papers)` or
  `Skill(tome:discourse)` (rare)

Bound research to the budget set by `bounded-discovery` (8 file reads max for
implementation tasks). Stop when you have a candidate hypothesis, not when you
have a complete picture.

## Step 4: Hypothesize

**Purpose**: Build a small ladder of hypotheses, ranked by likelihood.

Use `Skill(superpowers:systematic-debugging)`. Produce 2 to 4 hypotheses and
pick the most-likely one with the smallest blast radius.

Apply `Skill(imbue:rigorous-reasoning)` if any hypothesis pattern-matches a
"common cause" answer; do not accept the first plausible cause without
evidence from step 2.

## Step 5: Test (RED) - Iron Law

**Purpose**: Write the failing test that captures the bug.

`Skill(imbue:proof-of-work)` requires a TodoWrite item `proof:iron-law-red`.
The test must:

- Fail before any fix is applied
- Fail for the right reason (the bug, not a typo in the test)
- Use the project's existing test framework (do not introduce a new one)
- Live in the project's existing test directory layout

`Skill(superpowers:test-driven-development)` covers framing. The
`red_test_hint` from triage step 1.3 is the starting point.

Capture the failing run as part of `[E1]` (or a fresh `[E1.test]`).

## Step 6: Fix (GREEN)

**Purpose**: Smallest change that makes the RED test pass.

Apply `Skill(imbue:karpathy-principles)` module `surgical-edits`. Avoid
adjacent refactors. New comments or docstrings must clear the project rule
at `.claude/rules/slop-scan-for-docs.md`.

Re-run the failing test. If it still fails, return to step 4 (hypothesis
ladder) rather than mutating the test or the fix repeatedly. Apply the
two-challenge rule from CLAUDE.md: after two failed attempts of the same
shape, switch to a read-only diagnostic step.

## Step 7: Verify

**Purpose**: Confirm the fix works and nothing else broke.

`Skill(superpowers:verification-before-completion)` requires running:

- The new RED test (must now PASS)
- The surrounding test file or module
- Project linters and type checks if cheap (`make lint && make test --quiet`)

Capture the passing run as `[E2]`. Add TodoWrite items
`proof:iron-law-green` and `proof:evidence-captured`.

If any unrelated test breaks: stop, do not paper over. Add a TodoWrite
`proof:regression-detected` and report to the user.

## Step 8: Report

**Purpose**: Summarize the fix with evidence trail.

Output the following structure:

```text
fixit summary
=============
Failure type:    <triage>
Scope:           <auto-detected or override>
Hypothesis:      <chosen cause>
Files changed:   <list>
RED test:        <test path::name>          [E1.test]
GREEN run:       <command>                  [E2]
Lint/type:       <command>                  [E2.lint]
Status:          PASS | FAIL | BLOCKED
Confidence:      high | medium | low
```

If `--commit` is set and Status is PASS:

- Invoke `/sanctum:acp` to stage, commit (via
  `Skill(sanctum:commit-messages)`), and push
- Use a `fix:` conventional-commit type by default
- Reference the failing input or error code in the commit body

Default behavior is no-commit; the user reviews the diff and commits manually.

### Record Lessons Learned (decision journal)

If this work involved rework, a failed approach, or a blocker, record it to
`docs/lessons-learned.md` so the insight survives past the session (draft and
confirm):

- If leyline is installed, invoke `Skill(leyline:decision-journal)` and append
  a lesson entry (`what_happened`, `what_didnt_work`, `root_cause`, `action`;
  set `phase` to `execute`). Show the draft; append on confirmation.
- Fallback (leyline absent): append to `docs/lessons-learned.md` using the
  in-file ENTRY TEMPLATE; assign the next `LL-NNN` id.

## Configuration and Options

| Flag | Default | Effect |
|------|---------|--------|
| `--file <path>` | unset | Read input from a file instead of `$ARGUMENTS` |
| `--scope auto\|minor\|medium\|major` | `auto` | Override scope detection |
| `--from <step>` | `triage` | Start at a later step |
| `--to <step>` | `report` | Stop after a given step |
| `--research` / `--no-research` | auto | Force or skip step 3 |
| `--strict` | off | Enforce Iron Law even when otherwise softened |
| `--quick` | off | Skip Research; do not skip RED test |
| `--commit` | off | Auto-commit via `/sanctum:acp` on PASS |
| `--dry-run` | off | Plan and report only; no edits, no commands |

`--strict` and `--quick` can coexist: `--quick` skips research, `--strict`
keeps Iron Law and all verification steps.

## Examples

### Example 1: pasted Python traceback

```bash
/fixit "Traceback (most recent call last):
  File 'parser.py', line 88, in parse_header
    return tokens[0].upper()
TypeError: 'NoneType' object has no attribute 'upper'"
```

Expected flow: triage classifies as `runtime` / `python`, scope=`medium`. RED
test asserts `parse_header(<minimal-empty-input>)` raises a typed error rather
than a `TypeError`. Fix returns early or raises a domain error.

### Example 2: paste a build log file

```bash
/fixit --file /tmp/cargo-build.log --scope major
```

Expected flow: triage parses cargo error codes (E0382 etc.), scope is forced
major, research runs against rust-lang docs and prior issues, hypothesis
ladder picks borrow-checker vs lifetime, RED test is a `cargo test` case that
fails to compile in the same way.

### Example 3: behavior mismatch with no error

```bash
/fixit "calling render() returns '<empty>' but it should return the
formatted resume HTML when called with a valid YAML path"
```

Expected flow: triage classifies as `behavior`, scope=`medium`. Reproduce by
running the described call; capture the empty output as `[E1]`. RED test
asserts `render(valid_yaml).startswith('<!DOCTYPE')`.

### Example 4: do not commit; just plan

```bash
/fixit "..." --to test --dry-run
```

Expected flow: triage and reproduction plan are produced with no edits. Useful
for validating that the input is enough to act on before allocating the time
for a full fix.

## Related Commands

- `/sanctum:fix-pr` - PR or MR review feedback
- `/sanctum:do-issue` - GitHub or GitLab issue implementation
- `/sanctum:fix-workflow` - retrospective workflow improvement (not code defect)
- `/sanctum:acp` - stage, commit, push (used by `--commit`)
- `/pensive:bug-review` - systematic bug hunting in surrounding code

## Related Skills

- `Skill(imbue:proof-of-work)` - evidence capture and Iron Law enforcement
- `Skill(imbue:rigorous-reasoning)` - anti-sycophancy in diagnosis
- `Skill(imbue:karpathy-principles)` - surgical edits and pre-impl gate
- `Skill(superpowers:systematic-debugging)` - hypothesis ladder methodology
- `Skill(superpowers:test-driven-development)` - RED test framing
- `Skill(superpowers:verification-before-completion)` - evidence before claims
- `Skill(tome:code-search)` and `Skill(tome:research)` - prior-art lookup

## Exit Criteria

- [ ] Input was parsed into a triage record with at least
      `failure_type`, `scope`, and one artifact (file, code, or symbol)
- [ ] A reproduction command was captured and recorded as `[E1]`
- [ ] A RED test exists and was observed to fail before the fix
- [ ] The fix made the RED test pass and did not break any previously-passing
      test in the same file or module
- [ ] Status is reported as PASS, FAIL, or BLOCKED with evidence references
- [ ] If `--commit` is set, a commit was created via `/sanctum:acp` only when
      Status is PASS
- [ ] If triage cannot classify the input, the workflow halted and asked the
      user a clarifying question instead of guessing
