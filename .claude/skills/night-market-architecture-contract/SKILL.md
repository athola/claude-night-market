---
name: night-market-architecture-contract
description: States load-bearing decisions, invariants, and weak points. Use when judging a design change. Do not use for gating; use night-market-change-control.
---

# Night Market Architecture Contract

This skill records the design decisions that hold claude-night-market
together, the invariants that enforcement code keeps true, and the weak
points that are known and accepted. Read it before proposing a change
that crosses a plugin boundary, touches a hook, adds a skill, or bumps
a version. Every claim cites in-repo evidence: an ADR (Architecture
Decision Record, in `docs/adr/`), a commit hash, or a checked-in
enforcement file. Verify a citation before relying on it:

```bash
git log --oneline -1 <hash>
rg -n "Status" docs/adr/<file>.md
```

## Load-bearing decisions

### 1. Plugins are self-contained deployables

Each of the 23 plugins under `plugins/` must install and run alone.
There is no shared registry and no root-level shared library that
plugins import at runtime (ADR-0001, Accepted). Plugins detect each
other at runtime via filesystem checks and must degrade gracefully when
a sibling is absent.

Cross-plugin DRY is an anti-pattern here, and that is settled by
experiment, not taste. Commit `054e2679` consolidated 1164 lines of
duplicated `tasks_manager.py` from attune, sanctum, and spec-kit into a
shared root script. It broke plugin self-containment and was reverted
in `29961cd2`. The durable fix, `d89a55c7`, made the copies
per-plugin and intentionally different. `docs/dependency-audit.md`
records the per-plugin copies as the approved state. Do not re-propose
the consolidation.

Practical test before you extract shared code: if a user installs only
one plugin from the marketplace, does your change still work? If not,
duplicate the code into each plugin instead.

### 2. Hooks run under host Python from a cache directory

Claude Code copies an installed plugin into a cache directory and runs
its hooks under the host system Python, which can be as old as 3.9.
The repo itself is Python 3.12 (root `pyproject.toml`,
`requires-python >= 3.12`). Only hook scripts and their transitive
import chains carry the 3.9 constraint. Five contract rules follow,
each purchased with an outage:

| Rule | Why (evidence) |
|------|----------------|
| Hook code and every transitive import must be Python 3.9 compatible | `datetime.UTC` (a 3.11+ alias) broke the whole hook import chain repeatedly. ruff kept auto-reverting the fix until `UP017` was globally ignored (`pyproject.toml` line 165) and an AST scan test held the line (`plugins/leyline/tests/test_python39_compat.py`) |
| Read the hook payload as JSON on stdin, never from `CLAUDE_TOOL_*` env vars | Claude Code does not set those env vars, so env-reading hooks were silent no-ops for months (full record: night-market-failure-archaeology SB9). Canonical reader: `read_hook_payload()` in `plugins/abstract/hooks/shared/hook_io.py` |
| No relative paths in hooks | The cache directory is not the repo checkout. conserve's session-start hook broke on a relative path and now inlines its JSON utilities (CHANGELOG) |
| Hook entrypoints must import safely under a bare interpreter | An eager `import yaml` in gauntlet made every git commit emit `ModuleNotFoundError`. Guarded in `45dd77ef` (#518), `anthropic` deferred in `9bfc0a7a` |
| Subprocess timeouts must sit below the budget registered in `hooks.json` | herald's LLM call once outlived its registered Stop-hook budget, so the harness killed the hook with no verdict at all (full record: night-market-failure-archaeology SB7). Guard test: `plugins/herald/tests/unit/test_double_shot_latte.py` |

CI enforcement: `.github/workflows/python39-compat.yml` runs two
gates with uneven coverage. Gate 1 (ruff `UP007`, flags 3.10+ union
syntax) covers 12 plugins' `hooks/` dirs. Gate 2 (hook test suites
inside a real Python 3.9 venv) covers only 7 plugins: abstract,
conserve, egregore, imbue, leyline, memory-palace, sanctum. herald
ships a Stop hook yet appears in neither gate.

### 3. One ecosystem version, fanned out to every manifest

`.claude-plugin/marketplace.json` is the version source of truth
(1.9.15 as of 2026-07-02). Each plugin carries three manifests that
must stay in sync with it and with each other:

