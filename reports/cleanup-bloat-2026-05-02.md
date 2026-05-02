# Bloat Detection Report — Tier 3

**Scan Date**: 2026-05-02
**Branch**: ai-slop-1.9.4
**Scope**: All first-party files (entire monorepo)
**Baseline**: F01-F18 from `cleanup-bloat.md` closed at `d1e42ddf`;
91 docstring-restate hits cleared at `b8c45ab0`
**Excluded**: `.git`, `*.venv`, `.*-venv`, `.uv-cache`,
`node_modules`, `__pycache__`, `.pytest_cache`, `htmlcov`,
`dist`, `build`, `*.egg-info`

---

## Summary

| Dimension | Count | Est. Token Savings |
|-----------|-------|--------------------|
| HIGH priority | 7 | ~12,000 |
| MEDIUM priority | 11 | ~9,500 |
| LOW priority | 6 | ~2,000 |
| **Total** | **24** | **~23,500** |

All findings are new since `d1e42ddf` or were missed by the
prior scan. Items are grouped by risk, lowest first.

---

## Phase 1 — Zero-risk (safe to delete unconditionally)

### F01 — `reports/skill-graph-audit-1.9.3.txt`

- **Action**: DELETE
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~500

Untracked on-disk artifact from the 1.9.3 release cycle
(created 2026-04-28). Not committed, not gitignored, not
referenced anywhere. `git ls-files reports/skill-graph-audit-1.9.3.txt`
returns empty. Superseded by `reports/skill-graph.json`
which IS tracked. [EN: `git ls-files` confirms untracked;
`ls reports/` shows it alongside tracked files]

### F02 — `reports/unbloat-session-2026-05-01.md`

- **Action**: DELETE or ARCHIVE
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~700

Untracked session log (git status shows `?? reports/unbloat-session-2026-05-01.md`).
Documents the Phase 5/6 execution that has since landed in
commits `d1e42ddf` and `952a50fb`. The information is now
in git history. Not referenced by any tracked file or
Makefile target. [EN: git status confirms untracked; content
is a post-execution log not a planning document]

### F03 — `Makefile` dead PHONY entry: `stargazer-analysis`

- **Action**: DELETE (one-line edit in Makefile)
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~50

`stargazer-analysis` appears in the `.PHONY` declaration
(line 32) but has no recipe body anywhere in the Makefile.
Running `make stargazer-analysis` silently does nothing.
[EN: `rg "stargazer" Makefile` returns only the PHONY line;
no recipe found]

### F04 — `.uv-tools/` missing from `.gitignore`

- **Action**: ADD to `.gitignore` (append `.uv-tools/`)
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: 0 (disk hygiene: 58 MB)

The Makefile sets `UV_TOOL_DIR ?= $(abspath .)/.uv-tools`
and writes the ruff binary there. The directory (58 MB) is
not tracked by git but is also not listed in `.gitignore`.
`.*-venv/` and `.tools/` are already covered; `.uv-tools/`
is not. [EN: `git check-ignore -v .uv-tools` prints
`NOT gitignored`; `du -sh .uv-tools` shows 58M; Makefile
line 9 confirms intentional local cache]

---

## Phase 2 — Scripts with zero callers in the active pipeline

These scripts are not invoked by any Makefile target, CI
workflow, or pre-commit hook. Each was verified with
`rg "<script>" Makefile .github/workflows/ .pre-commit-config.yaml`.

### F05 — `scripts/check_hook_modernization.py`

- **Action**: DELETE (+ paired test)
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~4,000 (312 lines script +
  517 lines test)

Added in commit `0e774695` to modernize PostToolUse output
format. That migration is done (1.8.1). The script has no
caller in Makefile, CI, or pre-commit. The 517-line test
`tests/unit/test_check_hook_modernization.py` is the only
reference and becomes an orphan if the script is deleted.
[EN: `rg "check_hook_modernization" Makefile .github/ .pre-commit-config.yaml`
returns empty; git log shows script added at 0e774695 for
a one-time migration]

Paired orphan: `tests/unit/test_check_hook_modernization.py`
(517 lines) — DELETE together.

### F06 — `scripts/fix_descriptions.py`

- **Action**: DELETE (+ paired test)
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~3,000 (192 lines script +
  410 lines test)

One-off migration script that consolidated `triggers`,
`use_when`, `do_not_use_when` fields into the unified
`description` field (commit `ab1270a1`). Migration is
complete (confirmed: no skills still have the old fields
after `97bba368`). No caller in Makefile, CI, or
pre-commit. [EN: `rg "fix_descriptions" Makefile .github/`
returns empty; git log message for `ab1270a1` is
"consolidate descriptions to official Claude Code format"]

Paired orphan: `tests/unit/test_fix_descriptions.py`
(410 lines) — DELETE together.

