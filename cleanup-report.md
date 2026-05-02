# Cleanup Report — claude-night-market

**Generated:** 2026-05-01
**Branch:** `ai-slop-1.9.4`
**Tier:** 3 (deepest)
**Scope:** entire monorepo (25 plugins, ~1,348 first-party Python
files, ~2,182 markdown files; venvs, node_modules, caches excluded)
**Mode:** scan-only (no `--apply`); no remediation executed
**Source reports:**

- `reports/cleanup-bloat.md` (400 lines, 18 findings)
- `reports/cleanup-quality.md` (544 lines, 12 findings)
- `reports/cleanup-hygiene.md` (460 lines, 15 findings + 3 P0)

---

## Unified score

| Dimension | Score | Findings | Top concern |
|-----------|-------|----------|-------------|
| Bloat | n/a (count-based) | 18 (6H/7M/5L) | Untracked artifacts present at scan-visible paths; broken `Makefile` target |
| Code quality | 67/100 | 12 (4H/5M/3L) | Acknowledged duplication without drift-guard; god-class in parseltongue |
| AI hygiene | 61/100 | 15 + 3 P0 | Self-narration in tutorials; em-dash density 9-13× over rule; slop-playbook commits are the primary slop source |
| **Composite** | **64/100** | **45 + 3 P0** | Recently-shipped feature work (slop playbook integration) is itself the largest contributor to detected debt |

**Estimated token savings if all DELETE/ARCHIVE findings actioned:**
~60,000 tokens of artifacts/scripts/docs (bloat) + ~2-4 KB per
em-dash-heavy file polished.

---

## Cross-cutting patterns (flagged by 2+ agents)

These deserve priority because multiple audits independently
converged on the same area.

### CC-1: The slop-playbook integration commits are the largest slop source

- **Hygiene F-04, F-05, F-06, F-08, F-09, F-10** flag the highest-density
  slop files — most are part of `b6e87193` and `0567817f` (4,937
  lines added 2026-05-01).
- **Bloat** does not flag this directly, but **Quality** notes 10.1%
  refactor ratio (lower bound) — feature additions are outpacing
  cleanup.
- **The branch name `ai-slop-1.9.4` makes this self-referential.**
  The shipped slop-detection tooling correctly identifies its own
  integration prose as slop.

### CC-2: `plugins/abstract/` skill ecosystem has registration drift

- **Bloat F16/F17:** two skills (`validate-plugin-structure.md`,
  `hook-scope-guide.md`) exist on disk but are not declared in
  `plugin.json` — Claude Code will not load them.
- **Quality F05/F06/F11:** SKILL.md files in abstract reference module
  paths via `../sibling-skill/modules/...` (works but fragile) and an
  example SKILL.md references modules that do not exist at all.
- **Combined effect:** the plugin most responsible for plugin-development
  patterns has the worst plugin-registration hygiene.

### CC-3: `egregore/` shows multiple defect classes

- **Quality F08:** O(n²) in `scripts/parallel.py`.
- **Quality F12:** unvalidated path in `scripts/watchdog.sh` passed to
  `cd` without an `[[ -d ]]` guard.
- **Hygiene F-11:** stale `pytest.skip("user_prompt_hook.py not yet
  created")` — the file now exists; the test has never run.
- **Combined effect:** egregore's recent additions ship without the
  same scrutiny as its surrounding plugins.

### CC-4: `scripts/` contains both bloat and quality concerns

- **Bloat F08-F14, F15:** seven scripts with zero callers in
  Makefile/CI/pre-commit, plus a Makefile target referencing a deleted
  file (`scripts/stargazer_overlap.py` removed in commit `a3f11323` but
  the target remains).
- **Quality F04:** `scripts/detect_duplicates.py` does 13 directory walks
  where 1 would suffice.
- **Bloat F08 notes** these scripts even have tests — meaning broken
  reference removal must also clean up orphaned tests.

### CC-5: Documentation drift

- **Bloat F05-F07:** `docs/tome-*.md` (2,012 lines) tracked despite
  matching gitignore patterns; content superseded by plugin README.
- **Hygiene F-04, F-05, F-06:** scribe modules with em-dash density up
  to 26/1000 (rule target <2).
- **Hygiene F-08:** "actionable" appears 122 times across 40+ files in
  prose contexts.
- **Hygiene P0-3:** bare `_(TODO)_` rows in public `docs/guides/README.md`.

---

## P0 merge blockers (3)

Per `.claude/rules/slop-scan-for-docs.md` Layer 0, these block merge
to master:

1. **Self-narration in `book/src/getting-started/first-plugin.md:8`**
   ("By the end of this tutorial, you'll:") — single-line fix.
