---
name: claude-code-plugin-reference
description: Explain plugin, skill, command, agent, and hook mechanics used here. Use when authoring or debugging plugins. Do not use for ops; use night-market-operations.
---

# Claude Code Plugin Reference (night-market edition)

This is the domain pack for how Claude Code plugin machinery works in this
repository. It covers manifests, skills, commands, agents, hooks, and the
marketplace registry, with the local conventions layered on top. Every
contract below was checked against a shipped plugin (mostly `plugins/imbue`,
`plugins/abstract`, and `plugins/herald`) on 2026-07-02 at repo v1.9.15.
When another night-market skill says "see the plugin reference for what a
hook payload is," this is the file it means.

## Vocabulary

Each term is defined once here and used without redefinition below.

| Term | Meaning in this repo |
|------|----------------------|
| Plugin | A directory under `plugins/` shipping skills, commands, agents, and hooks, with its own tests, Makefile, and pyproject.toml. Independently deployable (ADR-0001). |
| Skill | A directory `skills/<name>/` containing `SKILL.md`. Loaded by the model on demand, invoked as `Skill(plugin:name)`. |
| Module | A file under a skill's `modules/` subdirectory. Loaded only when the hub `SKILL.md` routes to it (progressive loading). |
| Command | A markdown file under `commands/`. Surfaces as a slash command the user types. Repo docs refer to the namespaced form, e.g. `/sanctum:sync-capabilities`. |
| Agent | A markdown file under `agents/` defining a dispatchable subagent: frontmatter plus a system-prompt body. |
| Hook | An executable script Claude Code runs on a lifecycle event, registered in the plugin's `hooks/hooks.json`. |
| Hook event | The lifecycle point a hook fires on: `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, `UserPromptSubmit`, and others (full table below). |
| Manifest | `.claude-plugin/plugin.json`: the file Claude Code reads to register a plugin's components. |
| Marketplace | The root `.claude-plugin/marketplace.json` registry listing all plugins, installed via `/plugin marketplace add`. |
| Plugin cache | The directory Claude Code copies installed plugins into and executes them from. It is NOT the repo checkout. |
| `${CLAUDE_PLUGIN_ROOT}` | Placeholder Claude Code expands to the plugin's cache path. The only safe way to reference plugin files from hooks. |
| Host Python | The system Python interpreter that runs hook scripts. Assume 3.9, even though plugin package code targets 3.12. |

## Anatomy of a night-market plugin

Verified tree (imbue, trimmed):

```
plugins/imbue/
├── .claude-plugin/
│   ├── plugin.json       # Claude Code manifest: registers everything
│   └── metadata.json     # inter-plugin dependency manifest
├── openpackage.yml       # cross-framework export manifest
├── skills/<name>/
│   ├── SKILL.md          # hub document with frontmatter
│   └── modules/*.md      # spokes, loaded on demand
├── commands/*.md         # slash commands
├── agents/*.md           # subagents
├── hooks/
│   ├── hooks.json        # hook registration (auto-loaded)
│   ├── *.py, *.sh        # hook scripts
│   └── shared/           # vendored helpers (hook_io, vow_utils, ...)
├── scripts/              # Python utilities skills shell out to
├── tests/                # pytest suite, run per plugin
├── Makefile              # per-plugin test/lint/typecheck targets
├── pyproject.toml        # package config, per-plugin coverage threshold
└── README.md
```

### plugin.json field contract

| Field | What it does | Local rule |
|-------|--------------|------------|
| `name` | Plugin identity and namespace prefix for skills/commands | Matches directory name |
| `version` | Plugin version | Lockstep with marketplace version (1.9.15). Never hand-edit, use the bumper (below) |
| `description` | Marketplace listing text | Two-part style per ADR-0003 |
| `skills` | Array of `"./skills/<dir>"` paths. Each dir must contain a `SKILL.md`. Registration makes `Skill(plugin:name)` resolvable | Keep in sync with disk via `/sanctum:update-plugins` |
| `commands` | Array of `"./commands/<file>.md"` paths, each becoming a slash command | Same sync rule |
| `agents` | Array of `"./agents/<file>.md"` paths, each a dispatchable subagent | Same sync rule |
| `hooks` | Paths to ADDITIONAL hook files only. `./hooks/hooks.json` is auto-loaded and must never appear here | Every plugin in this repo keeps `"hooks": []` (verified across all 23 manifests). See the hooks section for why |
| `keywords` | Marketplace search and discovery terms | Free-form |
| `dependencies` / `optional_dependencies` | Names of other night-market plugins | Informational plus runtime detection only. ADR-0001 forbids import coupling: plugins detect each other via the filesystem and degrade gracefully |
| `author`, `license` | Attribution | MIT throughout |

### metadata.json

Second manifest in `.claude-plugin/`. Fields verified on imbue: `name`,
`version` (lockstep), `main`, a `skills` subset, `dependencies`,
`provides` (infrastructure/patterns/tools), and a `claude` block
(`skill_prefix`, `auto_load`, `categories`). One trap: dependency ranges
here use their own semver namespace. imbue declares `"abstract": ">=2.0.0"`
while every plugin ships 1.9.15. The range is not compared against the
marketplace version, so do not "fix" it to 1.9.15 during a bump. The
`update_versions.py` bumper knows which fields to touch.

### openpackage.yml

Cross-framework manifest consumed by the export pipeline
(`make cross-framework`, `scripts/clawhub_export.py`). Lists the skills
exported outside Claude Code and dependency sources in
`gh@athola/claude-night-market` form. Its `version` is also lockstep.

## SKILL.md contract

### Frontmatter

Fields verified on `plugins/imbue/skills/proof-of-work/SKILL.md`. Only
`name` and `description` are consumed by Claude Code itself. The rest are
house conventions read by repo tooling.

| Field | Purpose |
|-------|---------|
| `name` | Skill identity. `Skill(plugin:name)` resolves against it |
| `description` | Loading trigger. Hard cap 160 chars, enforced by `plugins/abstract/scripts/validate_budget.py` (`DESCRIPTION_MAX = 160`, ecosystem budget 90,000 chars per ADR-0004). House template: verb phrase, then "Use when [trigger].", then "Do not use when [negative]; use [sibling] instead." |
| `role` | One of `entrypoint`, `library`, `hook-target` (taxonomy below) |
| `modules` | List of `modules/*.md` spokes this hub can load |
| `dependencies`, `tags`, `category`, `usage_patterns` | Discovery metadata |
| `estimated_tokens`, `complexity`, `model_hint`, `alwaysApply`, `tools` | Advisory metadata for tooling and audits |

Role taxonomy (from `docs/skill-integration-guide.md`):

| Role | Inbound refs | User-invoked | Example |
|------|--------------|--------------|---------|
| `entrypoint` | low (0-3) | yes | `sanctum:do-issue` |
| `library` | high (4+) | rarely | `imbue:proof-of-work` |
| `hook-target` | varies | no | `imbue:vow-enforcement` |

### Progressive loading (hub-and-spoke)

A skill's `SKILL.md` is the hub: it carries the always-loaded core and a
routing table into `modules/*.md` spokes. The model loads a spoke only when
the hub tells it to. This keeps the initial token cost near the
`estimated_tokens` value instead of the whole directory. The pattern is
specified in `Skill(leyline:progressive-loading)`.

### Required sections and ratchets

- Every new or modified `SKILL.md` needs a `## Exit Criteria` section with
  concrete, observable, falsifiable checkboxes
  (`.claude/rules/skill-exit-criteria.md`). A pre-commit ratchet,
  `scripts/check_skill_exit_criteria_drift.py`, fails when the count of
  missing sections rises above `scripts/skill_exit_criteria_baseline.json`.
- `Skill(plugin:name)` references in prose are scanned by
  `plugins/abstract/scripts/skill_graph.py`. A second ratchet,
  `scripts/check_skill_graph_drift.py`, blocks commits that add dangling
  references (the `bugs` category) above
  `scripts/skill_graph_baseline.json`. When your change lowers the count,
  lower the baseline too so the ratchet tightens.
- CONSTITUTION.md rule 3 exempts skill prose from TDD but requires a
  structural validation test per new skill (constitution names the pattern
  `test_skill_<name>.py`; in practice imbue keeps them at
  `tests/unit/skills/test_<name>.py`, e.g. `test_proof_of_work.py`).

### How Skill() invocation resolves

`Skill(imbue:proof-of-work)` resolves `imbue` to the plugin registered in
the marketplace, then `proof-of-work` to the directory listed in that
plugin's `plugin.json` `skills` array. If the directory or the manifest
entry is missing, the reference is dangling and the skill-graph ratchet
will flag it.

## Commands

Frontmatter verified on `plugins/imbue/commands/justify.md` and
`plugins/sanctum/commands/fixit.md`:

```yaml
---
name: fixit
description: Fix broken functionality from pasted error output...
usage: /fixit <pasted-error-or-description> [--file <path>] ...
extends: "imbue:proof-of-work"
---
```

- `name` and `description` are required. `usage` documents the argument
  shape. `extends` (optional) names the skill the command routes into.
- `$ARGUMENTS` in the body is replaced with the raw argument string the
  user typed after the command (see fixit: "The input is `$ARGUMENTS` (a
  paste) or the contents of `--file <path>`").

When to write a command versus a skill:

| Write a | When |
|---------|------|
| Command | The user should type it deliberately with arguments (an entrypoint with a CLI-like contract) |
| Skill | The model should load it when a trigger matches (knowledge, procedure, or a library other skills compose) |
| Both | Common pattern here: a thin command that `extends` or routes into a skill (`/imbue:justify` wraps `imbue:justify`) |

The Exit Criteria rule does not apply to command files.

## Agents

Frontmatter verified on `plugins/imbue/agents/review-analyst.md`:

```yaml
---
name: review-analyst
description: Autonomous agent for conducting structured reviews with
  evidence gathering. Use when detailed code reviews requiring evidence
  trails... Do not use when quick code check without formal review...
model: opus
tools:
- Read
- Glob
- Grep
- Bash
skills: imbue:review-core, imbue:proof-of-work, ...
---
```

- The `description` drives dispatch: Claude decides whether to hand a task
  to the agent by matching it, so it must carry "Use when" and "Do not use
  when" clauses just like a skill description.
- `tools` is the allowlist the subagent gets. `model` pins the model tier.
- `skills` lists skills the agent should load. The body below the
  frontmatter is the agent's system prompt.

## Hooks

The hardest-won knowledge in the repo. Read this whole section before
writing or editing any hook.

### Events registered in this repo

Survey of every `plugins/*/hooks/hooks.json` (2026-07-02):

| Event | Registered by |
|-------|---------------|
| `PreToolUse` | abstract, conserve, gauntlet, imbue, leyline, memory-palace, pensive, sanctum |
| `PostToolUse` | abstract, cartograph, conserve, gauntlet, leyline, memory-palace, sanctum |
| `UserPromptSubmit` | abstract, egregore, imbue, memory-palace, sanctum |
| `SessionStart` | conserve, egregore, imbue, leyline, memory-palace, oracle, sanctum, tome |
| `Stop` | abstract, egregore, herald, memory-palace, oracle, sanctum |
| `PreCompact` | conserve, tome |
| `Setup`, `PermissionRequest`, `PermissionDenied` | conserve |
| `ConfigChange` | sanctum |

### Events available but unregistered here

Added between Claude Code 2.1.80 and 2.1.220. Nothing in this repo
registers them yet, which is a gap to consider rather than a defect.

| Event | Shipped | Fires when |
|-------|---------|------------|
| `Notification` | 2.1.218 | A background agent needs input or completes |
| `DirectoryAdded` | 2.1.220 | `/add-dir` or an SDK `register_repo_root` registers a working directory mid-session |

`SessionStart` gained a third source value in 2.1.212: a session opened
as a fork now reports `"fork"` rather than `"resume"`. Any hook
branching on `source` should handle it, or a forked session will take
the resume path by accident.

Hook `if:` conditions changed in 2.1.214. A single-segment `dir/**`
pattern now matches only `<cwd>/dir`, so a hook meant to fire at any
depth needs `**/dir/**`. Note that `deny` and `ask` permission rules
kept their any-depth behavior, so the two syntaxes no longer agree and
copying a pattern from one to the other silently changes its scope.

### Registration: hooks/hooks.json, never the plugin.json array

Claude Code auto-loads `hooks/hooks.json` from each installed plugin.
Listing `./hooks/hooks.json` in the `plugin.json` `hooks` array causes a
"Duplicate hooks file" error at session start. The pre-commit guard
`scripts/check_plugin_hooks.py` rejects any manifest that does it. The
`hooks` array exists only for additional hook files beyond the auto-loaded
default, and every plugin here keeps it `[]`.

Shape (verified, herald):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/double_shot_latte.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

`PreToolUse`/`PostToolUse` entries add a `matcher` regex over tool names
(imbue uses `"Write|Edit|MultiEdit"` and `"Bash"`). `timeout` is the
per-hook budget in seconds. Always reference the script through
`${CLAUDE_PLUGIN_ROOT}`.

### Payload contract: stdin JSON, never env vars

Claude Code delivers the payload as one JSON object on stdin with fields
such as `tool_name`, `tool_input`, `tool_response`, `session_id`, and
`hook_event_name`. It does NOT set `CLAUDE_TOOL_NAME`,
`CLAUDE_TOOL_INPUT`, or `CLAUDE_TOOL_OUTPUT` environment variables. Hooks
that read those env vars silently no-op on every real invocation. That
exact bug left the skill-execution logger dead for months with no error
anywhere (fixed in 1.9.14). Canonical read pattern:

```python
import json
import sys


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)  # fail open: a broken hook must not wedge the session
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
```

The shared reader `plugins/abstract/hooks/shared/hook_io.py`
(`read_hook_payload()`) implements stdin-first with a legacy env fallback
for the synthetic test harness, and warns on stderr when stdin JSON is
malformed. Because ADR-0001 forbids cross-plugin imports, leyline
(`hooks/noqa_guard.py`) and sanctum (`hooks/deferred_item_watcher.py`)
carry parallel copies that must change together (noted in the hook_io
docstring). Hooks import their own plugin's `shared/` sibling by inserting
the script directory on `sys.path` first:

```python
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from shared.vow_utils import is_git_commit, shadow_mode_active
```

### Output contract and exit codes

Repo convention is exit 0 always, with the verdict carried as JSON on
stdout. Comments in `plugins/imbue/hooks/tdd_bdd_gate.py` record that
exit code 2 has blocked the tool call since Claude Code v2.1.90, so a
stray nonzero exit is itself a decision. Fail open on parse errors.

| Event | Verdict shape (verified in repo hooks) |
|-------|-----------------------------------------|
| `PreToolUse` | `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow" \| "deny" \| "ask", "permissionDecisionReason": "..."}}`. Those three are the only values the harness recognizes (see plugin-dev:hook-development and the upstream hook docs). Correct exemplar: `plugins/leyline/hooks/noqa_guard.py` emits `"deny"`. Print nothing (exit 0) to allow |
| `Stop` | `{"decision": "block", "reason": "..."}` forces the session to keep working. `{"decision": "approve", ...}` allows the stop (herald `double_shot_latte.py`) |
| `UserPromptSubmit` | `{"hookSpecificOutput": {..., "additionalContext": "..."}}` injects context (abstract `pre_skill_execution.py`, `aggregate_learnings_daily.py`) |

Human-facing diagnostics go to stderr, never stdout (stdout must stay
parseable JSON).

Repo-local anomaly, do not copy: imbue's shadow-mode vow hooks
(`vow_no_ai_attribution.py`) emit `"warn"` in shadow mode and
`"block"` when `VOW_SHADOW_MODE=0`. Neither value is in the harness
contract (`allow`/`deny`/`ask`), so the hook most likely fails open
silently even with shadow mode off: the SB9 failure class from
night-market-failure-archaeology. `vow_bounded_reads.py` in the same
plugin correctly emits `"deny"`. File an issue rather than imitating
the `"warn"`/`"block"` output. (Anomaly flagged 2026-07-03.)

### Timeout budgets

Any subprocess a hook spawns must finish inside the `timeout` registered
in `hooks.json`, with headroom. herald once shipped an LLM call whose
timeout exceeded its registered Stop-hook budget, so the harness
killed the hook before any verdict was emitted (full record:
night-market-failure-archaeology SB7). Copy the fix's pattern: assert
`subprocess_timeout < registered_budget` in a guard test, not a
comment.

### Host Python 3.9 constraint

Plugin package code targets Python 3.12, but hook scripts run under the
system interpreter, assumed 3.9. `python39-compat.yml` enforces two
gates with uneven coverage: ruff `UP007` under `--target-version py39`
(bare unions) runs on 12 plugins' `hooks/**`, while the hook test
subtree in a real 3.9 venv runs on only 7 plugins (abstract, conserve,
egregore, imbue, leyline, memory-palace, sanctum). herald ships a Stop
hook yet is covered by neither gate.

| Banned in hook import chains | Use instead |
|------------------------------|-------------|
| `datetime.UTC` (a 3.11+ alias that broke hooks 3+ times, and ruff UP017 kept auto-reverting the fix, so root ruff config carries `extend-ignore UP017`) | `from datetime import timezone` then `datetime.now(timezone.utc)` |
| Bare `X \| Y` annotations without `from __future__ import annotations` | Put the future import first in every hook file |
| Unguarded third-party imports (`yaml`, `anthropic`) anywhere a hook's import chain reaches | Guard with try/except ImportError or import lazily inside the function. An eager import in `gauntlet/__init__.py` once broke every `git commit` with a PreToolUse ModuleNotFoundError |

The durable defense against `datetime.UTC` regressions is an AST-scanning
test, not a lint rule: see
`plugins/leyline/tests/test_python39_compat.py`, which walks the source
tree and fails on any reintroduction. When a linter fights your fix, add
an AST invariant test.

### Cache-dir execution

Installed plugins run from the Claude Code plugin cache, not the repo.
Consequences:

- No relative paths in hook scripts or `hooks.json`. Use
  `${CLAUDE_PLUGIN_ROOT}` (config) or `Path(__file__)` (Python).
- No reaching into sibling plugins or repo-root scripts at runtime.
  Shared helpers are vendored per plugin: each hook-bearing plugin keeps a
  byte-identical copy of `scripts/shared/json_utils.sh` under its own
  `hooks/shared/`, and `make check-json-utils` fails on drift.

### Testing hooks

Hook behavior is tested by piping a synthetic payload:

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}}' \
  | python3 plugins/imbue/hooks/vow_no_ai_attribution.py
```

Exit code and stdout JSON are the assertions. Hook test subtrees (for
example `plugins/imbue/tests/unit/hooks/`) run under 3.9 in CI, so keep
them stdlib-plus-pytest only.

## Marketplace mechanics

- Registry: root `.claude-plugin/marketplace.json`. Top-level `name`,
  `version`, `description`, `owner`, and a `plugins` array of
  `{name, source: "./plugins/<dir>", description, version, keywords}`.
- Install: `/plugin marketplace add athola/claude-night-market`
  (README quick start), then `/plugin install <name>@claude-night-market`.
  The install form is documented in the book's getting-started pages;
  re-verify there if it fails.
- Version lockstep: one ecosystem version fans out from marketplace.json
  to every plugin's `plugin.json`, `metadata.json`, `openpackage.yml`,
  `pyproject.toml`, and package `__init__.py`. Bump with:

```bash
uv run python plugins/sanctum/scripts/update_versions.py 1.9.16 --dry-run
uv run python plugins/sanctum/scripts/update_versions.py 1.9.16
```

- Drift tooling: `/sanctum:update-plugins [plugin] [--fix]` audits
  `plugin.json` arrays against disk contents. `make docs-sync-check` (and
  the `capabilities-sync.yml` CI job) verifies
  `book/src/reference/capabilities-*.md` matches registrations. Fix drift
  with `/sanctum:sync-capabilities --fix`, never by hand-editing the
  generated capabilities files.

## Where the authoritative docs live

- Repo book: `book/src/` (mdBook, published by `deploy-book.yml`).
  `book/src/reference/capabilities-*.md` are generated by the sync
  tooling. Getting-started and plugin pages are hand-written.
- Local deep dives: `docs/plugin-development-guide.md`,
  `docs/skill-description-guide.md`, `docs/skill-integration-guide.md`.
  Note: the dev guide's `make create-plugin NAME=...` target does not
  exist in the root Makefile as of 2026-07-02 (stale doc). Scaffold with
  `Skill(abstract:create-skill)` and copy an existing plugin's layout.
- Upstream: https://code.claude.com/docs (linked from the dev guide and
  README badge). Consult upstream when the question is about harness
  behavior this repo only records as code comments: full event payload
  schemas, new hook events, or exit-code semantics changing across Claude
  Code versions.

## When NOT to use

| You need | Use instead |
|----------|-------------|
| Run tests, lint, typecheck, release, publish | night-market-operations |
| Classify or gate a change, review rules | night-market-change-control |
| Recreate the dev environment (uv, tool pins) | night-market-build-and-env |
| Triage a failing hook or CI job by symptom | night-market-debugging-playbook |
| History of why a hook or pattern exists | night-market-failure-archaeology |
| Design invariants across plugins (isolation, lockstep rationale) | night-market-architecture-contract |
| Config axes and env vars (VOW_SHADOW_MODE and friends) | night-market-config-catalog |
| Evidence bar and test-discipline policy | night-market-validation-and-qa |

## Exit Criteria

- [ ] Given a new hook idea, you register it by editing that plugin's
      `hooks/hooks.json` only, and `python3 scripts/check_plugin_hooks.py`
      exits 0 afterward.
- [ ] A hook you author reads its payload from stdin JSON (no
      `CLAUDE_TOOL_*` env vars) and exits 0 when fed malformed input:
      `echo not-json | python3 <hook>.py; echo $?` prints 0.
- [ ] Every subprocess timeout inside your hook is asserted in a test to
      be strictly less than the `timeout` registered in `hooks.json`.
- [ ] Your hook file starts with `from __future__ import annotations`,
      uses `timezone.utc` rather than `datetime.UTC`, imports no unguarded
      third-party package, and the `python39-compat.yml` gates pass.
- [ ] A new skill you add appears in its plugin's `plugin.json` `skills`
      array, its description is at most 160 characters, it has an
      `## Exit Criteria` section, and both ratchet scripts
      (`check_skill_graph_drift.py`, `check_skill_exit_criteria_drift.py`)
      pass.
- [ ] You can state from memory why `plugin.json` `hooks` arrays are empty
      in this repo and what error appears if they are not.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 (branch discussions-fix-1.9.14).
PreToolUse verdict contract corrected to `allow|deny|ask` and the imbue
vow-hook `warn`/`block` anomaly flagged on 2026-07-03.
Volatile facts and how to re-verify them:

```bash
# Hook events per plugin
for f in plugins/*/hooks/hooks.json; do
  echo "$f"
  python3 -c "import json,sys; print(list(json.load(open(sys.argv[1]))['hooks']))" "$f"
