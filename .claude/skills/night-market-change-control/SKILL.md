---
name: night-market-change-control
description: 'Classify, gate, and review changes. Use when landing a PR, releasing, or amending rules. Do not use for failure triage; use night-market-debugging-playbook.'
---

# Night Market Change Control

Every change to this repo passes through a fixed law stack, a
classification step, and a gauntlet of automated gates. This skill tells
you which class your change is, which gates it must pass, and which
rules are non-negotiable because a past incident made them so. Nothing
here may be routed around: if a gate fails, fix the cause, never the
gate.

Jargon used below: a "gate" is any automated check that can block a
commit, PR, or release. An "ADR" is an Architecture Decision Record in
`docs/adr/`. The "Iron Law" is constitution rule 3: no implementation
without a failing test first.

## The law stack

When two documents conflict, the higher one wins.

| Rank | Source | Contents |
|------|--------|----------|
| 1 | `CONSTITUTION.md` | 10 immutable rules, override and amendment process |
| 2 | `.claude/rules/` | 8 project rules (markdown style, read budgets, slop gates, invariants) |
| 3 | `docs/adr/` | 17 numbered decision records (0001 to 0017) |
| 4 | Guides in `docs/` | quality-gates, testing-guide, plugin-development-guide |

A skill, hook, or agent instruction that says "skip rule N" without an
explicit user grant or a merged amendment is itself a defect
(CONSTITUTION.md, Override mechanism section).

## The ten constitution rules

One line each. Where a rule was written in blood, the incident column
names the blood.

| # | Rule | Motivating incident |
|---|------|---------------------|
| 1 | Disclose AI involvement in every PR; never strip real or add fake AI attribution | Enforced by hook `plugins/imbue/hooks/vow_no_ai_attribution.py` |
| 2 | AI commits over 200 changed lines need a spec, ADR, or plan doc first (lockfiles, fixtures, snapshots excluded) | Size = scrutiny principle; see the unbloat incident under non-negotiables |
| 3 | Iron Law TDD: failing test before implementation for plugin Python. Skills and prose need structural tests (`test_skill_<name>.py`) | Design principle, no single incident |
| 4 | One identity leak ("As a large language model") in any committed artifact is an automatic revert | Pattern catalog in scribe slop-detector |
| 5 | Quality claims ("fast", "production-ready") need in-repo evidence or deletion | Design principle |
| 6 | No bypassing gates: no `--no-verify`, no `SKIP=hook`, no unauthorized force push, no bare suppression comments without a stated reason | Neutered-mypy incident (CHANGELOG 1.9.12); bulk-ignore revert `06b9b1db` |
| 7 | New dependencies need justification; 18 months unmaintained is presumed abandoned; verify AI-suggested package names against the registry | Slopsquatting defense; hook `guard_package_hallucination.py` (imbue) |
| 8 | Docs cost reader-time (audience x frequency x per-read time); writing effort must match | Design principle |
| 9 | Prefer deletion over rewriting; AI slop is overwhelmingly additive | Design principle |
| 10 | Errors are not optional: propagate by default, no bare except, safe-to-discard needs an inline "why" comment | Silent-failure sweep `666171c3`; ecosystem bare-except campaign |

## Change classification

Classify before the first commit. The class decides the paperwork.