- `.claude-plugin/plugin.json` (name, version, component arrays)
- `.claude-plugin/metadata.json` (version plus dependency hints)
- `openpackage.yml` (cross-framework manifest)

Plus `pyproject.toml` and any `__init__.py` carrying `__version__`.
Never hand-edit versions across files. Use the bumper, which finds and
rewrites all of them:

```bash
uv run python plugins/sanctum/scripts/update_versions.py <version>
```

One trap: `metadata.json` `dependencies` (for example imbue declaring
`"abstract": ">=2.0.0"`) is a separate semver namespace for capability
compatibility. It does not track the marketplace version and a `2.0.0`
there does not mean marketplace 2.0.0 exists.

### 4. Skill discovery budget is finite and overflow is silent

Claude Code loads every installed skill's description into context at
2% of the context window, with a 16,000-character fallback (ADR-0004,
Accepted, updated 2026-05-21). Descriptions that exceed the budget make
skills invisible with no error anywhere. That is why:

- Each description is capped at 160 characters
  (`docs/skill-description-guide.md`), enforced by the
  `validate-description-budget` pre-commit hook backed by
  `plugins/abstract/scripts/validate_budget.py`.
- The ecosystem-wide validator ceiling is 90,000 characters
  (`DEFAULT_BUDGET` in `plugins/abstract/scripts/validate_budget.py`,
  overridable via `SLASH_COMMAND_TOOL_CHAR_BUDGET`). ADR-0004 and
  `docs/skill-description-guide.md` still cite a stale 60,000 figure;
  the script is the enforcer. Flag the ADR for an update through
  change control.

When adding a skill, spend the 160 characters on trigger phrases, not
on restating the name.

### 5. Collective memory and trust are external services

Decisions, learnings, and audit syntheses are posted to GitHub
Discussions, which act as agent collective memory across sessions
(ADR-0007, Accepted). There is no `gh discussion` subcommand: all
Discussions access goes through `gh api graphql`. Release trust is
established by SLSA attestation (Supply-chain Levels for Software
Artifacts) of `trust-report.json` on master pushes
(`.github/workflows/trust-attestation.yml`). The original blockchain
design (ERC-8004) was dropped for cost. ADR-0008 is marked Superseded
2026-03-15 and now points at GitHub Attestations. See
night-market-collective-memory for the Discussions workflow.

### 6. Every skill has one of three roles

`docs/skill-integration-guide.md` defines the role taxonomy used when
judging whether a skill is an orphan or a hub:

| Role | Inbound refs | Invoked directly | Example |
|------|--------------|------------------|---------|
| `entrypoint` | low (0-3) | yes | `sanctum:do-issue` |
| `library` | high (4+) | rarely | `imbue:proof-of-work` |
| `hook-target` | varies | no | `imbue:vow-enforcement` |

A skill with zero inbound `Skill()` references is only a problem if it
also has no command path and no hook that loads it. Check the role
before archiving anything.

## Invariants

Each row names the enforcement that keeps the invariant true. If you
weaken the enforcement, you own the failure mode in the third column.

| Invariant | Enforced by | What breaks if violated |
|-----------|-------------|-------------------------|
| Hook import chains are Python 3.9 safe | `.github/workflows/python39-compat.yml` (2 gates) plus AST scan test `plugins/leyline/tests/test_python39_compat.py` | Total hook outage: one 3.11-only import kills every hook that transitively loads the module |
| No bare `except:` and errors propagate by default | ruff `E` ruleset (root `pyproject.toml`) plus CONSTITUTION.md rule 10 | Scanners silently drop files and report success on garbage input, and failures become invisible |
| All manifests carry the same ecosystem version | `plugins/sanctum/scripts/update_versions.py` rewrites pyproject/plugin.json/metadata.json/openpackage.yml/`__init__.py` in one pass | Version drift across ~100 files, and marketplace.json stops being the source of truth |
| `book/src/reference/capabilities-reference.md` matches plugin registrations | `scripts/capabilities-sync-check.sh` via `make docs-sync-check` and `.github/workflows/capabilities-sync.yml` | Published docs advertise components that do not exist, or hide ones that do |
| No new dangling `Skill(plugin:name)` references | `scripts/check_skill_graph_drift.py` ratchet against `scripts/skill_graph_baseline.json` | A model tries to load the referenced skill and silently gets nothing |
| Every SKILL.md has an `## Exit Criteria` section | `scripts/check_skill_exit_criteria_drift.py` ratchet against `scripts/skill_exit_criteria_baseline.json` | Skills the model cannot tell when to stop executing (vague success criteria at scale) |
| Hook subprocess timeout < registered hook budget | Guard test in `plugins/herald/tests/unit/test_double_shot_latte.py` asserts `LLM_TIMEOUT_SECONDS` fits inside the `hooks.json` timeout | Harness kills the hook mid-flight and no verdict is emitted at all |
| Hook payloads are read stdin-first | `plugins/abstract/hooks/shared/hook_io.py` `read_hook_payload()` shared by hook scripts | Hooks become silent no-ops (this happened, and the only symptom was a starved learning digest) |

