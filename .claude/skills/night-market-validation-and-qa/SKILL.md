---
name: night-market-validation-and-qa
description: 'Enforce evidence bar, coverage gates, and regression guards. Use when adding tests or claiming done. Do not use to run suites; use night-market-operations.'
---

# Validation and QA: what counts as evidence here

This skill defines the evidence bar for claiming work complete, the
coverage and quality thresholds that gate merges, the golden regression
tests that guard settled battles, and the procedure for adding tests.
The one-line thesis: a green check proves spec-satisfaction, not
correctness, so every completion claim needs cited evidence and every
test needs proof it can fail.

## The evidence bar

Never claim "should work". Run the thing, capture the output, cite it.
The house discipline comes from `Skill(imbue:proof-of-work)`:

1. Number every piece of evidence: `[E1]`, `[E2]`, each with the exact
   command and its captured output.
2. Map each acceptance criterion to evidence with a verdict:
   `Criterion: [E2] -> PASS` or `-> FAIL`.
3. Give the overall claim one of three statuses: `COMPLETE` (all
   criteria passed), `PARTIAL` (list blockers), `BLOCKED` (explain
   why). A blocked task reported as blocked with evidence is a
   successful report. A guessed "done" is not.
4. The final response must not contain "should work", "looks right",
   or any other unverified confidence phrase.

### Verifier integrity: never let the generator judge itself

A passing verifier can mislead two ways (from the prover-verifier
research, codified in commit `29081fda`, module
`plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md`):

| Failure mode | What it looks like |
|--------------|--------------------|
| Wrong spec | The check confirms the code matches the spec, not that the spec matches intent |
| Hollow check | `assert True`, a mock returning the expected value, a stubbed service: all green, all worthless |

Rules that follow:

- The agent that wrote the code must not be the sole judge of whether
  the code works. Use an independent check: a fresh subagent, the real
  test suite, a human, or an end-to-end run the generator cannot
  influence.
- Validate the spec separately from the code. A machine-checked pass
  against a wrong spec is confident, green, and wrong.
- When reviewing a test, ask what change to the code would make it
  fail. If nothing would, it is not a test.

## Iron Law TDD (Constitution rule 3)

CONSTITUTION.md rule 3: no implementation without a failing test
first. Scope:

- Applies to every code change in plugin Python sources
  (`plugins/*/src/`, `plugins/*/scripts/`, `plugins/*/hooks/`).
- Skill files, agent files, and prose docs are exempt. Their analogue
  is a structural validation test: every new skill needs a
  `test_skill_<name>.py` proving the structure.

A structural validation test asserts observable content in the skill
file: required sections exist, the referenced modules exist on disk,
tables and examples the skill promises are present. Model on
`plugins/imbue/tests/unit/skills/test_proof_of_work.py`, which checks
SKILL.md sections, module files, and enforcement tables. The test must
fail if someone deletes the section it guards (see the
tautological-test trap below).

## Thresholds

| Gate | Value | Where defined | Enforced by |
|------|-------|---------------|-------------|
| Root coverage | `fail_under = 85` | root `pyproject.toml` `[tool.coverage.report]` | root pytest runs |
| Per-plugin coverage | `coverage_threshold` in `[tool.nightmarket]`, 90 for most plugins, 85 for gauntlet | `plugins/<p>/pyproject.toml` | `scripts/run-plugin-tests.sh` passes `--cov-fail-under` only when the key is set and > 0 |
| Mutation testing | weekly Sunday 00:00 UTC cron mutates only sanctum (the matrix falls back to sanctum when the dispatch input is empty); abstract/imbue/attune run only via manual dispatch with `plugin=all` or a named plugin | `.github/workflows/mutation-testing.yml` | mutmut: exit 0 = no survivors, exit 2 = survivors (allowed), anything else = crash |
| Critical issues | `max_critical_issues: 3`, `enforce_blocking: true` | `.claude/quality_gates.json` | quality-gate tooling |
| File size | < 20KB and < 5000 tokens per file | `.claude/quality_gates.json` | advisory (`block_on_violation: false`) |
| Function length | <= 60 lines, complexity < 12, nesting <= 5, debt ratio < 0.3 | `.claude/quality_gates.json` | advisory, except security dimension which blocks |

Notes:

