# Tier 3 Code Refinement -- Synthesis

**Date**: 2026-05-02
**Branch**: ai-slop-1.9.4
**Scope**: Entire codebase (plugins/, scripts/)
**Tier**: 3 (Deep) -- all 7 dimensions + plugin-specific patterns
**Mode**: Scope-guard ignored per user instruction

## Baseline Metrics

| Metric | Count |
|--------|-------|
| Source Python files (non-test) | 1,009 |
| Source Python LOC (non-test) | 95,370 |
| Test Python LOC | 196,509 |
| Shell scripts (non-test) | 1,141 |
| Shell LOC | 5,759 |
| Total Python functions | 2,966 |
| Plugins | 25 |
| Skills | 187 |

## Dimension Reports

| # | Dimension | File | Findings |
|---|-----------|------|----------|
| 1 | Duplication & Redundancy | `01-duplication.md` | 13 |
| 2 | Algorithmic Efficiency | `02-algorithm-efficiency.md` | 12 |
| 3 | Clean Code + Anti-Slop + Errors | `03-clean-code.md` | 50 |
| 4 | Architectural Fit | `04-architecture.md` | 31 |
| 5 | Additive Bias | `05-additive-bias.md` | 27 |
| 6 | Plugin-Specific Patterns | `06-plugin-patterns.md` | 22 |
| **Total** | | | **155** |

## Closed in this multi-session run (24 findings, 24 commits)

### Wave 1 + Wave 2a (15 findings, prior session)

| Finding | Title | Commit |
|---|---|---|
| A-01 | Pre-compile rust_review regex patterns | d79f6f73 |
| A-02 | repository_analyzer single rglob | feec0f9d |
| A-03 | code_review single rglob | feec0f9d |
| A-04 | safe_replacer single SKILL.md walk | 80b64e62 |
| A-07 | Counter idiom in memory-palace | 396daf72 |
| A-11 | frozenset constants for membership | 396daf72 |
| A-12 | dict.fromkeys for ordered dedup | 396daf72 |
| B-03 | Truthful phantom safety stubs | 969d53a7 |
| B-15 | Truthful bug_review stub docstring | 969d53a7 |
| C-13 | conserve cli main decomposition | 0d67d339 |
| C-21 | Surface vow hook exceptions | 0d67d339 |
| D-05 | resolve_session_file shared module | 60b328ee |
| D-06 | imbue vow shared helpers | 60b328ee |
| D-11 | get_plugin_version shared helper | 91b11e88 |
| D-12 | abstract emit_warn helper | 60b328ee |

### Wave 2 + partial Wave 3 (this session, 9 commits)

| Finding | Title | Commit |
|---|---|---|
| D-04 | abstract.utils dir helpers shared across scripts + hooks | 396ba302 + d77d2a4e |
| D-01 | Vendor json_utils.sh per plugin (5 hooks deduped) | a8c9e4e9 |
| D-02 | Unify parse_frontmatter on leyline canonical (4 callers) | cf34ba8b |
| D-03 | Share extract_section across abstract scripts (3 callers) | 12a7ce99 |
| D-13 | Share CLI JSON envelope helpers via leyline (3 callers) | 6014f345 |
| C-20 | Narrow memory-palace CLI excepts to typed errors | dbaccef7 |
| C-46 | Decompose memory_palace_cli build_parser | 21769f7e |
| B-08 | Delete sleep-only "perf tests" in imbue | 5fb7d4f2 |
| B-10 | Fix audit_skill_modules + replace assert True | 5fb7d4f2 |
| AR-30 | leyline.git_platform Python wrapper for gh api | 6e6b4f98 |

**Net impact across this session**: ~700 LOC duplicated/dead
code removed; ~480 LOC canonical helpers added (with tests).
Behavior preserved across 5,855+ tests on every modified plugin
(abstract 2175, memory-palace 970+, sanctum 970, conserve 627+,
imbue 627+, leyline 130+, pensive 407+, phantom 86). Pre-commit
suite (ruff, ruff-format, bandit, mypy, plugin validators) clean
on every commit.

## Deferred to dedicated PRs (rationale documented)