2. **Self-narration in
   `plugins/sanctum/skills/tutorial-updates/modules/markdown-generation.md:178`**
   — higher blast radius because it sits inside a codegen template.
3. **Bare `_(TODO)_` cells in `docs/guides/README.md:175-176`** — link
   to tracker issues or delete rows.

Plus add: `Makefile:151` references a non-existent script — `make
stargazer-analysis` is a runtime error, not a merge blocker, but
should fix in the same pass.

---

## Phased remediation plan

### Phase 1 — Zero-risk quick wins (30 min total)

Untracked artifacts and broken references. No PR review needed (or one
small PR for the Makefile fix).

| ID | Action | Source | Effort |
|----|--------|--------|--------|
| Q1 | `rm -rf node_modules/` (509 MB; only dependency is unused gemini-cli npm) | Bloat F01 | 10s |
| Q2 | `rm coverage.xml` (73 KB; gitignored, regenerable) | Bloat F02 | 5s |
| Q3 | `rm -rf htmlcov/` (1.6 MB; gitignored, regenerable) | Bloat F03 | 5s |
| Q4 | `rm -rf __pycache__/` (root; gitignored) | Bloat F04 | 5s |
| Q5 | Fix or delete `Makefile:151` `stargazer-analysis` target | Bloat F15 | 2 min |
| Q6 | Remove stale `pytest.skip` in `plugins/egregore/tests/test_user_prompt_hook.py:19` and run test | Hygiene F-11 | 5 min |

### Phase 2 — P0 slop-rule fixes (15 min, single PR)

Required before next merge to master per `.claude/rules/slop-scan-for-docs.md`.

| ID | Action | Source | Effort |
|----|--------|--------|--------|
| P1 | Replace "By the end of this tutorial, you'll:" in `first-plugin.md:8` with thesis-first opener | Hygiene P0-1 | 2 min |
| P2 | Replace self-narration in `markdown-generation.md:178` codegen template | Hygiene P0-2 | 3 min |
| P3 | Resolve bare `_(TODO)_` in `docs/guides/README.md:175-176` (link issues or delete rows) | Hygiene P0-3 | 2 min |

### Phase 3 — Structural cleanup (1-2 h, single PR)

Tracked files; needs PR review.

| ID | Action | Source | Effort |
|----|--------|--------|--------|
| S1 | Un-track or delete `docs/tome-*.md` (3 files, 2,012 lines superseded by plugin README) | Bloat F05-F07 | 10 min |
| S2 | Archive or delete one-shot migration scripts (`add_cross_framework_fields.py`, `add_model_hints.py`, `cursor_lean_export.py`) and their tests | Bloat F08-F10 | 30 min |
| S3 | Resolve orphaned abstract skills (`validate-plugin-structure.md`, `hook-scope-guide.md`) — add to `plugin.json` or delete | Bloat F16-F17 | 15 min |
| S4 | Activate or remove `.pre-commit-hook-makefile-dogfood.yaml` | Bloat F18 | 10 min |
| S5 | Fix example SKILL.md links in `plugins/abstract/docs/examples/.../development-workflow/SKILL.md` (stub modules or use prose) | Quality F11 | 10 min |
| S6 | Add `[[ -d "$project_dir" ]]` guard before `cd` in `egregore/scripts/watchdog.sh:62-69` | Quality F12 | 5 min |
| S7 | Single-walk `find_duplicates` in `conserve/scripts/detect_duplicates.py:185-187` | Quality F04 | 10 min |
| S8 | Extract `_LANGUAGE_MARKERS` constant from `scribe/src/scribe/pattern_loader.py:118` | Quality F09 | 15 min |
| S9 | Merge overlapping `re.search` loops in `imbue/scripts/imbue_validator.py:180-212` | Quality E11 | 10 min |

### Phase 4 — Em-dash polish pass (2-3 h, doc-only PR)

Use `Skill(scribe:slop-detector)` per file rather than bulk regex —
some em-dashes are legitimate prose apposition.

| ID | Action | Source | Effort |
|----|--------|--------|--------|
| D1 | Reduce em-dashes in `narrative-structure.md` (26.2/1000 → ≤2/1000) | Hygiene F-04 | 30 min |
| D2 | Same for `update-ci.md` (20.4/1000) — replace `**label** —` separators with colons | Hygiene F-05 | 30 min |
| D3 | Same for `session-to-post/SKILL.md` (18.8/1000) | Hygiene F-06 | 30 min |
| D4 | Same for `incident-response.md` (19.6/1000) | Hygiene F-07 | 15 min |
| D5 | "actionable" purge across 40+ files (122 hits → <20 target) | Hygiene F-08-F-10 | 1 h |

