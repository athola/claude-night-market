---
name: night-market-build-and-env
description: "Rebuild the dev environment: uv, Python tiers, pins, traps. Use when onboarding or toolchain breaks. Do not use for daily commands; use night-market-operations."
---

# night-market-build-and-env

Recreate a working claude-night-market development environment from a
bare machine, verify it in under an hour, and avoid the traps that have
broken it before. Everything below was verified against the repo on
2026-07-02 (v1.9.15).

One rule dominates: every Python tool runs through `uv run`. uv is
Astral's Python package and environment manager. On first `uv run` it
creates `.venv/` and syncs it from `uv.lock`. Never install repo
dependencies with bare `pip`.

## Toolchain setup

Install in this order. "via uv" means the tool resolves from `uv.lock`
automatically. There is no manual install step for those rows.

| # | Tool | Required? | Install hint | Verify command |
|---|------|-----------|--------------|----------------|
| 1 | uv | REQUIRED | official installer at astral.sh/uv | `uv --version` |
| 2 | Python 3.12 | REQUIRED | `uv python install 3.12` | `python3 --version` |
| 3 | make + bash | REQUIRED | GNU make 3.82+ (Xcode CLT ships 3.81, which ignores `.SHELLFLAGS`; `brew install make`, run `gmake`) | `make --version` |
| 4 | ruff >=0.14.13 | via uv | none (dev dependency in `uv.lock`) | `uv run ruff --version` |
| 5 | bandit | via uv | none (pre-commit env is pinned separately, see traps) | `uv run bandit --version` |
| 6 | mypy >=1.13 | via uv | none | `uv run mypy --version` |
| 7 | pre-commit >=4 | via uv | `uv run pre-commit install` | `uv run pre-commit --version` |
| 8 | Python 3.9 | optional | `uv python install 3.9` | `uv venv --python 3.9 /tmp/py39-check` |
| 9 | node + npm | optional | needed for conjure Gemini delegation | `node --version` |
| 10 | Rust + cargo | optional | rustup (only for `make skrills-build`) | `cargo --version` |
| 11 | skrills binary | optional | `make skrills-build` or `make skrills-install` | `make skrills-verify` |
| 12 | mdbook | optional | `cargo install mdbook`; builds `book/` | `mdbook --version` |
| 13 | gh CLI | optional | cli.github.com (releases and Discussions) | `gh --version` |

Notes on the optional rows:

- Python 3.9 is ONLY for local hook-compatibility testing. Hooks are
  scripts Claude Code runs on tool events under the host system Python
  (macOS ships 3.9.6), outside any virtual environment. CI enforces
  this in `.github/workflows/python39-compat.yml`.
- The conjure plugin delegates to Gemini. The root `package.json` pins
  `@google/gemini-cli` at `^0.25.1`. Run `npm install` at the repo root
  only if you use conjure delegation.
- skrills is a Rust CLI that validates and analyzes skill files. Every
  Makefile target that uses it (`make validate-skills`,
  `make analyze-skills`) has a Python fallback, so you can skip Rust
  entirely.
- gh is needed for releases and for GitHub Discussions. Discussions
  have no `gh discussion` subcommand. They are reachable only through
  `gh api graphql`.

Version numbers observed on the reference machine (2026-07-02):
uv 0.8.22, Python 3.12.3, ruff 0.14.13, mypy 1.19.1, bandit 1.9.2,
pre-commit 4.5.1. Newer versions of uv are fine. The ruff version must
match `uv.lock` (see traps).

## First-hour verification sequence

Run these in order after installing rows 1-3 above. Each step lists the
output shape that means success.

Step 1: clone and check uv.

```bash
git clone git@github.com:athola/claude-night-market.git
cd claude-night-market
uv --version
```

Expected: a single line like `uv 0.8.22`. Any 0.8+ version works. CI
pins `astral-sh/setup-uv@v8.2.0`.

Step 2: validate all plugin structures (also proves the venv syncs).

```bash
make validate-all
```

Expected: one block per plugin (26 directories) shaped like:

```text
>>> Validating plugins/abstract:
Plugin Validation Report: abstract
...
OK Plugin validation passed
```

Blue "Recommendations" lines are advisory and fine. A red failure line
or `(validation failed)` is not.

Step 3: run one fast plugin test suite.

```bash
make -C plugins/leyline test
```

Expected: verbose pytest output ending with a coverage table and a
summary like `710 passed, 6 warnings in 9.96s` (counts and timing
drift, but zero failures is the invariant). This proves `uv run`, pytest,
and per-plugin coverage thresholds all work.

Step 4: install the git hooks.

```bash
uv run pre-commit install
```

Expected: `pre-commit installed at .git/hooks/pre-commit`. From now on
commits run the full hook chain (file validation, bandit, ruff, mypy,
changed-plugin tests, structure validation). Never bypass it with
`--no-verify`; CONSTITUTION.md forbids that.

If any step fails, load night-market-debugging-playbook.

## Python version tiers

This is the number-one onboarding misconception. The README says
"Python 3.9+ for hooks", and newcomers read that as "the repo runs on
3.9". It does not. There are three tiers:

| Tier | Version | Enforced by | Why |
|------|---------|-------------|-----|
| Root tooling (pytest, ruff, mypy) | 3.12 | root `pyproject.toml` `requires-python = ">=3.12"`, ruff `target-version = "py312"`, mypy `python_version = "3.12"` | dev toolchain runs inside the uv venv |
| Plugin packages | varies, 3.9 to 3.12 | each `plugins/<name>/pyproject.toml` | plugins are independent deployables (ADR-0001) |
| Hook import chains | 3.9 | `.github/workflows/python39-compat.yml` | hooks run under the HOST system Python (macOS 3.9.6), outside any venv |