The following Wave 3 items were evaluated but deferred from this
multi-session run because each requires a focused PR with its
own risk-management plan:

### Pensive review god modules (AR-01..AR-04)

Six review skills sit at 700-968 lines, each one class with
14-19 methods. The `rust_review/` package pattern (mixin-based,
~200 LOC per concern) is the agreed target shape.

| File | Lines | Methods |
|---|---|---|
| `architecture_review.py` | 968 | 17 |
| `makefile_review.py` | 921 | 19 |
| `test_review.py` | 902 | 19 |
| `api_review.py` | 760 | 14 |
| `performance_review.py` | 744 | -- |
| `bug_review.py` | 744 | -- |
| `math_review.py` | 703 | -- |

**Why deferred**: Each decomposition is a 6-8-mixin split with
behavior preservation across 25-50 tests per skill. Combining
all six into one branch raises blast radius; each deserves its
own PR with focused review. Recommendation: one per release
cycle, starting with `architecture_review.py` (highest impact).

### sys.path centralization (AR-08, AR-13, AR-15)

45 `sys.path.insert` sites across hooks/scripts. AR-13 specifically
flags spec-kit/attune/sanctum all importing
`abstract.tasks_manager_base` without a manifest declaration.

**Why deferred**: A single `leyline.bootstrap.add_plugin_src_to_path()`
helper helps secondary lookups but cannot bootstrap leyline
itself (chicken-and-egg). The full fix requires either
(a) declaring inter-plugin dependencies in `plugin.json` schema
+ resolver, or (b) making plugins installable Python packages
in their own venv. Both are larger architecture changes than
fit in this code-refinement scope.

### Skill module explosion (P-14, AR-17..AR-20)

`slop-detector` has 19 modules, several plausibly mergeable
(`vocabulary-patterns` + `structural-patterns` -> `pattern-detection`,
`progress-indicators` + `metrics` -> `reporting`).

**Why deferred**: Each merge requires reading 2 source modules,
hand-editing prose to remove duplication, updating SKILL.md
module index, and verifying load-on-demand still works. P-15
(rust-review, 16 modules) and P-16 (mission-orchestrator, 12
modules) were inspected and confirmed intentionally fine-grained
-- no action needed there.

### Other Wave 3 god modules (AR-05, AR-06, AR-07)

| File | Lines | Note |
|---|---|---|
| `memory_palace/project_palace.py` | 823 | Mix of room enums + entry model + manager |
| `sanctum/validators.py` | 777 | 5 validators in one file |
| `memory_palace_cli.py` | 1050 | C-46 partial fix landed (build_parser); main remains |

**Why deferred**: Same blast-radius argument as AR-01..AR-04.
sanctum/validators is the cheapest win (split-by-class is
mechanical) and a good first follow-up.

## Remaining findings (not classified above)

The dimension reports contain ~140 findings. Most are LOW or MEDIUM
impact items (single-class consolidations, minor naming,
docstring-only fixes). They remain available for opportunistic
cleanup as adjacent code is touched, per the synthesis convention
of "fix one when you change a file in the same area."

The dimension reports themselves
(`01-duplication.md` ... `06-plugin-patterns.md`) remain on
disk in this directory as the source of truth.

## Methodology notes

- **Iron Law throughout**: Every Python addition (D-04 helper,
  parse_frontmatter_with_body, extract_section, cli_envelope,
  git_platform) had a failing BDD test written first; RED was
  confirmed before GREEN.
- **Behavior preservation**: Each refactor was paired with the
  pre-existing test suite as a regression net. No tests deleted
  except B-08 (vacuous sleep-tests with no SUT involvement) and
  B-10's `assert True` placeholder (replaced with real
  contract).
- **Pre-commit gates**: ruff (check + format), bandit, mypy,
  plus each plugin's structure validator ran on every commit.
- **Scope-guard ignored**: Per user instruction. Branch metrics
  ended ~38k lines / 75 commits. The work clusters by
  finding-ID (D-01, D-02, ...), so post-hoc splitting to
  conventional 1k-LOC PRs is mechanical.