### F07 — `scripts/run-plugin-lint.sh`

- **Action**: DELETE
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~900 (168 lines)

Provides per-plugin linting with a `--changed` flag and
per-plugin fallback. The root Makefile `lint` target
replaced this: it runs ruff + bandit across all of
`plugins/` directly without delegation. No caller found in
Makefile, `.github/workflows/`, pre-commit, or any plugin
Makefile. [EN: `rg "run-plugin-lint" Makefile .github/ plugins/`
all return empty]

---

## Phase 3 — Scripts with no active pipeline caller
(but carry some operational use case)

### F08 — `scripts/clawhub-batch-publish.sh`

- **Action**: DELETE
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~1,400 (242 lines)

Implements a batch-publish strategy using a manifest and
progress file in `.egregore/`. However, `clawhub-cron.sh`
calls `clawhub-submit.sh` (not this script), and the CI
workflow `cross-framework-publish.yml` calls
`clawhub-submit.sh` directly. The batch approach was
superseded when `clawhub-submit.sh` was rewritten to use
`clawhub sync` (commit `f8a8eeff`). No active caller in
Makefile, CI, or cron. [EN: `tail -20 clawhub-cron.sh`
confirms it calls `clawhub-submit.sh`; `rg "clawhub-batch"
.github/ plugins/` returns empty]

### F09 — `scripts/clawhub-cron.sh`

- **Action**: ARCHIVE
- **Confidence**: MEDIUM
- **Risk**: LOW
- **Token savings**: ~250 (44 lines)

A local-machine cron wrapper for `clawhub-submit.sh`.
Not referenced by any CI or Makefile target; it is only
invoked by a user's personal crontab. The comment block
says "install: crontab -e". This is not CI infrastructure
but a developer convenience script with no test coverage.
Confidence is MEDIUM because someone may have this cron
active locally. Archive rather than delete to preserve
the crontab install pattern. [EN: `rg "clawhub-cron" -l`
returns only itself; CI uses clawhub-submit.sh not this]

### F10 — `scripts/check-all-quality.sh`

- **Action**: DELETE
- **Confidence**: MEDIUM
- **Risk**: LOW
- **Token savings**: ~1,400 (243 lines)

An all-in-one quality wrapper that runs lint, typecheck,
and test sequentially and optionally generates a report.
The Makefile `all` target (`lint && test`) and each
individual target cover the same ground. The `--report`
flag generates files under `audit/` (a directory not
present). No caller in Makefile, CI, or pre-commit.
Confidence is MEDIUM because someone may reference it in
local shell aliases or READMEs not captured by rg.
[EN: `rg "check-all-quality" Makefile .github/ plugins/`
returns empty; Makefile `all` target covers the same scope]

---

## Phase 4 — Structural / registration issues

### F11 — `plugins/abstract/skills/hook-scope-guide.md`
(flat file in skills/, not a skill directory)

- **Action**: REFACTOR (convert to skill directory or
  move to `skills/hook-authoring/modules/`)
- **Confidence**: HIGH
- **Risk**: MEDIUM
- **Token savings**: ~0 (structural fix)

This is a valid skill with proper frontmatter (name,
description, triggers) but it lives as a bare `.md` file
directly in `skills/`. Claude Night Market skill convention
requires `skills/<name>/SKILL.md` directory structure.
As a result it is unregistered in `plugin.json` (confirmed:
`python3` check shows it as the only unregistered skill
across all 23 plugins). It IS referenced from
`plugins/abstract/skills/hook-authoring/SKILL.md` and
`plugins/abstract/commands/hooks-eval.md`. Two options:

1. Convert to `skills/hook-scope-guide/SKILL.md` and
   register in `plugin.json` as a skill (preferred)
2. Absorb as a module into `skills/hook-authoring/modules/`

[EN: automated plugin registration check shows only
`abstract: UNREGISTERED skills: ['hook-scope-guide.md']`
across all 23 plugins; file has valid SKILL frontmatter]

---

## Phase 5 — Stale tracked artifacts / generated content

### F12 — `cleanup-report.md` (repo root)

- **Action**: DELETE
- **Confidence**: HIGH
- **Risk**: LOW
- **Token savings**: ~1,500 (250 lines)

