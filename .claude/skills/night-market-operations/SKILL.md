---
name: night-market-operations
description: "Run and ship this repo: make targets, artifacts, release runbook. Use when testing, linting, or releasing. Do not use for setup; use night-market-build-and-env."
---

# Night Market Operations

This skill is the runbook for operating the claude-night-market repo:
what each make target actually executes, where artifacts land, and the
exact sequence that ships a release. Every command below was verified
against the Makefile, scripts/, and .github/workflows/ on 2026-07-02
(repo v1.9.15).

Terms used once and reused throughout:

- **Plugin**: a directory under `plugins/` with a
  `.claude-plugin/plugin.json` manifest. Most have their own Makefile,
  pyproject.toml, and tests/.
- **skrills**: a Rust CLI for skill validation and token analysis,
  vendored at `plugins/abstract/bin/skrills`. Every skrills target has
  a Python fallback, so a missing binary never blocks you.
- **ClawHub export**: a cross-framework skill package format written to
  `clawhub/` by `scripts/clawhub_export.py`.

All commands run from the repo root unless a `cd` is shown. `uv` is
required for everything Python. For environment setup, see
night-market-build-and-env.

## Command anatomy

| Command | What it actually executes | When to use | Expected output shape |
|---------|---------------------------|-------------|-----------------------|
| `make test` | `./scripts/run-plugin-tests.sh --all`: per plugin, runs `make test --quiet` if the plugin Makefile has a `test:` target, else `uv run python -m pytest tests/ --tb=short --quiet` if pyproject mentions pytest. Skips plugins without `tests/`. | Full sweep before a PR or release. | Per-plugin pass/fail/skip lines. Failures re-run verbose. |
| `make lint` | `uv run ruff format plugins/`, then `uv run ruff check --fix plugins/`, then ruff format again, then `uv run bandit --quiet -c pyproject.toml -r plugins/`. All use root pyproject.toml config. | Before every commit. Mutates files (auto-fix). | Four staged sections ending "Lint Complete". |
| `make typecheck` | `./scripts/run-plugin-typecheck.sh --all`: per-plugin `uv run mypy` under each plugin's own strict config, plus a separate `uv run mypy hooks/` pass when `hooks/*.py` exists. | After type-touching changes and before release. | Per-plugin pass/fail. Hooks checked as a sub-step. |
| `make validate-all` | `python3 plugins/abstract/scripts/validate_plugin.py <plugin>` for every plugin. Failures print "(validation failed)" but do NOT stop the loop or fail the target. | Structure audit after manifest edits. | One validation block per plugin. Read output, not exit code. |
| `make plugin-check` | For each plugin whose Makefile has a `plugin-check:` target: `timeout 180 make -C plugins/<p> plugin-check`. Failures and timeouts print a note, exit code stays 0. | Dogfood/demo sweep before release. | Per-plugin sections. Watch for "(plugin-check failed or timed out)". |
| `make docs-sync-check` | `bash scripts/capabilities-sync-check.sh` | PR touches plugin manifests or skills (mirrors capabilities-sync.yml CI). | Drift list or clean pass. Fix drift with `/sanctum:sync-capabilities --fix`. |
| `make supply-chain-scan` | `python3 scripts/supply_chain_scan.py` | After dependency or lockfile changes. | Scan report between banner lines. |
| `make validate-skills` | `skrills validate --skill-dir plugins --target claude` (plugin bin, then PATH). Falls back to `uv run python scripts/check_plugin_hooks.py`. | Skill frontmatter/structure check. | skrills report, or the Python fallback notice plus its output. |
| `make analyze-skills` | `skrills analyze --skill-dir plugins`. Falls back to `uv run python scripts/generate_dependency_map.py`. | Skill token-budget and dependency analysis. | Token/dependency stats. |
| `make status` | `make -C <plugin> status` for every plugin. | Quick overview. | Per-plugin status or "(status unavailable)". |
| `make clean` | `make -C <plugin> clean` for every plugin, errors ignored. | Reset build artifacts. | "Done." |

Two targets have soft failure modes worth repeating: `make validate-all`
and `make plugin-check` keep going past failures and can exit 0 while a
plugin is broken. Read their output. Do not treat a green exit as proof.

## Scoping runs: one plugin, one file

The root Makefile auto-generates delegation targets for every plugin
that has a Makefile. `make <plugin>-<target>` is identical to
`make -C plugins/<plugin> <target>`:

```bash
make sanctum-test        # run sanctum's test suite
make imbue-lint          # run imbue's lint target
make abstract-help       # list a plugin's own targets
```

Run a single test file from inside the plugin directory:

```bash
cd plugins/imbue && uv run pytest tests/unit/test_deferred_capture.py -x -q
```

Rules that save you an hour:

- Never run root `pytest` expecting plugin tests to run. Root
  pyproject.toml sets `norecursedirs = ["plugins/*", ...]` because
  plugin conftest.py files collide on import paths. Plugin tests run
  per-plugin, always.
- Some plugins force coverage on every run. imbue's pytest `addopts`
  include `--cov=scripts`, `--cov-report=html:htmlcov`, and
  `--cov-report=xml`, so even a single-file run writes `htmlcov/` and
  `coverage.xml` into `plugins/imbue/`. This is normal, not a mess you
  made.
- Coverage thresholds: root coverage `fail_under = 85`. Per-plugin
  overrides live in each plugin's `[tool.nightmarket]`
  `coverage_threshold` (per-plugin values: see
  night-market-validation-and-qa, the designated home for the
  threshold inventory). `run-plugin-tests.sh` reads that value and
  passes `--cov-fail-under=<n>` when the plugin runs via the pytest
  path.

## Artifact conventions

| Artifact | Producer | Location | Committed? |
|----------|----------|----------|------------|
| `htmlcov/`, `coverage.xml` | pytest coverage addopts | Repo root and per-plugin dirs | Present in tree but regenerated. Never hand-edit |
| `reports/skill-graph.json` | skill-graph tooling | `reports/` | No, generated locally (`reports/` is gitignored). Rebuild with the skill-graph tooling |
| `clawhub/` | `make clawhub-export` | `clawhub/manifest.json` plus one `nm-<plugin>-<skill>/` dir per exported skill | No, generated locally. `make clawhub-export` rebuilds it, and the release workflow regenerates it in CI |
| `bridge/openclaw/`, `bridge/a2a/` | `make bridge-build`, `make a2a-cards` | `bridge/` | Build outputs. `make bridge-clean` removes skills and a2a |
| `book/build/` | `mdbook build` (book/book.toml sets `build-dir = "build"`) | `book/build/` | No, CI-built |
| `trust-report.json` | CI only: trust-attestation.yml on push to master | Workflow workspace, SLSA-attested | No, never in tree |

## Release runbook

The ecosystem ships as one version. `.claude-plugin/marketplace.json`
is the version source of truth, fanned out to every plugin manifest.
Gates and review policy are night-market-change-control territory.
This is the mechanical sequence.

1. **Preflight.** Run `Skill(sanctum:git-workspace-review)` (read-only
   workspace check). Confirm you are on a `<topic>-<version>` branch,
   not master.

2. **Bump the version everywhere.** Dry-run first:

   ```bash
   uv run python plugins/sanctum/scripts/update_versions.py 1.9.16 --dry-run
   uv run python plugins/sanctum/scripts/update_versions.py 1.9.16
   git diff --stat
   ```

   The script rejects anything not matching `^\d+\.\d+\.\d+$`, then
   rewrites the version field in every match of these globs (cache and
   venv dirs excluded): `**/pyproject.toml`, `**/Cargo.toml`,
   `**/package.json`, `**/.claude-plugin/plugin.json`,
   `**/.claude-plugin/metadata.json`,
   `**/.claude-plugin/marketplace.json`, `**/openpackage.yml`, and any
   `**/__init__.py` containing `__version__`. Expect a large diff
   of roughly 100 files. That is the design.

3. **CHANGELOG entry.** CHANGELOG.md follows Keep a Changelog 1.1.0
   with SemVer. Keep `## [Unreleased]` at the top and insert
   `## [X.Y.Z] - YYYY-MM-DD` directly below it. Never rewrite or
   de-slop historical entries.

4. **Docs sync.** Update the per-plugin version column in
   `docs/api-overview.md`. Then:

   ```bash
   make docs-sync-check
   ```

   If it reports drift between plugin.json registrations and the
   capabilities reference (`book/src/reference/`, generated content),
   run `/sanctum:sync-capabilities --fix`.

5. **PR and gates.** Open the PR and clear the gates per
   night-market-change-control (pre-commit hooks, slop-check on docs,
   capabilities-sync, typecheck, security workflows).

6. **Merge to master.** trust-attestation.yml fires on the push: it
   runs `make test`, writes `trust-report.json`, and attaches a SLSA
   provenance attestation via `actions/attest-build-provenance@v4`.

7. **Tag.** Run `/sanctum:create-tag v1.9.16`. It pushes a v-prefixed
   annotated tag and confirms the release pipeline started.

8. **Release pipeline.** cross-framework-publish.yml fires on `v*`
   tags: it strips the `v`, validates the version against
   `^[0-9]+\.[0-9]+\.[0-9]+`, runs the cross-framework unit tests
   (clawhub_export, build_bridge, a2a_cards, framework_detect), runs
   `make cross-framework`, packages four tarballs
   (`night-market-clawhub`, `night-market-openclaw-bridge`,
   `night-market-a2a-cards`, `night-market-cross-framework`), and
   creates the GitHub release. Precondition: the publish job fails if
   `clawhub/manifest.json` is missing or its `total_exported` is 0
   (currently 188). Post-release ClawHub submission is manual:
   `./scripts/clawhub-submit.sh v<version>`.