done

# All plugin.json hooks arrays empty (exit 0 = clean)
python3 scripts/check_plugin_hooks.py
rg '"hooks": \[' plugins/*/.claude-plugin/plugin.json

# 160-char description cap still in force
rg -n 'DESCRIPTION_MAX' plugins/abstract/scripts/validate_budget.py

# Payload-on-stdin contract (read the module docstring)
head -15 plugins/abstract/hooks/shared/hook_io.py

# Exit-2 semantics comment
rg -n 'exit 2 blocks' plugins/imbue/hooks/tdd_bdd_gate.py

# permissionDecision values in repo hooks (deny is correct; the
# warn/block hits in vow_no_ai_attribution.py are the known anomaly)
rg -n '"permissionDecision"' plugins/*/hooks/*.py

# Herald timeout pairing (registered 10s vs internal 8s)
rg -n 'LLM_TIMEOUT_SECONDS|timeout' plugins/herald/hooks/

# py39 gates and covered plugins
head -50 .github/workflows/python39-compat.yml

# Version lockstep fields touched by the bumper
rg -n 'def main' -A 12 plugins/sanctum/scripts/update_versions.py

# Marketplace entry shape
head -60 .claude-plugin/marketplace.json

# Stale make create-plugin claim (doc says it exists, Makefile disagrees)
rg -n 'create-plugin' Makefile docs/plugin-development-guide.md
```

Unverified/candidate items are labeled inline: the
`/plugin install <name>@claude-night-market` form (book-documented, not
exercised here) and the explanation that metadata.json dependency ranges
form a separate semver namespace (observed, not specified anywhere).
