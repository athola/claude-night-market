---
name: night-market-config-catalog
description: Catalog every config axis, its defaults and guards. Use when adding or auditing configuration. Do not use for running gates; use night-market-operations.
---

# Night Market Config Catalog

Every configuration axis in this repo: where it lives, what the
options and defaults are, whether it is production policy or an
experimental opt-in, and what guards it. Flags drift, so every
axis ends with a one-line re-verification command. Run it before
trusting a value stated here.

Terms used once, defined once:

- **Axis**: one independently tunable configuration surface (a
  file, a key, or an environment variable).
- **Guard**: the mechanism that notices when the axis breaks or
  drifts (a test, a pre-commit hook, a CI job, or a script).
- **Shadow mode**: a hook that evaluates and warns but does not
  block. The blocking posture is opt-in.

## Axis table

| Surface | File | Key options and defaults | Status | Guarded by |
|---------|------|--------------------------|--------|------------|
| Quality gate thresholds | `.claude/quality_gates.json` | `enforce_blocking` true, `max_critical_issues` 3, `max_warnings_per_dimension` 5; per-dimension keys below | Production policy | Documented in `docs/quality-gates.md`; consumed as policy prose by sanctum PR workflows (see caveat below) |
| Context governance | `.claude/context_governance.json` | `enforce_strict_limits` false, `require_progressive_disclosure` true, `require_modular_structure` true, `require_optimization_level` "standard", `block_on_critical_violations` false, `max_violations_per_file` 5 | Production, advisory | `docs/quality-gates.md` |
| Repo Claude settings | `.claude/settings.json` | Contains only a `description` key. NO hooks registered at repo level; all active hooks ship from plugins | Production invariant | Convention; see night-market-architecture-contract |
| Behavioral rules | `.claude/rules/*.md` (8 files) | bounded-discovery, markdown-formatting, plan-before-large-dispatch, prefer-invariants-over-fallbacks, prefer-rg-over-grep, shared-utility-consumer-rule, skill-exit-criteria, slop-scan-for-docs | Production | slop CI, pre-commit, review practice |
| Python toolchain | root `pyproject.toml` | See "Root pyproject tool tables" below | Production | Pre-commit hooks, `typecheck.yml`, `security.yml` |
| Per-plugin coverage | `plugins/*/pyproject.toml` `[tool.nightmarket]` | `coverage_threshold = 90` in 19 plugins, 85 in gauntlet (20 files total) | Production | Read by `scripts/run-plugin-tests.sh` |
| Pre-commit pins | `.pre-commit-config.yaml` | Remote pins: pre-commit-hooks v6.0.0, bandit 1.8.6 (last release supporting the 3.9 system interpreter). Ruff runs from a local repo via the uv-managed binary so hook and `make format` share one version | Production | `scripts/check_pinned_versions.py`, `python39-compat.yml` |
| Plugin manifest trio | `plugins/<p>/.claude-plugin/plugin.json`, `.claude-plugin/metadata.json`, `openpackage.yml` | All three carry `version` in lockstep with the marketplace (1.9.15 at compile time) | Production | `plugins/sanctum/scripts/update_versions.py`, `plugins/abstract/scripts/validate_plugin.py` |
| Marketplace version | `.claude-plugin/marketplace.json` top-level `version` | Single ecosystem version, source of truth for the fan-out | Production | `update_versions.py <version>` bumper |
| MCP servers | `.mcp.json` | One stdio server: `markitdown` via `uvx markitdown-mcp` | Production | Manual |
| LSP config | `.cclsp.json` | `pylsp` for py/pyi; `typescript-language-server` for js/ts and markdown | Production | Manual |
| Feature-review scoring | `.feature-review.yaml` | `version: 1`; weight tables for value and cost; thresholds `high_priority` 2.8, `medium_priority` 1.8, `confidence_warning` 0.6 | Production | Consumed by imbue:feature-review |
| Egregore runtime config | `.egregore/config.json` (runtime file, created in the target repo, not committed here) | Nested dataclasses in `plugins/egregore/scripts/config.py`: overseer, alerts, pipeline, budget, discussions. `pipeline.completion_integrity = False` | Experimental opt-in flag inside production config | Unit tests in `plugins/egregore/tests/test_config.py` (default, roundtrip, and raw-JSON opt-in paths) |
| Conjure delegation | `~/.claude/hooks/delegation/config.json` (runtime file, per machine, not committed here) | Top-level `enabled` defaults to on when absent; only an explicit `false` opts out. `services` overrides per-provider `ServiceConfig` fields | Production, default-on | `plugins/conjure/tests/scripts/test_delegation_executor.py::TestDelegationIsOnUnlessRefused` |
| Herald Stop-hook judge | `plugins/herald/hooks/hooks.json` + env vars | Stop hook `double_shot_latte.py` registered with `timeout: 10`; internal `LLM_TIMEOUT_SECONDS = 8` | Hook production, LLM path experimental | Guard test asserts LLM timeout stays under the registered hook budget |

