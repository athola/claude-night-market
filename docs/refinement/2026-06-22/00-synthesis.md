---
date: 2026-06-22
scope: entire codebase
tier: 3 (deep)
mode: plan-only (no code edits)
verified: 176/176
tool: pensive:code-refinement
---

# Code Refinement Synthesis — 2026-06-22

Tier 3 deep scan of 23 plugins, ~323K Python lines, ~190 SKILL.md files.
All 176 findings verified by `citation_verifier.py` (exit 0).

## Summary

| Dimension | HIGH | MEDIUM | LOW/INFO |
|-----------|------|--------|----------|
| clean-code | 12 | 21 | 15 |
| duplication | 7 | 19 | 15 |
| error-handling | 5 | 15 | 4 |
| algorithmic-efficiency | 4 | 6 | 2 |
| architectural-fit | 4 | 9 | 5 |
| anti-slop | 4 | 6 | 2 |
| skill-exit-criteria | 10 | 0 | 0 |
| coupling | 4 | 2 | 0 |
| **Total** | **40** | **84** | **52** |

Top plugins by finding count: pensive (28), abstract (23),
conserve (22), sanctum (20), memory-palace (18), imbue (17).

## Wave 1 Candidates (HIGH severity, 40 findings)

Ranked by estimated effort and risk.

### 1a. Stub/dead code to delete immediately (zero risk)

These are confirmed stubs with no production callers.

| ID | Location | Issue |
|----|----------|-------|
| PEN-003 | `pensive/src/pensive/skills/code_review.py:26` | `CodeReviewWorkflow.run()` always returns empty findings dict; never calls any real analysis |
| PEN-004 | `pensive/src/pensive/skills/unified_review.py:14` | `dispatch_agent()` returns `f"{skill_name} execution result"` — fabricated string passed as real output |
| ABS-006 | `abstract/src/abstract/wrapper_base.py:257` | `SuperpowerWrapper` (270 lines) is tagged deprecated, zero production consumers; delete |
| IMB-013 | `imbue/skills/proof-of-work/SKILL.md:226` | Skeleton status declaration with no content; delete or fill |

### 1b. Missing Exit Criteria in SKILL.md files (10 findings)

