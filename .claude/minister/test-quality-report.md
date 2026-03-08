# Test Quality Review: Unified Report

Date: 2026-03-08
Scope: 16 plugins, 5,814 tests

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Total tests | 5,814 |
| Passed | 5,814 |
| Failed | 0 |
| Skipped | 5 |
| Pass rate | 100% (of tests that actually run) |
| Silently ignored | 162 (parseltongue collect_ignore) |

**Coverage distribution (16 plugins):**

| Bracket | Count | Plugins |
|---------|-------|---------|
| 90%+ (real) | 4 | leyline (93%), abstract (92%), conjure (91%), minister (96%) |
| 85-89% | 3 | attune (89%), pensive (89%), egregore (83%*) |
| 75-84% | 2 | sanctum (81%), egregore (83%) |
| 60-74% | 2 | memory-palace (65%), hookify (63%) |
| Illusory / unmeasured | 5 | conserve (100%*), imbue (100%*), parseltongue (98%*), spec-kit (0% real), scribe (none), scry (none) |

\* Asterisk marks coverage numbers that are misleading due to
narrow measurement scope.

**Anti-pattern density (aggregate):**

| Anti-pattern | Total instances | Affected plugins |
|-------------|----------------|-----------------|
| Weak assertions | 2,837 of ~5,900 (48%) | 15/16 |
| Unverified mocks | 504 across 66 files | 13/16 |
| Long tests (>50 lines) | 168 | 11/16 |
| Zero parametrize usage | 5 plugins (0 total) | conjure, attune, hookify, egregore, scribe |
| Near-zero parametrize | 6 plugins (<1%) | abstract, sanctum, memory-palace, conserve, pensive, imbue |
| Private-attribute tests | 65 | 7/16 |
| Bare Mock() (no spec) | 23+ | 3/16 |
| Illusory coverage | 4 plugins | conserve, imbue, parseltongue, spec-kit |

**Key finding:** Every plugin passes every test it runs,
but the test suites mask substantial quality gaps.
Four plugins report inflated coverage by excluding most
source from measurement.
Nearly half of all assertions are weak (string containment
or `is not None`).
Mock verification is absent in 66 test files.

---

## 2. Per-Plugin Scorecards

Grading rubric:

- Coverage (2x weight): A=90%+ real, B=85-89%, C=75-84%,
  D=60-74%, F=<60% or unmeasured/illusory
- Mock quality: A=verified/not needed, B=mostly verified,
  C=some gaps, D=major gaps, F=no verification
- Assertion quality: A=<20% weak, B=20-35%, C=35-50%,
  D=50-70%, F=>70%
- Test design: parametrize usage, test length, edge coverage

| Rank | Plugin | Tests | Cov | Cov Grade | Mock Grade | Assert Grade | Design Grade | Overall |
|------|--------|-------|-----|-----------|------------|-------------|-------------|---------|
| 1 | leyline | 267 | 93% | A | A | A | B | **A** |
| 2 | minister | 169 | 96% | A | C | B | B | **A-** |
| 3 | abstract | 1,590 | 92% | A | D | D | C | **B** |
| 4 | egregore | 153 | 83% | C | C | B | C | **B-** |
| 5 | attune | 376 | 89% | B | C | B | C | **B-** |
| 6 | conjure | 303 | 91% | A | D | C | D | **B-** |
| 7 | sanctum | 741 | 81% | C | D | B | C | **C+** |
| 8 | pensive | 297 | 89% | B | F | F | D | **C** |
| 9 | memory-palace | 646 | 65% | D | F | D | D | **D+** |
| 10 | hookify | 120 | 63% | D | A | B | D | **C-** |
| 11 | conserve | 356 | illusory | F | F | D | D | **D** |
| 12 | imbue | 267 | illusory | F | F | D | F | **D-** |
| 13 | scry | 52 | none | F | B | B | B | **D** |
| 14 | scribe | 283 | none | F | A | B | D | **D** |
| 15 | parseltongue | 10 | illusory | F | D | C | F | **F** |
| 16 | spec-kit | 184 | 0% real | F | F | C | D | **F** |

---

## 3. Top 20 Remediation Actions