- The `run-plugin-tests.sh` awk parser reads `coverage_threshold` from
  `[tool.nightmarket]`, never from `addopts`. Use
  `scripts/fix_coverage_threshold.py` to migrate a plugin still using
  the old location.
- The script itself sets no minimum floor for `coverage_threshold`. If
  the key is absent, no `--cov-fail-under` flag is passed at all, so a
  plugin without the key has no coverage gate in the runner.
- imbue's own `addopts` force `--cov=scripts` plus term and HTML
  coverage reports on every run, including single-file runs.

## The tautological-test trap

PR review here repeatedly catches tests that assert nothing. Evidence
in history: `a94240e2` (12 tests of constants tightened to behavioral
coverage), `f1cbbcf1` (strengthened tautological assertions),
`30e58586` (validation-floor regression test), `42f7ce84` (round-trip
test replacing a structure-only check). The pattern: a test that
restates the code, mocks the unit under test, or asserts a constant
equals itself.

The counter-discipline is the revert test, executed by
`sanctum:validate-pr`:

1. Take the fix the PR claims to make.
2. Edit the fixed line back to its broken state (working tree must be
   clean first, or the step is skipped as unsafe).
3. Run the test that supposedly guards the fix.
4. The test must FAIL against the reverted code. If it stays green,
   the test is a dead assertion, not a guard.
5. Restore the fix.