Per-plugin `requires-python` as of 2026-07-02 (22 of 26 plugin dirs
have a `pyproject.toml`):

- 3.12: abstract, conjure (also `<3.14`), imbue, leyline, minister,
  sanctum, scry
- 3.10: attune, conserve, hookify, memory-palace, parseltongue,
  pensive, scribe, spec-kit
- 3.9: archetypes, egregore, gauntlet, herald, oracle, phantom, tome

Why the hook tier exists: Claude Code executes hook scripts with
whatever interpreter the host provides, not the repo venv. A hook file
AND everything it transitively imports must therefore stay
3.9-compatible, even inside a plugin whose package requires 3.12. CI
enforces this with two gates in `python39-compat.yml`: gate 1 runs
`ruff check --select UP007 --target-version py39` on hook files (bare
`X | Y` union annotations), gate 2 builds a real 3.9 venv with
`uv venv --python 3.9` and runs hook tests with
`--override-ini="addopts="`.

Consequences you must respect in hook-reachable code:

- Use `timezone.utc`, never `datetime.UTC` (a 3.11+ alias). The root
  ruff config extend-ignores UP017 specifically so autofix does not
  reintroduce the alias. This break recurred three times before the
  ignore plus an AST guard test held the line.
- Guard third-party imports (`yaml`, `anthropic`) in hook entrypoints.
  The system interpreter has none of the repo's dependencies, and an
  unguarded import makes every git commit emit ModuleNotFoundError.

## Known traps

| Trap | Symptom | Fix or guard |
|------|---------|--------------|
| `setup-uv@v8` bare tag | CI fails: the bare `v8` tag does not exist upstream | pin exact tag `astral-sh/setup-uv@v8.2.0` (commit f81d89a5). Guard: `scripts/check_pinned_versions.py` |
| bandit 1.9+ under system 3.9 | pre-commit bandit hook env fails to install | `.pre-commit-config.yaml` pins `rev: 1.8.6`, the last release supporting 3.9 (commit 25bf5a9d). The project-venv bandit (1.9.x via `uv run`) is a different install and is fine |
| stale `.uv-tools` binary shadows ruff | bare `ruff` reports an old version (0.7.3 observed) and disagrees with CI | root Makefile sets `UV_TOOL_DIR ?= $(abspath .)/.uv-tools` and prepends `.uv-tools/ruff/bin` to PATH. Always lint via `make lint` or `uv run ruff`, never bare `ruff`. Guard: `scripts/check_ruff_version.py` compares `uv.lock` to PyPI |
| root pytest silently skips plugins | `uv run pytest` at the root collects only `tests/`, never plugin tests | root `pyproject.toml` sets `norecursedirs = ["plugins/*", ...]` on purpose (root `conftest.py` documents ImportPathMismatchError). Run `make -C plugins/<name> test` or `make <name>-test` |
| imbue coverage artifacts | every pytest run in `plugins/imbue` writes `htmlcov/`, `coverage.xml` | imbue's pytest `addopts` force `--cov=scripts` with term, html, and xml reports. Artifacts are gitignored. Expect them and never commit them |
| `make skrills-build` fails | `Error: skrills repo not found at $HOME/skrills` | `SKRILLS_REPO` defaults to `$(HOME)/skrills`. Set `SKRILLS_REPO=/path/to/skrills` or skip: `make validate-skills` falls back to a Python checker when no skrills binary exists |
| plugins run from a cache dir | plugin hook cannot find a file by relative path | installed plugins execute from the Claude Code cache dir, not the repo. Hooks must never use paths relative to the current working directory |

## When NOT to use

- Daily test, lint, release, and publish commands: use
  night-market-operations. This skill only bootstraps the machine.
- A previously working environment started failing: use
  night-market-debugging-playbook first to triage the symptom.
- Configuration axes, env vars, and their defaults beyond setup
  (`VOW_SHADOW_MODE`, quality gates): use night-market-config-catalog.
- Plugin, skill, and hook mechanics (how the pieces work rather than
  how to install the tools): use claude-code-plugin-reference.

## Exit Criteria

- [ ] `uv --version` prints a version at the repo root.
- [ ] `uv run ruff --version` prints the `uv.lock` version (0.14.13 as
      of 2026-07-02), not the `.uv-tools` version.
- [ ] `make validate-all` prints `Plugin validation passed` for every
      plugin and no `(validation failed)` lines.
- [ ] `make -C plugins/leyline test` ends with `N passed` and zero
      failures, plus a coverage table.
- [ ] `uv run pre-commit install` created `.git/hooks/pre-commit`.
- [ ] The reader can state why hook code is 3.9-constrained while root
      tooling requires 3.12 (hooks run under the host system Python).

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 (branch
discussions-fix-1.9.14). Observed tool versions and test counts in
this file are snapshots and will drift. Re-verify with:

- Root Python floor: `rg -n "requires-python" pyproject.toml`
- Per-plugin floors: `rg -n "requires-python" plugins/*/pyproject.toml`
- Locked ruff version: `rg -n -A1 'name = "ruff"$' uv.lock`
- setup-uv pin: `rg -n "setup-uv" .github/workflows/*.yml`
- bandit pin: `rg -n -B2 "id: bandit" .pre-commit-config.yaml`
- Makefile defaults: `rg -n "UV_TOOL_DIR|SKRILLS_REPO \?=" Makefile`
- Root pytest exclusion: `rg -n "norecursedirs" pyproject.toml`
- imbue coverage addopts: `rg -n -A8 "addopts" plugins/imbue/pyproject.toml`
- gemini-cli pin: `rg -n "gemini-cli" package.json`
- Leyline test count drift: `make -C plugins/leyline test`
