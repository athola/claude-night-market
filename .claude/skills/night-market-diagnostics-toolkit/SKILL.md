---
name: night-market-diagnostics-toolkit
description: Run and interpret repo diagnostic scripts (ratchets, validators, token stats). Use when measuring health. Do not use to run tests; use night-market-operations.
---

# Night Market Diagnostics Toolkit

Measure instead of eyeballing. Every claim about the health of this
repo ("the skill graph is clean", "descriptions fit the budget",
"no compromised dependencies") has a script that produces a number
or a PASS/FAIL. This skill catalogs those scripts, their exact
invocations, and how to read their output.

Conventions for everything below:

- Run all commands from the repo root
  (`/home/alext/claude-night-market`).
- Plain `python3` is enough for every script in the table except
  mutation testing, which needs `uv`.
- All checks here are read-only. None of them mutate the repo.

## The ratchet-baseline concept

Several checks are ratchets. A ratchet check counts a category of
existing debt (for example, SKILL.md files missing an Exit Criteria
section), compares the live count against a frozen number in a
baseline JSON file, and:

- passes while the live count is at or below the baseline
  (pre-existing debt is tolerated),
- fails the moment a NEW violation pushes the count above the
  baseline (debt may not grow),
- nudges you to lower the baseline number when the live count drops
  (locking in the win so the debt cannot silently return).

The goal is a baseline that only shrinks, eventually to zero. The
two ratchet baselines live at `scripts/skill_graph_baseline.json`
(keys `max_dangling_bugs`, `max_uncalled_libraries`) and
`scripts/skill_exit_criteria_baseline.json`
(key `max_missing_exit_criteria`). When a ratchet prints a
"dropped to N (baseline M). Lower ... to lock the win." line, edit
the baseline JSON down to N in the same PR.

## Tool table

Jargon used in the table: "dangling Skill() ref" means a
`Skill(plugin:name)` reference in a skill/command/agent file whose
target skill does not exist. "Uncalled library" means a
library-role skill no other skill invokes (the risk targeted by
`.claude/rules/shared-utility-consumer-rule.md`).