Caveat on the two `.claude/*.json` policy files: no Python
script in the repo reads them directly. They are policy inputs
referenced by `docs/quality-gates.md` and by sanctum command
prose (prepare-pr, pr-review configuration). Treat them as
contract documents for review workflows, not as runtime config
a daemon loads. Direct programmatic consumers: none found at
compile time (candidate: wire one before tightening values).

## Quality gate dimensions (.claude/quality_gates.json)

Per-dimension keys and defaults:

| Dimension | Keys | Blocks? |
|-----------|------|---------|
| performance | `max_file_size_kb` 20, `max_tokens_per_file` 5000, `max_function_lines` 60, `max_complexity_score` 12 | No (`block_on_violation` false) |
| security | `block_hardcoded_secrets` true, `block_insecure_functions` true, `require_input_validation` true | Yes (`block_on_violation` true) |
| maintainability | `max_technical_debt_ratio` 0.3, `max_nesting_depth` 5 | No |
| compliance | `require_plugin_structure` true, `require_proper_metadata` true | No |

Security is the only blocking dimension. Everything else is
advisory, capped globally by `max_critical_issues: 3`.

## Root pyproject tool tables

Root `pyproject.toml` (version 1.9.15, `requires-python >=3.12`)
carries these tables:

- `[tool.ruff]`: line-length 88, target-version py312.
- `[tool.ruff.lint]` select: E, W, F, I, B, C4, UP, PLC0415,
  PLR0913. extend-ignore: E501, B007, B008, B905, E402, and
  UP017. UP017 is load-bearing: it keeps `timezone.utc` instead
  of the 3.11+ `datetime.UTC` alias because hook scripts must
  import under the system Python 3.9. Removing it re-breaks
  hooks (this has happened three or more times, and an AST test
  now holds the line).
- `[tool.ruff.lint.per-file-ignores]`: tests get S-series and
  assert allowances; `**/__init__.py` gets F401; `**/hooks/*.py`
  gets BLE001, PLC0415, E402 (resilience lazy imports);
  `scripts/*.py` gets E402.
- `[tool.pytest.ini_options]`: `norecursedirs` includes
  `plugins/*`, so plugin tests MUST run per-plugin. Markers:
  unit, integration, e2e, slow, network, plugin, skill, hook,
  command, bdd, benchmark. `--strict-markers` is on.
- `[tool.coverage.report]`: `fail_under = 85` at root.
- `[tool.mypy]`: `python_version = "3.12"` with strict-leaning
  flags (`disallow_untyped_defs`, `warn_unused_ignores`, etc.).
- `[tool.uv.workspace]` members: plugins/abstract,
  plugins/leyline, plugins/conserve, plugins/core (a minimal set
  for linting, not all 26 plugin dirs).
- `[tool.bandit]` skips: B101, B103, B105, B108, B110, B112,
  B310, B311, B404, B603, B607, B608. Each skip has an inline
  rationale comment in the file. Keep that pattern when adding
  one.

## Manifest trio and the two semver namespaces

Each plugin ships three manifests that must stay in sync:

- `.claude-plugin/plugin.json`: name, version, component arrays.
- `.claude-plugin/metadata.json`: version, dependencies,
  provides, claude integration block.
- `openpackage.yml`: cross-framework manifest (name, version,
  description, keywords).

Two distinct semver namespaces appear in `metadata.json` and are
easy to confuse:

1. The ecosystem version (`"version": "1.9.15"`), bumped in
   lockstep from `marketplace.json` by
   `plugins/sanctum/scripts/update_versions.py <version>`.
2. Capability dependency ranges, for example imbue declares
   `"dependencies": {"abstract": ">=2.0.0"}`. That `2.0.0` is a
   capability-contract version, NOT the marketplace version.
   Do not "fix" it to 1.9.x during a bump.

## Environment variables

| Variable | Consumer | Values and default | Effect | Status |
|----------|----------|--------------------|--------|--------|
| `VOW_SHADOW_MODE` | imbue hooks via `plugins/imbue/hooks/shared/vow_utils.py` | Default `"1"` (shadow). Set `0` to block | Vow hooks (bounded reads, scope ramp, package hallucination, no-AI-attribution, no-emoji-commits) warn instead of blocking | Shadow default is production; blocking posture experimental |
| `UV_TOOL_DIR` | root `Makefile` (line 9) | Default `./.uv-tools` | Where uv installs tools; ruff resolves from `$(UV_TOOL_DIR)/ruff/bin` first on PATH | Production |
| `SKRILLS_REPO` | root `Makefile` (`skrills-build`) | Default `$HOME/skrills` | Source checkout used to cargo-build the skrills binary | Production (skrills itself optional; Python fallbacks exist) |
| `CONSERVATION_MODE` | `plugins/conserve/hooks/session-start.sh` | `quick`, `deep`, `normal`; default `normal`; unknown values warn and fall back to `normal` | How much conservation guidance loads at session start | Production |
| `DOUBLE_SHOT_LATTE_LLM` | `plugins/herald/hooks/double_shot_latte.py` | Set `"1"` to enable | Enables the LLM "second shot" tiebreaker, only on the single ambiguous Stop-hook outcome | Experimental opt-in, default off |
| `DOUBLE_SHOT_LATTE_MODEL` | same hook | Default `"haiku"` | Model used for the second shot | Experimental |
| `DOUBLE_SHOT_LATTE_MAX_CONTINUATIONS` | same hook | Integer (read from env; see hook source for cap semantics) | Caps forced continuations | Production guard |
| `CLAUDE_HOOK_JUDGE_MODE` | same hook | `"true"` disables the LLM path | Prevents the judge from invoking itself recursively | Production guard |
| `CONJURE_DELEGATION` | `plugins/conjure/scripts/delegation_executor.py` | `off`/`0`/`false`/`no` and their opposites, any case; unset means on | Declines delegation for one run. A disabled delegator probes and spawns nothing, and returns `fallback_reason="delegation_disabled"`. Overrides the config file in both directions | Production, opt-out |

## Experimental and opt-in flags

Both current experiments follow the same pattern: default off,
guard tests, blocking behavior only on explicit opt-in.

### egregore completion_integrity

- Key: `pipeline.completion_integrity`, a bool defaulting to
  `False` in the `PipelineConfig` dataclass at
  `plugins/egregore/scripts/config.py` (line 49 at compile
  time).
- Stored in the target repo's `.egregore/config.json`, read by
  the summon skill alongside `.egregore/manifest.json`.
- When `True`: a quality verdict of "fix-required" becomes a
  step failure (cannot advance to ship) and merge is held for
  human review regardless of `auto_merge`.
- Guards: `plugins/egregore/tests/test_config.py` covers the
  False default, the opt-in roundtrip, and loading from a
  hand-written raw JSON file.

### herald LLM second shot

- The Stop hook itself is production (registered in
  `plugins/herald/hooks/hooks.json` with `timeout: 10`).
- The LLM tiebreaker is gated three ways: `DOUBLE_SHOT_LATTE_LLM`
  must be `"1"`, judge mode must not be active, and the turn
  must land on the single ambiguous outcome (every confident
  verdict skips the LLM entirely).
- `LLM_TIMEOUT_SECONDS = 8` is deliberately under the 10-second
  registered budget. A value above the budget once made the harness
  kill the hook before any verdict (full record:
  night-market-failure-archaeology SB7). A guard test now asserts
  the ordering. Never raise the LLM timeout without checking the
  registered budget first.

## Adding a config axis

Checklist for any new flag, threshold, or env var:

- [ ] Default preserves current behavior (default off, or the
      value the system already exhibits).