The two ratchet scripts share one mechanic: they fail a commit only
when the violation count rises above the committed baseline, and they
ask you to lower the baseline when the count drops. Never raise a
baseline to get a commit through. That is routing around change
control. One documented exception: a brand-new library skill
legitimately starts uncalled, and `scripts/check_skill_graph_drift.py`
(plus the `_comment` in `scripts/skill_graph_baseline.json`) instructs
you to raise `max_uncalled_libraries` to record the 30-day consumer
grace period that `.claude/rules/shared-utility-consumer-rule.md`
grants. See night-market-change-control.

## Known weak points

Stated plainly so nobody rediscovers them the hard way. These are open
by decision or by neglect, not secrets.

1. Skill-discovery overflow is silent. If total description overhead
   exceeds the context budget, skills vanish with no error (ADR-0004).
   The 160-char cap and validator ceiling are preventive guards. There
   is no runtime detection of overflow.

2. The quality-gate federation has one real orchestrator. The gate
   skills (karpathy-principles, scope-guard, proof-of-work, justify,
   rigorous-reasoning, vow-enforcement) are designed to compose, but
   only `egregore:quality-gate` sequences the full pipeline today
   (`docs/quality-gates.md`, "Who currently orchestrates"). Every
   other consumer picks gates ad hoc.

3. `docs/project-brief.md`, `docs/specification.md`, and
   `docs/implementation-plan.md` are overwritten each feature cycle.
   The current contents describe only the latest cycle (insight-palace
   bridge as of 2026-07-02). Past cycles survive only in git history.
   Do not cite these files as a permanent record.

4. Duplicate module names across plugins force per-plugin mypy.
   Running `mypy plugins/` from the root collides on duplicate module
   names (comment in `.github/workflows/typecheck.yml`). The same
   constraint makes root pytest exclude `plugins/*`
   (`norecursedirs` in root `pyproject.toml`, and root `conftest.py`
   documents the `ImportPathMismatchError`). Always run plugin tests
   and typechecks per plugin.

5. mdbook is unpinned in the deploy workflow.
   `.github/workflows/deploy-book.yml` installs `mdbook-version:
   'latest'`, so an upstream mdbook release can break the book deploy
   with no repo change. Candidate fix: pin a version. Not done as of
   2026-07-02.

## ADR digest

All 17 records live in `docs/adr/`. Statuses read from the files on
2026-07-02.