| Tool | Invocation | What it measures | How to interpret | When to run |
|------|------------|------------------|------------------|-------------|
| Plugin structure validator | `python3 plugins/abstract/scripts/validate_plugin.py plugins/<name>` | plugin.json validity, kebab-case naming, directory layout | Exit 0 with "Plugin validation passed". Any FAIL line names the broken file | Before committing plugin changes. `make validate-all` loops it over every plugin |
| Skill-graph drift ratchet | `python3 scripts/check_skill_graph_drift.py` | Dangling Skill() refs and uncalled libraries vs `skill_graph_baseline.json` | Exit 0 at/below baseline. Nonzero exit lists the new dangling refs. "Lower ... to lock the win" means shrink the baseline | After adding, renaming, or deleting skills or Skill() refs |
| Exit-criteria drift ratchet | `python3 scripts/check_skill_exit_criteria_drift.py` | SKILL.md files under plugins/ missing an `## Exit Criteria` heading vs `skill_exit_criteria_baseline.json` | Same ratchet semantics as above | After adding or editing any SKILL.md |
| Pinned-version checker | `python3 scripts/check_pinned_versions.py` | GitHub-sourced tool pins vs the latest upstream release (needs network) | "N pin(s) current" is healthy. A "holding X at ..." line documents an intentional hold with its reason (for example bandit 1.8.6 for the Python 3.9 hook floor) | In pre-commit, and whenever a CI tool-setup step breaks |
| Capabilities sync | `bash scripts/capabilities-sync-check.sh` | plugin.json registrations vs the generated capabilities reference in book/src/ | "PASSED: All capabilities are in sync" plus counts. On drift, run `/sanctum:sync-capabilities --fix` | After changing any skill, command, or agent registration |
| Supply-chain scan | `python3 scripts/supply_chain_scan.py` | Lockfiles vs the known-compromised-versions blocklist, plus known malicious artifacts | Two `[OK]` lines is clean. Any hit must be resolved before release | When adding dependencies, during incidents, before releases |
| Token stats | `python3 plugins/abstract/scripts/context_optimizer.py stats plugins/ --format json` | Bytes and estimated tokens per SKILL.md, bucketed small/medium/large | Skills over ~5,000 estimated tokens breach the quality-gates file limit and are split candidates | When a skill feels bloated, before modularizing |
| Description budget | `python3 plugins/abstract/scripts/validate_budget.py` | Sum of all skill/command description characters vs the 90,000-char ecosystem ceiling (ADR-0004, 160 chars per description) | Prints used/ceiling and headroom. Exit 0 means within budget | After editing any frontmatter description |
| skrills validate | `skrills validate --skill-dir plugins --target claude` | Skill frontmatter validity per target framework (Claude, Codex, Copilot) | "Validated N skills: ..." then an `Errors (n):` list with file:line. Fix every listed error | Skill audits. `make validate-skills` falls back to `uv run python scripts/check_plugin_hooks.py` when skrills is absent |
| skrills analyze | `skrills analyze --skill-dir plugins` | Skill token usage and dependency structure | Large-token outliers are split candidates | Budget planning. `make analyze-skills` falls back to `scripts/generate_dependency_map.py` |
| Mutation testing | `cd plugins/<name> && uv run mutmut run --paths-to-mutate=scripts/,src/ --tests-dir=tests/` | Whether the test suite kills injected code mutations (surviving mutants = untested behavior) | Exit 0 = no survivors. Exit 2 = survivors found (CI treats this as pass-with-report). Any other exit = crash, investigate | Weekly CI (Sunday) or manually before hardening a test suite |
| Markdown link checker | `python3 scripts/check-markdown-links.py [file.md ...]` | Broken relative links and anchors. No args = scan the whole repo | Exit 1 prints each broken link as `file: link` | After moving or renaming docs or skills |
| Lint-suppression guard | `python3 scripts/check_noqa.py <files...>` | Inline lint/type suppressions that lack a stated reason | "BLOCKED" plus a hit list. Fix the issue, or append a reason after the suppression marker | Pre-commit runs it on changed files |
| Docstring quality | `python3 scripts/check_docstring_quality.py <files.py...>` | Docstrings that merely restate the function name | Each hit says "delete it or add information". Do exactly that | Pre-commit runs it on changed Python files |
| JSON-utils drift | `bash scripts/shared/check-json-utils-drift.sh` | Vendored JSON helper copies in plugin hooks vs the canonical `scripts/shared/json_utils.sh` | "OK: all vendored JSON utilities match canonical." Anything else names the drifted copy | After editing json_utils.sh or any inlined copy |
| Export stats | `python3 scripts/clawhub_export.py --stats` | Skill counts per plugin and top-20 membership for cross-framework export | Totals line plus a per-plugin table | Before cross-framework publishing |
| Framework detect | `python3 scripts/framework_detect.py [--json]` | Which agent-framework capabilities the current directory exposes (skills, agents, hooks, commands, mcp, a2a) | `[+]`/`[-]` capability checklist | When debugging cross-framework export targets |

### Interpretation notes

- **context_optimizer stats prints nothing in the default text
  format.** This is a verified quirk: `stats` on a directory with
  no `--format` flag produces empty output and exit 0. Always pass
  `--format json` (clean JSON) rather than `--format table`, which
  dumps a raw Python dict.
- **Ratchet failures name the new violations.** A ratchet that
  fails after your change means your change added debt. Fix the
  new ref or add the missing section. Never raise a baseline number
  to make a check pass, with one documented exception: a brand-new
  library skill legitimately starts uncalled, and
  `scripts/check_skill_graph_drift.py` itself (plus the `_comment`
  in `scripts/skill_graph_baseline.json`) instructs you to raise
  `max_uncalled_libraries` to record the 30-day consumer grace
  period that `.claude/rules/shared-utility-consumer-rule.md`
  grants (the rule grants the grace period; the script defines the
  baseline mechanics). night-market-architecture-contract records
  the same exception in its ratchet invariants.
- **Mutation exit codes are the contract.** CI
  (`.github/workflows/mutation-testing.yml`) treats exit 0 and
  exit 2 as success and posts survivors to the step summary. Only
  exits other than 0 and 2 fail the workflow. So a green mutation
  run does NOT mean zero survivors. Read the report.
- **check_pinned_versions needs network access.** It queries GitHub
  for latest releases. Offline, expect failures that are
  environmental, not real findings.

## Health snapshot in one command

`scripts/health-snapshot.sh` (in this skill directory) runs the six
cheap checks and prints a PASS/FAIL table. It is read-only,
needs only bash and python3, requires no network, and completes in
about 6 seconds (measured 2026-07-02).