| Change | Required process |
|--------|------------------|
| AI-generated diff, 200 changed lines or fewer | Plain PR through the standard gates |
| AI-generated diff over 200 changed lines | Spec, ADR, or planning doc BEFORE the code (rule 2) |
| Load-bearing design decision | Numbered ADR in `docs/adr/` (next number after 0017) |
| New project-wide rule | New file in `.claude/rules/` via plain PR; existing rules cite an origin issue or discussion (#454, #457) |
| Constitution amendment | PR titled `constitution: amend rule N`, a summary of what changes and why, sign-off from the repo owner |
| Release | Version bump, changelog section, v-prefixed tag (lifecycle below) |

## The change lifecycle

### 1. Branch

Branch from `master` (the main branch) using `<topic>-<version>`:

```bash
git checkout master && git pull
git checkout -b my-topic-1.9.16
```

Live examples in `git branch -a`: `ai-slop-1.9.4`, `bugfixes-1.9.5`,
`discussions-fix-1.9.14`. Never delete `backup/unbloat-*` branches.
They are the recovery points for past deletion campaigns
(`backup/unbloat-20260328` is how the 2026-03-28 over-deletion was
undone).

### 2. Local gates before committing

```bash
make lint          # ruff format + ruff check --fix + bandit
make typecheck     # per-plugin strict mypy (all plugins)
make test          # per-plugin pytest via scripts/run-plugin-tests.sh
make validate-all  # plugin structure validation
```

Plugin tests MUST run per plugin (`make <plugin>-test` or
`make -C plugins/<plugin> test`). Root pytest excludes `plugins/*` to
avoid import-path collisions.

### 3. The pre-commit gauntlet

`git commit` runs `.pre-commit-config.yaml` hooks in this order
(verified 2026-07-02):

1. Suppression guards: `check-noqa` (blocks bare inline lint
   suppressions), `check-docstring-quality`, `check-json-utils-drift`,
   `check-per-file-ignores`.
2. Hook registration: `check-hook-registrations`,
   `check-plugin-hooks`.
3. Code gates: `run-plugin-typecheck --all` (strict mypy on every
   plugin, not just changed ones), `run-plugin-tests --changed`.
4. Skill and plugin validation: `validate-skill-descriptions`, one
   `validate-<plugin>-plugin` hook per plugin,
   `check-context-optimization`, `validate-description-budget`,
   `check-markdown-links`, `capabilities-sync-check`,
   `check-skill-graph-drift`, `check-skill-exit-criteria-drift`.
5. Standard file hygiene (trailing whitespace, YAML/TOML/JSON syntax,
   merge conflicts, debug statements).
6. `bandit` security scan.
7. `ruff-format`, `ruff-fix`, `ruff-check`.
8. Pin freshness: `check-ruff-version`, `check-pinned-versions`.

The typecheck gate runs `--all` deliberately. It used to run
`--changed`, and a global mirrors-mypy hook silently disabled 13 error
codes. Both were fixed in 1.9.12 (CHANGELOG). Do not weaken either
setting.

### 4. PR flow

Run in this order (all are sanctum slash commands):

1. `/sanctum:prepare-pr` updates docs, runs tests, drafts the PR.
2. `/sanctum:pr-review` reviews scope, requirements, and code.
3. `/sanctum:validate-pr` builds and executes a diff-derived test
   plan, and proves revert-tests are genuine guards.
4. `/sanctum:fix-pr` and `/sanctum:resolve-threads` handle feedback.

For plugin-touching changes, add `abstract:plugin-review` at the
matching tier:

| Tier | When | Scope | Time |
|------|------|-------|------|
| branch | Default during work | Affected and related plugins | ~2 min |
| pr | Before merge | Affected and related plugins | ~5 min |
| release | Before version bump | Every plugin | ~15 min |

### 5. Release

1. Bump the ecosystem version. `.claude-plugin/marketplace.json` is
   the source of truth; the bumper fans it out to every plugin's
   `plugin.json`, `metadata.json`, `openpackage.yml`, `pyproject.toml`,
   and `__init__.py`:

   ```bash
   python3 plugins/sanctum/scripts/update_versions.py 1.9.16
   ```

   Or use the `sanctum:version-updates` skill, which runs a
   `git-workspace-review` preflight first.

2. Move `[Unreleased]` entries in `CHANGELOG.md` into a dated version
   section (Keep a Changelog 1.1.0, SemVer). Never rewrite or de-slop
   historical entries.

3. Update the docs of record: `docs/api-overview.md` version
   reference, plugin READMEs, and the generated capabilities reference
   via `/sanctum:sync-capabilities`.

4. Run `abstract:plugin-review --tier release`.

5. `/sanctum:create-tag` pushes a v-prefixed tag. The tag matching
   `v*` triggers `.github/workflows/cross-framework-publish.yml`
   (semver validation, cross-framework build, tarballs, GitHub
   release). Pushes to `master` separately trigger
   `trust-attestation.yml` (full test run plus SLSA attestation).

## Landing a change: checklist

| Step | Action | Gate satisfied |
|------|--------|----------------|
| Classify | Match the change against the classification table | Rule 2, amendment process |
| Branch | `<topic>-<version>` off master | Convention |
| Test first | Failing test before implementation | Rule 3 (Iron Law) |
| Local gates | `make lint && make typecheck && make test` | Rule 6 |
| Commit | Plain commit, no bypass flags, honest attribution | Rules 1 and 6 |
| PR | prepare-pr, pr-review, validate-pr; disclose AI involvement | Rule 1 |
| Plugin review | `abstract:plugin-review` at branch or pr tier | Plugin quality |
| Merge | All CI checks green, review threads resolved | CI |

## Non-negotiables

Each row is a settled battle. Re-litigating one requires new evidence
stronger than the incident that settled it.

| Non-negotiable | Rationale | Incident | Evidence |
|----------------|-----------|----------|----------|
| Never bypass or weaken a gate | A green gate that skips checks is worse than no gate: it certifies broken code | mirrors-mypy silently disabled 13 error codes; typecheck ran changed-only; bulk ruff ignores hid 73 real violations | CHANGELOG 1.9.12; commit `06b9b1db` |
| No swallowed errors, ever | catch-and-continue in a scanner drops findings silently and reports clean | Scanners B1-B4 returned clean results on malformed input for months | commit `666171c3` (PR #521, issue #575) |
| Deletion campaigns need a backup branch and a markdown-reference scan | Python import graphs miss scripts referenced only from skills and commands | Tier-3 unbloat deleted 182 files (66K lines); skill-referenced scripts had to be restored | commits `a3f11323` (delete), `3f280334` (restore); branch `backup/unbloat-20260328` |
| No DRY consolidation across plugin boundaries | Plugins are independent deployables, and shared code couples their release cycles | tasks_manager consolidated to a shared script, reverted, then differentiated per plugin | commits `054e2679`, `29961cd2`, `d89a55c7` |
| No speculative infrastructure | Unused abstraction is pure carrying cost | LSP proxy landed without a consumer and was reverted in PR #193 review | commit `bc318947` |
| Identity leaks are an automatic revert | One leaked phrase proves unreviewed AI text shipped | Constitution rule 4 | `CONSTITUTION.md` |
| Historical CHANGELOG entries are never edited | The changelog is a record, not prose to polish | Codified as an anti-goal in the slop rules | `.claude/rules/slop-scan-for-docs.md` (anti-goals) |

## When NOT to use

- A gate is failing and you need to diagnose why: use
  `night-market-debugging-playbook`.
- You want the full story behind an incident named above: use
  `night-market-failure-archaeology`.
- You need the mechanics of running tests, lint, or the release
  scripts (flags, artifacts, environments): use
  `night-market-operations`.
- You are judging whether a design fits the architecture: use
  `night-market-architecture-contract`.
- You are deciding what evidence a test must provide: use
  `night-market-validation-and-qa`.

## Exit Criteria

- [ ] The change is classified against the classification table, and
      any over-200-line AI diff has a spec, ADR, or plan doc committed
      before the implementation.
- [ ] `make lint`, `make typecheck`, and `make test` pass locally, and
      no bypass flag (`--no-verify`, `SKIP=`, force push) appears in
      the branch history.
- [ ] The branch name matches `<topic>-<version>` and is based on
      `master`.
- [ ] The PR description discloses AI involvement (authored,
      co-authored, or reviewed).
- [ ] For a release: `marketplace.json`, the dated `CHANGELOG.md`
      section, and the pushed `v*` tag all carry the same version.
- [ ] Any constitution change is in a PR titled
      `constitution: amend rule N` with repo-owner sign-off.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 (10 constitution rules, 8
project rules, 17 ADRs). Re-verify volatile facts before relying on
them:

```bash
rg -c '^### [0-9]' CONSTITUTION.md          # expect 10
ls .claude/rules/ | wc -l                    # expect 8
ls docs/adr/ | wc -l                         # expect 17
rg -n '"version"' .claude-plugin/marketplace.json | head -1
rg -n '      - id:' .pre-commit-config.yaml  # current gate order
rg -n 'v\*' .github/workflows/cross-framework-publish.yml
rg -n 'amend rule' CONSTITUTION.md           # amendment title convention
```

Commit hashes cited above were verified with `git log --oneline -1
<hash>` on 2026-07-02. Unverified/candidate: the exact count of files
restored after the unbloat incident (commit subjects confirm the
delete and restore, not the restored-file count), and whether
`docs/api-overview.md` holds a version table or a single version
reference (one version mention verified).