All 10 conserve skills and 2 sanctum skills lack the
`## Exit Criteria` section required by
`.claude/rules/skill-exit-criteria.md` (issue #454).

Conserve (10): `bloat-detector`, `token-conservation`,
`decisive-action`, `response-compression`, `mcp-code-execution`,
`agent-expenditure`, `cpu-gpu-performance`,
`code-quality-principles`, `context-map`, `smart-sourcing`.

Sanctum (2): `commit-messages`, `do-issue` (highest-complexity
skill in the repo, model_hint: deep — highest priority).

Fix: add an `## Exit Criteria` block with 3+ concrete, falsifiable
checklist items to each file.

### 1c. Cross-plugin import coupling (4 findings)

Three plugins (sanctum, gauntlet, tome) carry inline fallback
duplicates of leyline utilities. Memory-palace duplicates tome's
fallback verbatim.

| ID | Importer | What is duplicated |
|----|----------|--------------------|
| XPL-001 | `sanctum/_frontmatter.py:17` | `leyline.frontmatter` parser (inline fallback) |
| XPL-002 | `gauntlet/graph.py:18` | `leyline.sqlite_graph_base.SqliteGraphBase` (inline fallback) |
| XPL-003 | `tome/session.py:12` | `leyline.session_store.SessionStore` + `validate_session_id` |
| XPL-004 | `memory-palace/session_history.py:20` | Near-identical duplicate of tome's XPL-003 fallback |

Fix: declare leyline as a hard dependency in each plugin's
`pyproject.toml` and remove the fallback duplicates. leyline is
already installed wherever these plugins run.

### 1d. N+1 and god-object code issues

| ID | Location | Issue |
|----|----------|-------|
| MP-003 | `memory-palace/palace_renderer.py:83` | One `get_entity()` DB query per resident in a loop; batch with `IN` clause |
| MP-002 | `memory-palace/palace_renderer.py:350` | Fetches entire `triples` table then filters in Python |
| MP-005 | `memory-palace/autonomy_state.py:350` | Bare `except Exception: return` swallows all `record_decision` failures |
| MP-006 | `memory-palace/memory_palace_cli.py:72` | 1,245-line god class; 20+ unrelated methods across plugin lifecycle, garden, and routing |
| CON-003 | `conserve/ecosystems.py:164` | 6 independent filesystem traversals where 1 pass suffices |
| ABS-009 | `abstract/token_tracker.py:109` | Four analysis methods each call `analyze_skill()` independently; 4× wasted re-reads per skill |
| ABS-015 | `abstract/improvements.py:217` | Same skill analyzed three times in one `generate_improvement_plan` call |
| ABS-022 | `abstract/tasks_manager_base.py:72` | `in_progress_tasks` uses O(n) list membership check inside a loop |
| EGR-001 | `egregore/notify.py:40` | Herald path hardcoded as `parents[2]/herald/scripts/notify.py` |
| SAN-008 | `sanctum/quality_checker.py:216` | `_check_assertion_quality` AST nesting depth 15; unreachable branches |
| SAN-009 | `sanctum/quality_checker.py:321` | `run_dynamic_validation` 78 lines, depth 11 |
| SAN-010 | `sanctum/quality_checker.py:572` | `main()` depth 10; three independent command branches in one function |
| SAN-003 | `sanctum/quality_checker.py:170` | List comprehension result silently discarded (dead computation) |
| CJR-001 | `conjure/experts.py:42` | 5 hardcoded model IDs with no startup validation |
| SML-001 | `parseltongue/__init__.py:49` | `AsyncAnalysisSkill` is a 13-method stateless delegation class; replace with module-level functions |
| SML-002 | `parseltongue/_base.py:10` | `parse_code` copied verbatim into `testing_guide/_constants.py:11` |
| PEN-014 | `pensive/unified_review.py:350` | `execute_skills()` defined twice with incompatible return types |
| ABS-001 | `abstract/tasks_manager_base.py:454` | Fallback-load pattern duplicated across 4 methods |
| ABS-002 | `abstract/tasks_manager_base.py:482` | Second duplicate instance of ABS-001 pattern |
| MP-001 | `memory-palace/.gitignore:3` | `.uv-cache/` and `.venv/` on disk but absent from `.gitignore` |

---

## Wave 2 Candidates (MEDIUM severity, 84 findings)

Selected high-value items. Full list in `.review/findings.json`.

### Error handling (15 findings)

Consistent pattern: `except Exception` catching far more than
intended, followed by either `return None` or silent
`logger.debug`. Most are in abstract (4), imbue (3), conjure (2).

Key items:

- `ABS-003`, `ABS-004`: `token_tracker.py` silently returns
  error states on file-read failure
- `ABS-005`: `_unparse_annotation` returns `None` on all
  exceptions including `MemoryError`
- `CJR-002`, `CJR-003`: `delegation_executor.py` swallows auth
  probe errors and config load errors to `logger.debug`
- `MP-011`: `embedding_index.py:131` swallows `MemoryError` on
  model load
- `CON-008`, `CON-009`: `growth_analyzer.py` and
  `growth_controller.py` call `sys.exit(1)` with no message on
  `FileNotFoundError`/`JSONDecodeError`

### Duplication (19 findings)

- `SAN-001`: `update_pyproject_version` and
  `update_cargo_version` are byte-for-byte identical in
  `update_versions.py`; same for two other version-update
  functions (4 → 2)
- `ABS-011`, `ABS-018`: `audit_skills` and `audit_all_skills`
  perform the same SKILL.md traversal with different return shapes
- `CJR-008`: `conjure/quota_tracker.py` reimplements token
  estimation that leyline already provides
- `CON-001`: `ecosystems.py` defines its own `_walk` that
  duplicates `_walk_limited` from `models.py`

### Algorithmic efficiency (6 findings)

- `GAT-001`: `graph.py impact_radius` resolves BFS nodes one-by-one;
  needs batch `IN`-clause SELECT
- `GAT-002`, `GAT-003`: weight-selection loops in `challenges.py`
  and `progress.py` scan full history per candidate; build a dict
  index once
- `CJR-004`: O(n³) Borda count in `conjure/phases.py:289`
- `MP-013`: `install_skills` uses `rglob("skills")` for
  non-deterministic discovery
- `ATT-001`: Three `_create_*_structure` functions (186 lines)
  are near-identical; consolidate to data-driven dispatch

### SKILL.md Exit Criteria gaps (MEDIUM, non-conserve)

Leyline (9 skills), abstract (14 skills), sanctum (11 additional
skills beyond Wave 1), imbue (most skills) — all missing Exit
Criteria sections. Total SKILL.md gap across the codebase:
approximately 60 skills.

---

## Wave 3 Candidates (LOW/INFO, 52 findings)

### Configuration and naming

- `ATT-004`: `--python-version` defaults to `3.10` but project
  system Python is 3.9.6 (`attune_init.py:608`)
- `EGR-002`: `run_scout()` has `category_id` and `repo_owner`
  baked into function signature defaults
- `CON-004`: Magic values `1_000_000` / `600` / `150` buried
  inside `context_warning.py:294`; promote to module constants
- `CJR-001` (already Wave 1): `conjure/experts.py` model IDs

### Architecture documentation

- `SML-008`: Herald registers zero skills; document that it is an
  intentional hook-and-script library, not a skill plugin
- `SML-009`: Archetypes is a valid markdown-skill-only plugin
  (14 skills, 0 Python src); add README note
- `SML-010`: Cartograph same pattern (7 skills, 1 hook, 0 src)

### Skill overlap candidates

- `LEY-004`: `quota-management` and `usage-logging` both claim
  cost-tracking without a documented boundary
- `CON-020`: `bloat-detector` skill vs `bloat-scan` skill
  descriptions are near-identical
- `PEN-001`, `PEN-002`: `rust_review_data.py` mixes schema,
  patterns, compiled regexes, and templates in 832 lines;
  section on compiled REs (lines 616-738) mechanically mirrors
  the pattern strings

---

## Cross-Plugin Coupling Report

### Confirmed leyline fallback pattern (4 plugin sites)

```
sanctum  → leyline.frontmatter       (XPL-001)
gauntlet → leyline.sqlite_graph_base (XPL-002)
tome     → leyline.session_store     (XPL-003)
memory-palace → leyline.session_store (XPL-004, identical to XPL-003)
```

All four import leyline with `try/except ImportError` and then
duplicate the leyline implementation as a fallback. leyline is
already a required plugin in these environments. The fallbacks
will drift from the canonical source.

Fix in one PR: add `leyline` to each importer's
`pyproject.toml` `[project.dependencies]`, remove the fallback
duplicates, add an integration test that imports from leyline
in each plugin's test suite.

### `_jaccard_similarity` duplication

Nearly identical functions in:
- `tome/synthesis/merger.py:39`
- `memory-palace/corpus/semantic_deduplicator.py:23`

Extract to `leyline/src/leyline/text_similarity.py`.

### Corrected claim from exploration

Prior analysis claimed `ReportingMixin` appeared in 6 plugin
`src/` directories. The cross-plugin agent confirmed all 7
occurrences are within `plugins/pensive/src/` in different skill
subdirectories. This is an intra-plugin naming convention, not
cross-plugin duplication. Same for `QualityMixin`. No extraction
to leyline warranted.

---

## Notable Structural Issues

1. `plugins/memory-palace/.gitignore` does not exclude `.uv-cache/`
   or `.venv/`. Both directories exist on disk and contain
   thousands of vendored package files that inflate `git status`
   and `find` output. Add both to the gitignore (finding MP-001).

2. `pensive/src/pensive/skills/code_review.py` contains two
   confirmed stubs (`CodeReviewWorkflow.run()` always returns
   empty; `dispatch_agent()` always returns a format string).
   These stubs are wired into `execute_skills()` which is called
   by real consumers. The callers receive useless data silently.
   This is the single highest-risk finding in the report (PEN-003,
   PEN-004, PEN-014).

3. `attune_init.py` defaults `--python-version` to `3.10`
   (ATT-004). Any project scaffolded with the default generates
   a `pyproject.toml` claiming Python 3.10 as minimum, which
   will fail on the documented 3.9.6 system Python.

---

## Verification

```
python3 plugins/imbue/scripts/citation_verifier.py \
  --findings .review/findings.json --repo-root .
```

Output: `Citation verification: PASS — Verified: 176  Failed: 0`

All findings have been verified against the current working tree.
The full machine-readable dataset is at `.review/findings.json`.

---

## Execution Log

### Phase 1 — Mechanical fixes (commit `refactor(codebase): Phase 1 mechanical fixes`)

Closed: MP-001, ATT-004, CON-004, EGR-002, SAN-003, IMB-013, SML-008,
SML-009, SML-010.

### Phase 2 — Exit Criteria additions (complete)

Closed all 105 SKILL.md files missing `## Exit Criteria` in three
parallel agent batches:

- Batch A (abstract/archetypes/attune/conjure, 35 files): `63c6c162`
- Batch B (conserve/gauntlet/hookify/imbue/leyline/oracle/phantom, 35 files): `c7c8f6f4`
- Batch C (cartograph/egregore/memory-palace/sanctum/scribe/spec-kit/tome, 35 files): `78871f49`

### Phase 2b — SML-002 import deduplication (complete)

`parse_code` duplicate in `testing_guide/_constants.py` eliminated.
`_recommendations.py` now imports from `async_analysis._base` (canonical source).
TDD: test `test_parse_code_sourced_from_async_analysis_base` written first, passed (1 test).
Commit: `bdd3a996`.

### Explicit Deferrals

The following findings are deferred per the skill's completion gate
("architecture-level decisions, new dependency declarations") with
one-sentence rationale each:

| ID | Rationale |
|----|-----------|
| PEN-003 | `CodeReviewWorkflow.run()` always returns empty dict; fixing it requires deciding the intended real behavior — Claude API dispatch, subprocess, or skill invocation. Design decision outside code-refinement scope. |
| PEN-004 | `dispatch_agent()` returns a format string to real callers; same design-decision blocker as PEN-003. |
| PEN-014 | `execute_skills()` type mismatch is a downstream effect of the PEN-003/PEN-004 stubs; resolves when those are wired. |
| PEN-001 | `rust_review_data.py` (832 lines) split requires agreeing on module boundaries and public API surface. Module reorganization design decision. |
| PEN-002 | Same file as PEN-001; same rationale. |
| XPL-001 | `sanctum/_frontmatter.py` leyline fallback: removal requires declaring leyline as hard dependency in pyproject.toml and adding integration tests. New dependency declaration — named deferral category in skill. |
| XPL-002 | `gauntlet/graph.py` leyline fallback: same rationale as XPL-001. |
| XPL-003 | `tome/session.py` leyline fallback: same rationale as XPL-001. |
| XPL-004 | `memory-palace/session_history.py` leyline fallback: same rationale as XPL-001. |
| ABS-006 | `SuperpowerWrapper` (270 lines) is deprecated in production but has 20+ active test references. Deletion would break the test suite. Deferred: requires test migration to the replacement API first. |
| SML-002 | CLOSED — `bdd3a996`. Import redirect verified, no circular import (async_analysis._base imports only ast stdlib). |