```bash
bash .claude/skills/night-market-diagnostics-toolkit/scripts/health-snapshot.sh
```

It runs: plugin structure validation (all plugins), capabilities
sync, supply-chain scan, both drift ratchets, and the description
budget. Exit 0 means all six passed. Exit 1 means at least one
failed, and the failing check's full output is printed to stderr
above the table. Run it at session start, before a PR, and after
any bulk skill edit.

## Blocking vs advisory

Which failures stop a merge and which are signals:

| Check | Gate | Effect on failure |
|-------|------|-------------------|
| validate_plugin.py | pre-commit (19 hook entries) | Blocks commit |
| Skill-graph drift ratchet | pre-commit | Blocks commit |
| Exit-criteria drift ratchet | pre-commit | Blocks commit |
| check_noqa.py | pre-commit | Blocks commit |
| check_docstring_quality.py | pre-commit | Blocks commit |
| check-markdown-links.py | pre-commit | Blocks commit |
| validate_budget.py | pre-commit | Blocks commit |
| check-json-utils-drift.sh | pre-commit | Blocks commit |
| check_pinned_versions.py | pre-commit | Blocks commit |
| capabilities-sync-check.sh | pre-commit and CI (capabilities-sync.yml) | Blocks commit and PR |
| Mutation testing | CI (weekly and manual dispatch) | Advisory: survivors reported, workflow stays green |
| supply_chain_scan.py | manual / `make supply-chain-scan` (not wired to CI) | Advisory day-to-day, treat as blocking before any release |
| context_optimizer, skrills analyze, clawhub stats, framework_detect | manual | Advisory: measurement only |

The dimension-level policy lives in `.claude/quality_gates.json`:
`enforce_blocking` is true with `max_critical_issues: 3`, and only
the `security` dimension sets `block_on_violation: true`. The
`performance` (20KB / 5,000-token file limits, 60-line functions,
complexity under 12), `maintainability` (debt ratio under 0.3,
nesting under 5), and `compliance` dimensions are advisory
(`block_on_violation: false`). So: security findings block,
size/complexity findings warn.

## When NOT to use

- Running the test suite, lint, typecheck, or a release:
  use night-market-operations (command anatomy and artifacts).
- You already have a failure and need symptom-to-cause triage:
  use night-market-debugging-playbook.
- You need the meaning and default of a config knob rather than a
  measurement: use night-market-config-catalog.
- You are deciding whether evidence is sufficient to claim work
  complete: use night-market-validation-and-qa.

## Exit Criteria

- [ ] `bash .claude/skills/night-market-diagnostics-toolkit/scripts/health-snapshot.sh`
      runs from the repo root, prints a six-row PASS/FAIL table,
      and exits 0 when all checks pass and 1 when any fails.
- [ ] Every invocation in the tool table is copy-pasteable from the
      repo root and executes without a usage error.
- [ ] A reader who has only this file can state the ratchet
      contract: baseline freezes existing debt, new violations
      fail, shrinking the baseline locks in wins.
- [ ] The blocking/advisory table matches `.pre-commit-config.yaml`
      entries and the `block_on_violation` flags in
      `.claude/quality_gates.json`.
- [ ] Mutation exit-code semantics (0 clean, 2 survivors tolerated,
      anything else is a crash) match
      `.github/workflows/mutation-testing.yml`.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 on branch
discussions-fix-1.9.14. Volatile numbers observed that day:
197 skills, 134 commands, 56 agents registered; description budget
73,135 of 90,000 chars used (81.3%); ratchet live counts 5 dangling
refs (baseline 31), 7 uncalled libraries (baseline 8), 1 missing
Exit Criteria (baseline 127); 13 version pins current with bandit
intentionally held at 1.8.6.

Re-verification one-liners:

```bash
# Baselines and live ratchet counts
python3 scripts/check_skill_graph_drift.py; python3 scripts/check_skill_exit_criteria_drift.py

# Registration counts and budget usage
bash scripts/capabilities-sync-check.sh | tail -3; python3 plugins/abstract/scripts/validate_budget.py | tail -3

# Pre-commit wiring of the blocking table
rg -n "check_skill_graph_drift|check_noqa|validate_budget|check_pinned_versions" .pre-commit-config.yaml

# Mutation exit-code contract
rg -n "exit_code" .github/workflows/mutation-testing.yml

# Gate dimension block flags
python3 -c "import json;print(json.load(open('.claude/quality_gates.json')))"
```