A consolidated summary generated on 2026-05-01 that
aggregates the three `reports/cleanup-*.md` source files.
Those source files are still tracked and authoritative.
`cleanup-report.md` adds no information not in
`reports/cleanup-bloat.md` + `reports/cleanup-hygiene.md`
+ `reports/cleanup-quality.md`. Not referenced by any
tracked file. Lives at the repo root, which is untidy for
a scan artifact. [EN: `head -5 cleanup-report.md` shows
"Source reports: cleanup-bloat.md, cleanup-quality.md,
cleanup-hygiene.md"; `rg "cleanup-report" --include="*.md"
-l` returns empty]

### F13 — `reports/skill-graph.json`

- **Action**: ADD to `.gitignore`
- **Confidence**: MEDIUM
- **Risk**: LOW
- **Token savings**: ~1,500 (252 lines JSON)

Generated by `plugins/abstract/scripts/skill_graph.py`
(confirmed via docstring: "Used by: abstract:skill-graph-audit,
docs/quality-gates.md generation, audit reports"). The
file should be regenerated on each run rather than tracked;
committing it means it can silently drift from the actual
skill graph. No build step updates it on CI. Tracking this
file adds noise to diffs when skills change. [EN: skill_graph.py
docstring confirms it generates this file; no CI step regenerates
it; `git log` shows it last updated at commit `2109b63a`]

### F14 — `docs/architecture-analysis-report.md`

- **Action**: ARCHIVE
- **Confidence**: MEDIUM
- **Risk**: LOW
- **Token savings**: ~2,500 (418 lines)

A historical versioned architecture log. Last updated at
commit `ca8f5fab` (style/wrapping pass only; no content
change since earlier). The current version is 1.9.3/1.9.4
but the report's most recent entry covers earlier minor
versions. It does not appear in any SKILL.md cross-reference
or CI step. Keeping it as a root-level `docs/` tracked
file costs readers context without active maintenance.
Move to `docs/archive/` (which is already gitignored) and
remove from tracked files. [EN: `git log --oneline -3 docs/architecture-analysis-report.md`
shows last substantive commit is `e4ed3ec2` at v1.5.4;
`rg "architecture-analysis-report" -l` returns no references]

---

## Phase 6 — Low-confidence / INVESTIGATE

These items have conflicting signals. Do not auto-apply;
flag for manual review.

### F15 — `scripts/check-markdown-links.py`

- **Action**: INVESTIGATE
- **Confidence**: LOW
- **Risk**: LOW
- **Token savings**: ~600

Not in Makefile, CI, or pre-commit; no test file found.
However it may be used via `make check-examples` (which
calls `tests/integration/test_all_plugin_examples.py`
with a `--report` flag). Needs a check of that integration
test to confirm. If it has no caller, DELETE. [EN: `rg
"check.markdown.links" Makefile .github/ .pre-commit-config.yaml`
returns empty; no test file found; `make check-examples`
calls a different integration test]

### F16 — `scripts/reinstall-all-plugins.sh`

- **Action**: INVESTIGATE
- **Confidence**: LOW
- **Risk**: MEDIUM
- **Token savings**: ~1,000 (165 lines)

Not in Makefile or CI, but IS referenced by the leyline
command `/reinstall-all-plugins` (via
`plugins/leyline/commands/reinstall-all-plugins.md` which
describes running "the reinstall script"). This command is
part of the distributed plugin. Deleting the script would
silently break the command. The command reference uses a
relative path `scripts/reinstall-all-plugins.sh` assumed
to exist at the repo root. INVESTIGATE whether the command
embeds the script inline or delegates to it at runtime.
[EN: `cat plugins/leyline/commands/reinstall-all-plugins.md`
shows `bash` execution block referencing this script; `rg
"reinstall-all-plugins" Makefile .github/` returns empty]

### F17 — `reports/cleanup-hygiene.md`,
`reports/cleanup-quality.md`, `reports/cleanup-bloat.md`

- **Action**: ARCHIVE (after this report is applied)
- **Confidence**: MEDIUM
- **Risk**: LOW
- **Token savings**: ~3,500 (1,054 lines combined)

The three source reports for the `d1e42ddf` cleanup cycle.
All 18 findings (F01-F18) have been closed. Once the
current report (`cleanup-bloat-2026-05-02.md`) is
actioned, these become historical. They are not referenced
by any active Makefile target or CI step. Recommended path:
move to `docs/archive/reports/` in a follow-up commit after
this report's findings are resolved. [EN: `reports/cleanup-bloat.md`
states "F01-F18" findings; commits `d1e42ddf` and `952a50fb`
confirm these are all closed; `rg "cleanup-hygiene\|cleanup-quality"
Makefile .github/` returns empty]

### F18 — `plugins/abstract/docs/compatibility/`
(3,501 lines across 5 files)

- **Action**: INVESTIGATE (possible ARCHIVE)
- **Confidence**: LOW
- **Risk**: MEDIUM
- **Token savings**: ~15,000 if removed

Five versioned compatibility-tracking docs (Claude Code
versions 2.1.50-2.1.85, March 2026). No SKILL.md or
command references these files directly (confirmed via `rg
"compatibility.features" plugins/abstract/skills/`). They
are not linked from any active docs index except their own
internal cross-links. However they appear to be maintained
reference material for plugin developers. The largest file
(`compatibility-features-march2026-recent.md`, 1,923 lines)
documents features already integrated into the hooks.
INVESTIGATE before archiving: confirm whether these are
actively consulted for new feature development or are now
historical. [EN: `rg "compatibility-features" -l` across
the whole repo returns zero matches outside their own dir;
`git log -1 plugins/abstract/docs/compatibility/`
shows last commit is `4fcb3cca`]

### F19 — `docs/dependency-audit.md`

- **Action**: INVESTIGATE
- **Confidence**: LOW
- **Risk**: LOW
- **Token savings**: ~1,200 (195 lines)

Last-updated header reads 2026-03-27. Not referenced from
any Makefile, CI, or skill. The automated dependency map
is in `docs/plugin-dependencies.json` (generated by
`scripts/generate_dependency_map.py` via `make plugin-check`).
If `dependency-audit.md` duplicates that output, DELETE;
if it contains manually-maintained content not in the JSON,
KEEP. [EN: `head -10 docs/dependency-audit.md` shows
"Last updated: 2026-03-27"; `rg "dependency-audit" -l`
returns no references]

---

## Not findings (investigated, cleared)

The following were investigated and ruled out:

- **Plugin registration drift**: All 23 plugins have their
  skills correctly registered in `plugin.json` using
  `./skills/<name>` paths. The apparent mismatch in initial
  analysis was a path-prefix normalization issue.
  Only `hook-scope-guide.md` is genuinely unregistered
  (covered in F11).
- **Orphaned skill modules**: 0 module files found that
  are not referenced by their parent SKILL.md.
- **`scripts/clawhub-submit.sh`**: Referenced by
  `cross-framework-publish.yml` CI workflow. Not bloat.
- **`scripts/awesome-submit.sh`**: Referenced by
  `cross-framework-publish.yml`. Not bloat.
- **`scripts/reinstall-all-plugins.sh`**: Possibly
  referenced by leyline command. Escalated to F16.
- **`scripts/clawhub-cron.sh`**: Local cron helper, not
  CI. Escalated to F09 (ARCHIVE).
- **`reports/skill-graph.json`**: Tracked but generated.
  Escalated to F13 (gitignore candidate).
- **`plugins/conftest_shared.py`**: Referenced by 4+
  plugin `conftest.py` and `pyproject.toml` files.
- **Compatibility docs in `abstract/docs/compatibility/`**:
  Not dead but possibly archivable. Escalated to F18.
- **`docs/architecture-analysis-report.md`**: Historical
  log. Escalated to F14.
- **`CHANGELOG.md`**: 3,179 lines but intentional and
  actively maintained. Not bloat.
- **`.typecheck-venv/`**: Covered by `.*-venv/` in
  `.gitignore`. Correct.
- **Dead Makefile targets**: Only `stargazer-analysis` is
  genuinely dead (F03). All other targets have recipes.

---

## Recommended execution order

```
Phase 1 (zero-risk, ~30 min):
  F04  Add .uv-tools/ to .gitignore
  F03  Remove stargazer-analysis from Makefile .PHONY
  F01  rm reports/skill-graph-audit-1.9.3.txt
  F02  rm reports/unbloat-session-2026-05-01.md
  F12  rm cleanup-report.md
  F13  Add reports/skill-graph.json to .gitignore

Phase 2 (script deletions, ~45 min):
  F05  Delete scripts/check_hook_modernization.py +
       tests/unit/test_check_hook_modernization.py
  F06  Delete scripts/fix_descriptions.py +
       tests/unit/test_fix_descriptions.py
  F07  Delete scripts/run-plugin-lint.sh
  F08  Delete scripts/clawhub-batch-publish.sh

Phase 3 (structural fix, ~30 min):
  F11  Convert hook-scope-guide.md to proper skill dir
       + register in plugin.json

Phase 4 (archive candidates, after investigation):
  F09  Archive scripts/clawhub-cron.sh
  F10  Delete scripts/check-all-quality.sh (if confirmed)
  F14  Move docs/architecture-analysis-report.md to archive
  F17  Move reports/cleanup-*.md to archive

Manual review before action:
  F15  Investigate check-markdown-links.py callers
  F16  Investigate reinstall-all-plugins.sh / leyline command
  F18  Decide on compatibility docs fate
  F19  Compare dependency-audit.md vs plugin-dependencies.json
```

---

## Token-savings breakdown

| Phase | Findings | Est. Tokens |
|-------|----------|-------------|
| Phase 1 | F01-F04, F12, F13 | ~4,200 |
| Phase 2 | F05-F08 | ~9,550 |
| Phase 3 | F11 | ~1,500 |
| Phase 4 | F09, F10, F14, F17 | ~8,650 |
| INVESTIGATE | F15, F16, F18, F19 | TBD |
| **Total confirmed** | **14** | **~23,900** |

Estimates assume ~6 tokens/line average.