| # | Plugin | Action | Impact | Effort | Evidence |
|---|--------|--------|--------|--------|----------|
| 1 | parseltongue | Un-ignore 162 tests or delete them; implement the missing methods they test | High | L | `tests/conftest.py:23` - collect_ignore list of 11 files |
| 2 | spec-kit | Write tests that actually import from speckit; current 184 tests exercise zero source | High | L | `pyproject.toml` coverage config targets `src/speckit` but 0% measured |
| 3 | conserve | Expand coverage source from `hooks` to include `scripts/` (7 modules excluded) | High | S | `pyproject.toml:137` - `source = ["hooks"]` |
| 4 | imbue | Expand coverage source from `scripts` to include `hooks/`, `skills/` | High | S | `pyproject.toml:151` - `source = ["scripts"]` |
| 5 | memory-palace | Add tests for memory_palace_cli.py (500 uncovered statements, largest gap in codebase) | High | L | `src/memory_palace/memory_palace_cli.py` - 0% coverage |
| 6 | pensive | Reduce weak assertion ratio from 71% (605/855); replace `in` checks with exact equality | High | M | Across 13 test files |
| 7 | conserve | Add mock.assert_called verification to all 10 mock-using files (0/10 verified) | High | M | `test_context_warning.py` - 110 mock refs, 0 verify |
| 8 | memory-palace | Add mock verification to 10 files with 120 unverified mocks | High | M | `test_web_research_handler.py` - 55 mocks, 0 verify |
| 9 | abstract | Add mock verification to 18 files with 143 unverified mocks | High | M | `test_wrapper_generator.py` - 24 mocks, 0 verify |
| 10 | scribe | Add coverage measurement; configure `[tool.coverage]` in pyproject.toml | High | S | No `[tool.coverage]` section exists |
| 11 | hookify | Test pattern_matcher.py (143 lines, 0% coverage) and helpers.py (114 lines, 0%) | High | M | 257 uncovered statements in 2 modules |
| 12 | conjure | Fix lint errors blocking `make test`; decompose 315-line test | High | M | `test_war_room_full_flow.py:93` - 8-deep nested patches |
| 13 | abstract | Test modular_analyze.py (0%), modular_tokens.py (0%), makefile_dogfooder.py (12%) | Medium | M | 3 modules at near-zero coverage |
| 14 | sanctum | Test post_implementation_policy.py and security_pattern_check.py (104 stmts, 0%) | Medium | M | 2 hooks with zero coverage |
| 15 | imbue | Decompose 55+ tests over 50 lines (worst: 277 lines) | Medium | M | Across 9+ test files |
| 16 | pensive | Decompose 40 long tests; extract 218-line test from conftest.py | Medium | M | conftest.py contains test logic |
| 17 | conserve | Reduce weak assertion ratio from 48% (443/914) | Medium | M | Across test suite |
| 18 | abstract | Add parametrize to repeated patterns (1/1617 = 0.06% current usage) | Medium | M | Suite-wide opportunity |
| 19 | conjure | Add parametrize (0/303 tests use it); verify 79 unverified mocks in 5 files | Medium | M | `test_delegation_error_paths.py` - 28 unverified |
| 20 | parseltongue | Remove coverage omit of `parseltongue/skills/*` to get real numbers | Medium | S | `pyproject.toml:118` - omits entire skills directory |

---

## 4. Cross-Cutting Observations

### Illusory coverage is the single biggest quality risk

Four plugins report high coverage that does not reflect
reality.
Conserve measures only `hooks/`, Imbue only `scripts/`,
Parseltongue omits `parseltongue/skills/*` and ignores
162 of 172 tests, and Spec-kit's tests never import the
source package.
Together these plugins claim 100%, 100%, 98%, and 184
passing tests respectively, while testing little to none
of their actual source code.

### Mock-without-verify is systemic

504 unverified mocks across 66 files in 13 plugins.
The pattern is consistent: tests patch dependencies,
exercise the function, then assert only on the return
value.
They never call `mock.assert_called_with()` or
`mock.assert_called_once()`.
This means the tests pass even if the function stops
calling its dependencies entirely.

A project-wide lint rule (via ruff or a custom pytest
plugin) that flags `Mock()` or `patch()` usage without
a corresponding `assert_called` would catch this at CI
time.

### Weak assertions hide regressions