When writing a new test, apply the same standard preemptively: write
the test so it would catch the bug's return, then confirm it fails
before the fix lands (that is the Iron Law's RED step).

## Golden inventory: regression guards worth knowing

These tests lock in lessons from settled incidents. Do not weaken or
delete them without understanding the incident they guard.

| Guard | Location | What it locks |
|-------|----------|---------------|
| py39 datetime alias | `plugins/leyline/tests/test_python39_compat.py` | AST-scans leyline source for `datetime.UTC` (a 3.11+ alias). Hooks run under system Python 3.9, and this alias broke the whole hook import chain three-plus times. Ruff UP017 kept auto-reverting manual fixes, so only this AST invariant test holds the line. |
| Lazy-import blocker | `plugins/gauntlet/tests/unit/test_challenges.py` | Installs a `sys.meta_path` blocker that raises on any re-import of `anthropic`, proving gauntlet's heavy deps stay lazily imported. Eager imports made every git commit emit hook ModuleNotFoundError. |
| Hook timeout budget | `plugins/herald/tests/unit/test_double_shot_latte.py` (`test_llm_timeout_fits_within_hook_timeout`) | Asserts `LLM_TIMEOUT_SECONDS` is strictly less than the Stop-hook timeout registered in hooks.json. A timeout above the budget once cost the hook its verdict entirely (full record: night-market-failure-archaeology SB7). |
| Hook stdin contract | `plugins/abstract/tests/hooks/test_hook_io.py` | Locks the input contract of `shared/hook_io.py`: stdin JSON is primary, legacy `CLAUDE_TOOL_*` env vars are fallback only. Env-reading hooks were once silent no-ops for months (full record: night-market-failure-archaeology SB9). |

When you fix an incident of a similar class, add its guard here in the
same spirit: an invariant test that fails loudly if the lesson is
unlearned.

## How to add tests

### Layout and isolation

- Each plugin owns `plugins/<plugin>/tests/` with `unit/`,
  `integration/` subdirectories and its own `conftest.py` and pytest
  config in the plugin's `pyproject.toml`.
- Root `pyproject.toml` sets `norecursedirs = ["plugins/*", ...]`.
  Plugin tests MUST run per-plugin. Running them from the repo root
  causes ImportPathMismatchError from duplicate module names (the root
  `conftest.py` documents this).

### Commands

```bash
# Single test file (fastest loop)
cd plugins/imbue
uv run pytest tests/unit/test_deferred_capture.py -x -q

# Full suite for one plugin
cd plugins/<plugin>
uv run python -m pytest tests/ --tb=short -q
# or, where the plugin has a Makefile target:
make -C plugins/<plugin> test

# Everything (what `make test` at root does)
./scripts/run-plugin-tests.sh --all

# Only plugins with staged changes
./scripts/run-plugin-tests.sh --changed

# Mutation testing for one plugin, locally
cd plugins/<plugin>
uv run mutmut run --paths-to-mutate=scripts/,src/ --tests-dir=tests/
```

### Markers

Root pytest runs with `--strict-markers`, so only registered markers
are legal. Registered in root `pyproject.toml`: `unit`, `integration`,
`e2e`, `slow`, `network`, `plugin`, `skill`, `hook`, `command`, `bdd`,
`benchmark` (skip benchmarks in CI with `-m "not benchmark"`).

### Checklist for new code

- [ ] Failing test written and observed RED before implementation
  (Iron Law).
- [ ] Test would fail if the fix were reverted (revert-test standard).
- [ ] Correct marker applied and test placed in `unit/` or
  `integration/` accordingly.
- [ ] Plugin suite passes locally with its coverage flag:
  `uv run python -m pytest tests/ --cov-fail-under=<threshold>`.
- [ ] New skill files have a `test_skill_<name>.py` structural test.

## Failure-mode detection: silent failure in scanners

The most recurrent bug class in this repo is the swallowed error. In
scanner-shaped code (anything that walks files and reports findings),
the signature is except-continue: a `try/except` that skips a file on
malformed input and reports success on the remainder. The scanner
looks healthy while ignoring exactly the inputs most likely to be
broken.

The house convention since commit `666171c3` (issue #575): a scanner
that cannot process an input emits an ADVISORY finding for it instead
of skipping silently. Examples from that commit:

- `check_hook_modernization.py` emits findings on malformed
  hooks.json, SyntaxError, or OSError instead of dropping the file.
- pensive `harden/scanner.py` appends an ADVISORY finding for
  unreadable files under `--strict`.
- minister `dora_metrics` warns and sets a partial flag on malformed
  tag lines instead of silently classifying the repo Elite.

When reviewing or writing scanner code, grep for the pattern:

```bash
rg -n "except .*:\s*$" -A2 plugins/<p>/scripts/ | rg -B1 "continue|pass"
```

Any hit that discards an error without emitting a finding or an inline
"why it is safe to discard" comment violates Constitution rule 10
(errors are not optional).

## When NOT to use

- Running the suites, lint, release, or publish mechanics: use
  `night-market-operations` (command anatomy lives there).
- Classifying and gating a change, PR review flow, non-negotiables:
  use `night-market-change-control`.
- A test is failing and you need triage for a known repo failure mode:
  use `night-market-debugging-playbook`.
- History of why a guard exists (incident narratives, reverts): use
  `night-market-failure-archaeology`.
- Setting up pytest config or fixtures for a new plugin:
  `Skill(leyline:pytest-config)` has the templates, and
  `Skill(leyline:testing-quality-standards)` the anti-pattern catalog.

## Exit Criteria

- [ ] Any completion claim made under this skill cites numbered
  evidence (`[E1]`...) with commands and captured output, and carries
  a COMPLETE, PARTIAL, or BLOCKED status.
- [ ] Every new test added in the session fails when its guarded fix
  is reverted (demonstrated, not assumed).
- [ ] New plugin Python code landed with a test observed failing
  first, and the plugin suite passes at or above its
  `[tool.nightmarket]` coverage_threshold.
- [ ] Any new skill file has a passing `test_skill_<name>.py`
  structural test.
- [ ] No scanner code added or reviewed in the session contains an
  except-continue that drops input without an ADVISORY finding or a
  stated reason.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15, branch
discussions-fix-1.9.14. Volatile facts and how to re-verify them:

- Root coverage floor: `rg -n "fail_under" pyproject.toml`
  (85 as of 2026-07-02).
- Per-plugin thresholds:
  `rg -n "coverage_threshold" plugins/*/pyproject.toml`
  (90 everywhere except gauntlet at 85, as of 2026-07-02).
- Threshold parser behavior: read the awk block in
  `scripts/run-plugin-tests.sh` (search `tool.nightmarket`).
- Mutation cadence and plugin list:
  `rg -n "cron|matrix" .github/workflows/mutation-testing.yml`.
- Quality gate numbers: `cat .claude/quality_gates.json`.
- Golden guards still present:
  `ls plugins/leyline/tests/test_python39_compat.py
  plugins/gauntlet/tests/unit/test_challenges.py
  plugins/herald/tests/unit/test_double_shot_latte.py
  plugins/abstract/tests/hooks/test_hook_io.py`.
- Cited commits: `git log --oneline -1 <hash>` for `29081fda`,
  `a94240e2`, `f1cbbcf1`, `30e58586`, `42f7ce84`, `666171c3`,
  `268cff89`.
- Marker list: `rg -n -A12 "^markers" pyproject.toml`.