Release checklist:

- [ ] `make test`, `make lint`, `make typecheck` all pass locally
- [ ] `update_versions.py` diff reviewed and marketplace.json shows the
      new version
- [ ] CHANGELOG has the new section, `[Unreleased]` still on top
- [ ] `make docs-sync-check` clean
- [ ] Tag pushed, both workflows green, release has 4 tarball assets

## Book publishing

The mdBook under `book/` deploys via deploy-book.yml:

- Triggers: push to master or main touching `book/**` or the workflow
  file itself, plus PRs on the same paths (build-only) and manual
  dispatch.
- Build: `peaceiris/actions-mdbook@v2` with `mdbook-version: 'latest'`,
  then `mdbook build` with working-directory `book`. Output
  `book/build` uploads via `actions/upload-pages-artifact@v5` and
  deploys with `actions/deploy-pages@v5`, with one retry step if the
  first deploy fails.
- Known fragility: mdbook is unpinned ("latest"), so a new upstream
  mdbook release can break the build with no change in this repo. If
  the book job fails right after an mdbook release, suspect that first.

Local preview, if mdbook is installed:

```bash
cd book && mdbook build   # output in book/build/
```

## Cross-framework export surface

```bash
make clawhub-export       # export all skills to clawhub/, then validate
make clawhub-export-top   # top 20 most marketable skills only
make clawhub-validate     # re-validate an existing export
make clawhub-stats        # export statistics, no writes
make bridge-build         # (depends on clawhub-export) build bridge/openclaw/
make a2a-cards            # generate A2A agent cards into bridge/a2a/
make a2a-list             # list agents eligible for card generation
make detect-framework     # detect the active agentic framework
make cross-framework      # all of the above: export + bridge + cards
```

`make cross-framework` is exactly what the release pipeline runs, so
running it locally before tagging catches export failures early. It
prints skill and agent counts and ends with framework detection.

## When NOT to use

| You want | Use instead |
|----------|-------------|
| Set up uv, Python, tools from scratch | night-market-build-and-env |
| Classify a change, know which gates apply | night-market-change-control |
| Diagnose a failing test or broken hook | night-market-debugging-playbook |
| Configuration axes, env vars, defaults | night-market-config-catalog |
| Coverage discipline and evidence bar | night-market-validation-and-qa |
| Plugin/skill/hook mechanics | claude-code-plugin-reference |
| Measurement tooling interpretation | night-market-diagnostics-toolkit |
| Stop an egregore loop or its watchdog relaunch machinery | night-market-completion-integrity-campaign (P1b, "Stopping and relaunch machinery") |

## Exit Criteria

- [ ] The chosen make target ran and its per-plugin summary was read,
      beyond the exit code alone. For `make validate-all` and
      `make plugin-check`, output was scanned for embedded failure
      notes.
- [ ] Single-plugin or single-file test runs were executed from inside
      the plugin directory, never via root pytest.
- [ ] For a release: `update_versions.py` diff verified, CHANGELOG
      section added, `make docs-sync-check` clean, tag pushed, and the
      GitHub release shows all four tarball assets.
- [ ] Any generated artifact (htmlcov, coverage.xml, clawhub/,
      book/build) was identified as generated and not hand-edited.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15, branch discussions-fix-1.9.14.
Coverage-threshold inventory delegated to night-market-validation-and-qa
and the egregore stop cross-reference added on 2026-07-03.
Volatile facts and how to re-verify them:

```bash
# Make target wiring
sed -n '60,150p' Makefile && sed -n '150,300p' Makefile

# Test runner behavior (delegation, coverage threshold, skip logic)
sed -n '1,110p' scripts/run-plugin-tests.sh

# Version bump globs and semver regex
rg -n "patterns|re.match" plugins/sanctum/scripts/update_versions.py

# Release pipeline gates
rg -n "tags|total_exported|tar -czf" \
  .github/workflows/cross-framework-publish.yml

# Attestation flow
rg -n "make test|attest|trust-report" \
  .github/workflows/trust-attestation.yml

# Book deploy and mdbook pin
rg -n "mdbook-version|deploy-pages|working-directory" \
  .github/workflows/deploy-book.yml

# Current export count (was 188 on 2026-07-02)
python3 -c "import json; \
  print(json.load(open('clawhub/manifest.json'))['total_exported'])"

# Coverage thresholds
rg -n "coverage_threshold" plugins/*/pyproject.toml
rg -n "fail_under" pyproject.toml
```