- [ ] A guard test asserts the default AND the opt-in path,
      including loading from raw serialized config
      (model: `plugins/egregore/tests/test_config.py`).
- [ ] Env vars validate their input and fall back to the default
      on unknown values with a warning
      (model: `plugins/conserve/hooks/session-start.sh`).
- [ ] Any timeout inside a hook is asserted against the hook's
      registered budget in `hooks.json`.
- [ ] Add a row to the axis or env var table in this file, with
      status (production or experimental) and guard.
- [ ] Add a one-line re-verification command under Provenance.
- [ ] If the axis affects gating or review policy, update
      `docs/quality-gates.md` and route the change through
      night-market-change-control.

## When NOT to use

- Running tests, lint, gates, or releases: use
  night-market-operations.
- Deciding whether a config change is allowed at all, or how to
  review it: use night-market-change-control.
- Plugin/skill/hook mechanics (what `hooks.json` fields mean,
  how manifests load): use claude-code-plugin-reference.
- Recreating the toolchain (uv, Python versions, skrills): use
  night-market-build-and-env.
- Diagnosing a broken gate or hook: use
  night-market-debugging-playbook.

## Exit Criteria

- [ ] Every re-verification command under Provenance exits 0 and
      its output matches the value stated in this catalog.
- [ ] `jq -r '.version' .claude-plugin/marketplace.json` equals
      the `version` in each plugin's plugin.json, metadata.json,
      and openpackage.yml (spot-check at least one plugin).
- [ ] `rg -l "coverage_threshold" plugins/*/pyproject.toml | wc -l`
      returns 20. Any other count means this catalog is stale
      and must be updated before use.
- [ ] `rg -n "completion_integrity: bool = False" plugins/egregore/scripts/config.py`
      matches. If the default changed, the Experimental section
      here is wrong and must be rewritten.
- [ ] A new config axis added by the current change appears in
      the axis or env var table with a guard and a
      re-verification one-liner.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 (branch
discussions-fix-1.9.14). Line numbers and counts are volatile;
re-verify before quoting.

Re-verification one-liners per axis:

```bash
# Quality gates and context governance
jq . .claude/quality_gates.json
jq . .claude/context_governance.json

# Repo settings must stay hook-free
jq 'keys' .claude/settings.json   # expect ["description"]

# Behavioral rules roster
ls -1 .claude/rules/

# Root toolchain tables
rg -n "fail_under|extend-ignore|^select|target-version" pyproject.toml
rg -n "\[tool.bandit\]" -A 20 pyproject.toml
rg -n "\[tool.uv.workspace\]" -A 8 pyproject.toml

# Per-plugin coverage thresholds
rg -n "coverage_threshold" plugins/*/pyproject.toml

# Pre-commit pins
rg -n "rev:" .pre-commit-config.yaml

# Marketplace version and manifest fan-out (imbue as sample)
jq -r '.version' .claude-plugin/marketplace.json
jq -r '.version' plugins/imbue/.claude-plugin/plugin.json
jq -r '.version, .dependencies' plugins/imbue/.claude-plugin/metadata.json
head -3 plugins/imbue/openpackage.yml

# Root dotfiles
jq . .mcp.json
jq '.servers[].command' .cclsp.json
rg -n "high_priority|medium_priority|confidence_warning" .feature-review.yaml

# Env vars
rg -n "VOW_SHADOW_MODE" plugins/imbue/hooks/shared/vow_utils.py
rg -n "UV_TOOL_DIR|SKRILLS_REPO" Makefile
rg -n "CONSERVATION_MODE" plugins/conserve/hooks/session-start.sh

# Experimental flags
rg -n "completion_integrity" plugins/egregore/scripts/config.py
rg -n "DOUBLE_SHOT_LATTE|LLM_TIMEOUT_SECONDS|JUDGE_MODE" plugins/herald/hooks/double_shot_latte.py
jq . plugins/herald/hooks/hooks.json
```

Known drift risks: pre-commit `rev:` pins (guarded by
`scripts/check_pinned_versions.py`), the coverage-threshold file
count (20 at compile time), the egregore config.py line number,
and the promotion status of the two experimental flags (see
night-market-completion-integrity-campaign for the promotion
question).
