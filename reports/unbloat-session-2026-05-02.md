# Unbloat Session Report - 2026-05-02

**Branch:** `ai-slop-1.9.4`
**Continuation of:** `reports/unbloat-session-2026-05-01.md` (commits
`e279b155`...`d1e42ddf`)
**Mode:** Tier 3, all phases, scope-guard ignored per explicit user
authorization, do not stop until complete.

## Scope

Continued from the prior session, which closed Phases 1-6 of the
original `cleanup-report.md`. This session addressed:

1. The 91 deferred docstring-restate hits flagged by R7 (the new
   pre-commit hook landed in `d1e42ddf`).
2. The deferred file-thrashing detector improvement noted by I3.
3. A residual deletion missed by I2 (`scripts/test-lsp-manually.sh`
   was wrongly recorded as already absent).
4. A fresh Tier 3 bloat scan across the entire monorepo
   (`reports/cleanup-bloat-2026-05-02.md`, 24 findings).
5. Execution of all actionable findings from the new report.

## Commits landed this session

| Commit | Subject | Net delta |
|--------|---------|-----------|
| `b8c45ab0` | clear 91 deferred docstring-restate hits | -88 |
| `552409b9` | document substantive-commits filter for churn | +22 |
| `cd65dde1` | delete residual scripts/test-lsp-manually.sh | -121 |
| `28afe07e` | delete 5 orphaned plugin scripts | -401 |
| `ba2fc650` | Phase 1 Tier 3: F01, F03, F04, F12, F13 | -500 |
| `7da2e441` | F11 hook-scope-guide skill dir + register | -4 |
| `fa5030bc` | Phase 4 archive stale tracked artifacts | -1822 |

**Net delta: -2,914 lines tracked code/docs removed.**

## Findings actioned (from `reports/cleanup-bloat-2026-05-02.md`)

### Phase 1: Zero-risk

| ID | Action | Result |
|----|--------|--------|
| F01 | rm `reports/skill-graph-audit-1.9.3.txt` | DELETED |
| F03 | Remove `stargazer-analysis` from Makefile .PHONY | DELETED |
| F04 | Add `.uv-tools/` to `.gitignore` | ADDED |
| F12 | rm `cleanup-report.md` (root, 250 lines) | DELETED |
| F13 | Untrack `reports/skill-graph.json` + gitignore | UNTRACKED |

### Phase 3: Structural

| ID | Action | Result |
|----|--------|--------|
| F11 | Convert `hook-scope-guide.md` to skill directory; register in plugin.json; update test fixture; update capabilities-reference.md; trim description to <160 chars | CONVERTED |

### Phase 4: Archive

| ID | Action | Result |
|----|--------|--------|
| F14 | Move `docs/architecture-analysis-report.md` (418 lines) to `docs/archive/reports/` | ARCHIVED |
| F17 | Move `reports/cleanup-bloat.md`, `cleanup-quality.md`, `cleanup-hygiene.md` (1,404 lines combined) to `docs/archive/reports/` | ARCHIVED |

### Independent findings (not in agent report)