| ADR | Title | Status | One-line takeaway |
|-----|-------|--------|-------------------|
| 0001 | Plugin Dependency Isolation | Accepted | No shared registry. Runtime filesystem detection with graceful degradation |
| 0002 | Extract QuotaTracker to Leyline | Accepted | Quota tracking moved from conjure into leyline for reuse |
| 0003 | Command Description Refactoring | Accepted | Two-part descriptions: short display line, rich identification text |
| 0004 | Skill Description Budget Optimization | Accepted (updated 2026-05-21) | 160-char cap. Budget is 2% of context, 16k fallback. Its 60k validator ceiling is stale: the enforcing script uses 90k |
| 0005 | Attune Plugin Discoverability Enhancement | Accepted (2026-02-05) | Superpowers-style trigger phrasing for attune components |
| 0006 | Self-Adapting Skill Health | Accepted (2026-02-15) | Homeostatic monitoring detects degrading skills |
| 0007 | GitHub Discussions as Agent Collective Memory | Accepted (2026-02-19) | Decisions and learnings posted to Discussions (GraphQL only) |
| 0008 | Behavioral Contract Verification Framework | Superseded (2026-03-15) | ERC-8004 blockchain dropped for cost. GitHub Attestations (SLSA) instead |
| 0009 | Sidecar Service Discovery via Port Files | Accepted | Sidecar daemons publish their ports through port files |
| 0010 | Stacked Diff Workflows | Accepted | `git --update-refs` plus `gh pr create --base` as zero-dependency stacking |
| 0011 | Shared Session-Capture Envelope | Accepted | One JSON envelope shape for friction and trace payloads, separate files |
| 0012 | Confidence-Tagged Agent Claims | Superseded by 0017 | VERIFIED/INFERRED/ASSUMPTION tags: no enforcement built |
| 0013 | Operationalizing Naur Theory-Building | Superseded by 0017 | Theory-building rituals: folded into 0017's lighter form |
| 0014 | Pensive Review-Skill Consolidation | Accepted (sequencing only) | 9 review skills, 5 sharing a verdict scaffold. Consolidation sequenced, not done |
| 0015 | Over-Built Orchestrator Skill Simplification | Accepted (data-collection phase) | Collect 30 days of usage data before simplifying over-built skills |
| 0016 | Wire-or-Archive for Three Orphan Skills | Accepted (decisions recorded) | Orphans judged on demand signal, wiring cost, and reference value |
| 0017 | Decisions on Confidence-Tagging and Theory-Building | Accepted (2026-06-18) | No enforcement mechanisms and voluntary use. Supersedes 0012 and 0013 |

## When NOT to use

| You actually need | Use instead |
|-------------------|-------------|
| How a change is classified, gated, and reviewed | night-market-change-control |
| The full story of a past incident or revert | night-market-failure-archaeology |
| Commands to run tests, lint, release, publish | night-market-operations |
| Every config file, default, and env var | night-market-config-catalog |
| Plugin/skill/hook mechanics in the abstract | claude-code-plugin-reference |
| Triage for a live failure | night-market-debugging-playbook |

## Exit Criteria

- [ ] You can state why cross-plugin shared code is rejected, citing
      ADR-0001 and commits `054e2679` and `29961cd2`, and both
      commits resolve via `git log --oneline -1 <hash>`.
- [ ] Every enforcement file named in the Invariants table exists:
      `ls` each path in the second column from the repo root with
      zero errors.
- [ ] The ADR digest row count matches
      `ls docs/adr/*.md | wc -l` (17 as of 2026-07-02).
- [ ] For a proposed change, you can name which invariant row (if
      any) it touches and which weak point (if any) it worsens,
      before writing code.
- [ ] The version printed by
      `rg -m1 '"version"' .claude-plugin/marketplace.json` matches
      the version in every plugin's `plugin.json` you spot-check.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 on branch
discussions-fix-1.9.14. Skill/plugin counts drift: 198 SKILL.md files
under `plugins/` and 23 marketplace plugins at compile time.

Re-verify volatile facts:

```bash
# ADR count and statuses
rg -m1 -n "Status" docs/adr/*.md

# Ecosystem version source of truth
rg -m1 '"version"' .claude-plugin/marketplace.json

# Discovery budget numbers (2%, 16k fallback; the ADR still says 60k)
rg -n "16,000|60,000" docs/adr/0004-skill-description-budget-optimization.md

# Enforced validator ceiling (90,000 as of 2026-07-03)
rg -n "DEFAULT_BUDGET" plugins/abstract/scripts/validate_budget.py

# Who orchestrates the gate federation today
rg -n "orchestrat" docs/quality-gates.md

# mdbook still unpinned?
rg -n "mdbook-version" .github/workflows/deploy-book.yml

# Ratchet baselines still present
ls scripts/skill_graph_baseline.json scripts/skill_exit_criteria_baseline.json

# Plugin and skill counts
python3 -c "import json;print(len(json.load(open('.claude-plugin/marketplace.json'))['plugins']))"
find plugins -name SKILL.md | wc -l
```
