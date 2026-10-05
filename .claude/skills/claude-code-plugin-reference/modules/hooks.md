# Hooks

The hardest-won knowledge in the repo. Read this whole file before
writing or editing any hook.

## Events registered in this repo

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
| `Notification` | conserve |

## Events available but unregistered here

The full roster is `plugins/abstract/src/abstract/hook_events.py`: 33
events at 2.1.289, read by both frontmatter and hooks.json validation.
Ones a plugin here could use and does not yet:

| Event | Shipped | Fires when |
|-------|---------|------------|
| `PreModelSwitch` / `PostModelSwitch` | 2.1.251 | `/model` changes the session model. The pre event can block or confirm |
| `StopFailure` | 2.1.78 | A turn ends on an API error; matcher on type such as `rate_limit` |
| `SubagentStart` | | A subagent starts; the place for subagent-only context, since SessionStart does not fire for subagents |
| `InstructionsLoaded` | | A CLAUDE.md or rule file loads, with `agent_id`, `agent_type`, `effort` since 2.1.288 |
| `DirectoryAdded` | 2.1.220 | `/add-dir` or an SDK `register_repo_root` registers a working directory mid-session |

`Notification` fires when Claude needs approval, has idled, or a
background agent needs input. Its matcher values (`permission_prompt`,
`idle_prompt`, `auth_success`, the elicitation dialogs) are documented in
hooks.md "Notification". `conserve` records each event to `.claude/logs/`.

Stop input carries `background_tasks` and `session_crons`. Since 2.1.232
interactive subagent spawns run in the background, so a Stop hook that
blocks on unfinished work must check them: `egregore`'s Stop hook lets the
session stop while an `egregore:orchestrator` subagent is in flight.

`SessionStart` gained a fifth source value in 2.1.212: a session opened
as a fork reports `"fork"`. A matcher that enumerates the other four
silently stops firing for forks, which is what
`tests/unit/test_session_start_sources.py` now guards. `conserve` covers
every source. `egregore` matches only `startup` and `resume`: `fork` and
`compact` continue a conversation that already carries its banner, and
`clear` was excluded before `fork` shipped, so this change leaves that
choice as it found it.

Hook `if:` conditions changed in 2.1.214. A single-segment `dir/**`
pattern now matches only `<cwd>/dir`, so a hook meant to fire at any
depth needs `**/dir/**`. Note that `deny` and `ask` permission rules
kept their any-depth behavior, so the two syntaxes no longer agree and
copying a pattern from one to the other silently changes its scope.

## Registration: hooks/hooks.json, never the plugin.json array

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
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/double_shot_latte.py\"",
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
`${CLAUDE_PLUGIN_ROOT}`, inside double quotes: the install path can hold
a space, and an unquoted placeholder then splits into several words.
`claude plugin validate` warns on it since 2.1.281, and
`tests/test_hook_commands_quote_plugin_root.py` fails on it. Exec form
(`"args": [...]`) needs no quoting.

The same file may name a mod's module under `"modules"` beside `"hooks"`;
see `modules/mods.md`.

## Payload contract: stdin JSON, never env vars

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

## Output contract and exit codes

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

## Timeout budgets

Any subprocess a hook spawns must finish inside the `timeout` registered
in `hooks.json`, with headroom. herald once shipped an LLM call whose
timeout exceeded its registered Stop-hook budget, so the harness
killed the hook before any verdict was emitted (full record:
night-market-failure-archaeology SB7). Copy the fix's pattern: assert
`subprocess_timeout < registered_budget` in a guard test, not a
comment.

## Host Python 3.9 constraint

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

## Cache-dir execution

Installed plugins run from the Claude Code plugin cache, not the repo.
Consequences:

- No relative paths in hook scripts or `hooks.json`. Use
  `${CLAUDE_PLUGIN_ROOT}` (config) or `Path(__file__)` (Python).
- No reaching into sibling plugins or repo-root scripts at runtime.
  Shared helpers are vendored per plugin: each hook-bearing plugin keeps a
  byte-identical copy of `scripts/shared/json_utils.sh` under its own
  `hooks/shared/`, and `make check-json-utils` fails on drift.

## Testing hooks

Hook behavior is tested by piping a synthetic payload:

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}}' \
  | python3 plugins/imbue/hooks/vow_no_ai_attribution.py
```

Exit code and stdout JSON are the assertions. Hook test subtrees (for
example `plugins/imbue/tests/unit/hooks/`) run under 3.9 in CI, so keep
them stdlib-plus-pytest only.