| Finding | Action |
|---------|--------|
| Residual `scripts/test-lsp-manually.sh` (121 lines, 0 callers): prior I2 wrongly recorded as already absent | DELETED |
| `plugins/sanctum/scripts/validate_versions.sh` (140 lines, 0 callers, doc-only header) | DELETED |
| `plugins/memory-palace/scripts/tending_cli.py` (58 lines, 0 active callers) | DELETED |
| `plugins/memory-palace/scripts/metrics/regret_rate.py` + `context_savings.py` + `cache_hit_dashboard.py` (203 lines, all added in same dead batch) | DELETED + empty dir removed |
| 815 MB cache dirs (345 directories: `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `htmlcov`) + 48 MB `.uv-cache` | CLEANED (gitignored, regenerable) |

## Findings rejected after verification (false positives)

The Tier 3 bloat agent flagged seven items that proved to have active
callers the agent's narrow `Makefile/.github/.pre-commit-config.yaml`
grep missed. Each was verified before skipping.

| ID | What agent claimed | Reality |
|----|--------------------|---------|
| F02 | `reports/unbloat-session-2026-05-01.md` is dead | Untracked session record from prior cleanup; preserved as historical artifact (committed this session) |
| F05 | `scripts/check_hook_modernization.py` orphan | Active CLI invoked by sanctum `/update-plugins` command (`commands/update-plugins.md` and `phase1c-modernization.md`) |
| F06 | `scripts/fix_descriptions.py` orphan | Active pre-commit hook `validate-skill-descriptions` |
| F07 | `scripts/run-plugin-lint.sh` orphan | Documented developer tool in `docs/quality-gates.md` (parallel to `run-plugin-tests.sh`/`run-plugin-typecheck.sh`) |
| F10 | `scripts/check-all-quality.sh` orphan | Documented as recommended pre-PR workflow in `docs/quality-gates.md` |
| F15 | `scripts/check-markdown-links.py` orphan | Active pre-commit hook `check-markdown-links` |
| F16 | `scripts/reinstall-all-plugins.sh` orphan | Backs leyline `/reinstall-all-plugins` slash command + Makefile demo target |
| F18 | `plugins/abstract/docs/compatibility/` (3,501 lines) dead | Actively maintained: 4 separate updates in March 2026 tracking each Claude Code release (2.1.69 - 2.1.85) |
| F19 | `docs/dependency-audit.md` dead | Manually-maintained Supply Chain Incidents register; explicitly directed by leyline `supply-chain-advisory` skill (`Document in docs/dependency-audit.md`) |

The user's WIP edits to `scripts/clawhub-batch-publish.sh` (F08) and
`scripts/clawhub-cron.sh` (F09) signaled active development; both
preserved despite zero-caller status in the snapshot.

## Test gates

| Plugin | Suite | Result |
|--------|-------|--------|
| pensive | full | 407 passed |
| spec-kit | full | 203 passed |
| abstract | full | 2,168 passed |
| memory-palace | full | 970 passed |
| attune | full | 466 passed |
| sanctum | full | 970 passed |
| imbue | full | 627 passed |
| scribe | full | 580 passed |
| hookify | full | 289 passed |
| minister | full | 174 passed |
| tome | full | 362 passed |
| conjure | full | 351 passed |
| conserve | full | 627 passed |

**Total: 8,194 tests pass.**

## Pre-commit gates

All 60+ pre-commit hooks pass on the final commits:

- `validate-skill-descriptions`: clean
- `validate-description-budget`: under threshold (with hook-scope-guide
  trimmed to 130 chars)
- `capabilities-sync-check`: in sync
- `check-noqa`, `check-per-file-ignores`: clean
- `validate-*-plugin-structure`: all touched plugins pass
- `run-plugin-typecheck`: all touched plugins pass mypy/ty
- `run-plugin-tests`: all touched plugins pass with coverage
- `Mypy - Global Type Checking`: clean
- `Ruff - Format/Fix/Check`: clean
- `bandit`: clean

## Tooling improvements landed

* New module section in
  `plugins/conserve/skills/bloat-detector/modules/git-history-analysis.md`:
  documents the substantive-commits filter (>5 lines net) for churn
  detection, with a worked example (`rigorous-reasoning/SKILL.md` was
  flagged at 12 commits/30 days but only 1 was substantive. The rest
  were repo-wide release sweeps). Future detectors can use the
  `total_count / 3` threshold to classify cleanup-churn vs design churn.

## Token-savings achieved

| Source | Lines removed | Est. tokens saved |
|--------|---------------|-------------------|
| Phase 1 Tier 3 (F01, F12, F13 deletions; F03/F04 cleanups) | 503 | ~3,000 |
| Phase 4 Tier 3 (F14, F17 archives) | 1,822 | ~10,900 |
| F11 (skill dir + description trim) | 4 | ~50 |
| Independent: orphan scripts (test-lsp + 5 others) | 522 | ~3,100 |
| Independent: docstring-restate cleanup | 88 | ~530 |
| Total tracked-code reduction | **2,939** | **~17,600 tokens** |
| Cache cleanup (disk-only, gitignored) | n/a | 815 MB working-tree |

Estimates assume ~6 tokens/line average.

## Lessons for future bloat scans

1. **The bloat-detector's "no caller" check must include**
   pre-commit-config.yaml AND active slash command files
   (`plugins/*/commands/*.md`) AND developer documentation
   (`docs/quality-gates.md`, READMEs). Narrow grepping
   `Makefile/.github/.pre-commit-config.yaml` over-flags 30-40% of
   findings as false positives.
2. **WIP signals matter.** Active modifications in the working tree
   are evidence of intent; `git diff --stat` should annotate each
   bloat finding rather than be ignored.
3. **The "INVESTIGATE" tier in the agent report worked correctly.**
   None of F15-F19 were auto-applied, and all five turned out to be
   false positives. Keep this safety tier; do not promote LOW
   confidence to auto-action.

## Rollback

To undo this session's commits:

```bash
git reset --hard d1e42ddf
```

To restore individual files:

```bash
git checkout d1e42ddf -- <path>
```

The pre-session WIP edits in working tree (`clawhub-batch-publish.sh`,
`clawhub-cron.sh`, `clawhub-submit.sh`, `deploy-book.yml`) were left
untouched throughout this session.

## Next steps

1. Open a PR for the seven new commits from `ai-slop-1.9.4` to
   `master`.
2. Validate that the I2/I3 false-negative pattern (where the prior
   session's report wrongly stated `test-lsp-manually.sh` was absent)
   does not recur. Consider adding a verification step:
   `git ls-files <path>` after each DELETE finding to confirm actual
   removal.
3. Schedule a follow-up to fix the `pensive` env issue surfaced when
   running spec-kit tests at the wrong rootdir
   (`ModuleNotFoundError: psutil`). Pre-existing; not blocking.