### Phase 5 — Larger refactors (1-2 weeks, separate PRs each)

Each is a meaningful refactor needing its own PR and tests.

| ID | Action | Source | Effort |
|----|--------|--------|--------|
| R1 | Add `make check-json-utils` target diffing inlined hooks against `scripts/shared/json_utils.sh`; wire to pre-commit | Quality F01 | 4 h |
| R2 | Split `TestingGuideSkill` into 3 collaborators (`TestStructureAnalyzer`, `TestQualityEvaluator`, `TestRecommendationEngine`) | Quality F02 | 1-2 days |
| R3 | Extract `_count_content_bytes` from `tool_output_summarizer.py` (10 levels of nesting → 4) | Quality F03 | 4 h |
| R4 | Decompose `phantom/loop.py:run_loop` into `_process_iteration` + `_run_tool_block` | Quality F07 | 1 day |
| R5 | O(n²) → O(n) in `egregore/scripts/parallel.py:detect_independent_items` | Quality F08 | 2 h |
| R6 | Decompose `attune/scripts/plugin_project_init.py:initialize_plugin_project` (209 lines → 3 functions) | Quality F10 | 4 h |
| R7 | Add docstring-quality lint rule (or custom pre-commit hook) to flag restating docstrings; fix incrementally | Hygiene F-13/F-14 (1,185 instances) | 2 days |

### Phase 6 — Investigate before deleting (verify first)

| ID | Action | Source | Effort |
|----|--------|--------|--------|
| I1 | Confirm `scripts/parse-doc-sync.py` is fully superseded by `capabilities-sync-check.sh` before delete | Bloat F11 | 30 min |
| I2 | Confirm LSP guide + 3 LSP diagnostic scripts (`lsp-diagnostic.sh`, `lsp-vs-grep-comparison.sh`, `test-lsp-manually.sh`) still relevant | Bloat F12-F14 | 30 min |
| I3 | Investigate file thrashing on `rigorous-reasoning/SKILL.md` (12 commits/30 days) — design churn vs. ownership churn | Hygiene F-12 | 30 min |

---

## Token-savings estimate

| Phase | Token impact (working-tree footprint) |
|-------|---------------------------------------|
| 1 | ~5,200 tokens (gitignored artifacts removed from `find` paths) |
| 2 | ~50 tokens (P0 lines) |
| 3 | ~5,400 tokens (tome docs + scripts + orphans) |
| 4 | ~3,000 tokens (em-dash polish reduces verbiage) |
| 5 | structural; net token impact ~neutral but reader-time improvement |
| **Total** | **~60,000 tokens** of context-scan footprint reduction |

---

## Rollback safety

Since `--apply` was not passed, no changes have been executed. When
remediating:

- **Phase 1 (Q2-Q4):** untracked artifacts; trivially regenerable
  via `make test` / `npm install`.
- **Phase 1 (Q1):** delete only after confirming gemini-delegation skill
  doesn't actually invoke the npm binary (current evidence: 0 hits).
- **Phase 2-4:** standard PR workflow; create branch
  `cleanup/unbloat-2026-05-01`, commit per phase.
- **Phase 5:** each refactor is its own PR with TDD red-green-refactor;
  Iron Law applies.
- **Phase 6:** investigate before deletion; do not bulk-delete.

Recommended branching: `git checkout -b cleanup/unbloat-2026-05-01`,
then commit per phase with conventional commit messages.

---

## Anti-goals respected

Per `.claude/rules/slop-scan-for-docs.md` anti-goals:

- Em-dash polish recommendations preserve apposition uses; do not
  bulk-regex.
- "actionable" purge does not collapse rule files where the term is
  documented as anti-pattern.
- God-class refactor (`TestingGuideSkill`) follows the existing
  `BaseReviewSkill` pattern — does not introduce a new abstraction.
- Restating-docstring fix recommended as lint rule, not bulk rewrite —
  many test docstrings are correctly removed rather than improved.
- The `scribe:slop-detector` catalog is excluded from slop scans (it
  legitimately lists slop terms as anti-patterns).

---

## Next steps

1. Review this report with the user.
2. If approved: create branch `cleanup/unbloat-2026-05-01`.
3. Execute phases in order; commit per phase.
4. After Phase 1-4 land: re-run `Skill(conserve:bloat-detector)` to
   confirm remediation; expect bloat findings to drop from 18 to
   ~5-8.
5. Phase 5 refactors should be opened as individual PRs over the
   following weeks.