48% of all assertions across the codebase use string
containment (`assert "foo" in result`) or existence
checks (`assert result is not None`).
Pensive is worst at 71%.
These assertions pass when the output changes in
breaking ways, as long as the substring is still
present somewhere.

A custom pytest assertion helper that enforces exact
match with diff output would reduce this.

### Parametrize is almost unused

11 of 16 plugins use parametrize in fewer than 1%
of tests.
5 plugins have zero parametrize usage.
The codebase contains many test functions that repeat
the same logic with different inputs, perfect candidates
for parametrize.

### Long tests correlate with mock nesting

The worst long tests (315 lines in conjure,
277 lines in imbue, 218 lines in pensive, 206 lines
in memory-palace) all feature deeply nested
`unittest.mock.patch` context managers.
Extracting mocks into fixtures and splitting test
phases into helper functions would improve both
readability and maintainability.

### No shared conftest infrastructure

Each plugin maintains its own conftest.py with duplicated
fixture patterns.
Common fixtures (temp directories, mock subprocess
runners, sample TOML/JSON configs) are reimplemented
across plugins.
A shared test utilities package at the repo root would
reduce duplication.

### CI pipeline gaps

Scribe and scry have no coverage measurement at all.
Scry deselects 24 integration tests that need external
tools (ffmpeg/vhs) with no CI provision for running them.
Parseltongue's collect_ignore silently skips 94% of tests
with no CI warning.

### Python 3.9 compatibility

No 3.9-incompatible syntax was flagged in the Phase 1
review.
The `from __future__ import annotations` import is
correctly used where needed (confirmed in
parseltongue/tests/conftest.py:7).

---

## 5. Evidence Log

Key file references supporting the findings above.

**Illusory coverage configs:**

- `plugins/conserve/pyproject.toml:137` -
  `source = ["hooks"]` excludes scripts/
- `plugins/imbue/pyproject.toml:151` -
  `source = ["scripts"]` excludes hooks/skills
- `plugins/parseltongue/pyproject.toml:118` -
  omits `parseltongue/skills/*`
- `plugins/parseltongue/tests/conftest.py:23` -
  collect_ignore drops 11 of 12 test files

**Zero-coverage modules:**

- `plugins/memory-palace/src/memory_palace/memory_palace_cli.py` -
  500 statements, 0% (largest gap)
- `plugins/abstract/src/abstract/modular_analyze.py` - 0%
- `plugins/abstract/src/abstract/modular_tokens.py` - 0%
- `plugins/hookify/scripts/pattern_matcher.py` - 143 lines, 0%
- `plugins/hookify/scripts/helpers.py` - 114 lines, 0%
- `plugins/sanctum/hooks/post_implementation_policy.py` - 0%
- `plugins/sanctum/hooks/security_pattern_check.py` - 104 stmts, 0%
- `plugins/pensive/src/pensive/skills/rust_review_data.py` - 0%

**Worst unverified mock files:**

- `plugins/conserve/tests/test_context_warning.py` -
  110 mock references, 0 verify calls
- `plugins/memory-palace/tests/test_web_research_handler.py` -
  55 mocks, 0 verify
- `plugins/conjure/tests/test_delegation_error_paths.py` -
  28 unverified mocks
- `plugins/abstract/tests/test_wrapper_generator.py` -
  24 mocks, 0 verify
- `plugins/attune/tests/test_template_loader.py` -
  21 unverified mocks
- `plugins/imbue/tests/test_tdd_bdd_gate.py` -
  20 unverified mocks
- `plugins/sanctum/tests/test_config_change_audit.py` -
  17 mocks, 0 verify

**Worst long tests:**

- `plugins/conjure/tests/test_war_room_full_flow.py:93` -
  315 lines, 8-deep nested patches
- `plugins/parseltongue/tests/conftest.py` -
  284-line test function inside conftest
- `plugins/imbue/` - 277-line test (worst single file)
- `plugins/pensive/tests/conftest.py` -
  218-line test in conftest
- `plugins/memory-palace/` - 206-line test

**Weak assertion hotspots (% weak):**

- pensive: 71% (605/855)
- imbue: 55% (483/884)
- conserve: 48% (443/914)
- abstract: 42% (668 weak across 29+ files)
- conjure: 37% (261/715)
