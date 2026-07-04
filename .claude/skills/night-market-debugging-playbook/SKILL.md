---
name: night-market-debugging-playbook
description: Triage night-market failures by symptom (hooks, CI, tests). Use when a check fails unexpectedly. Do not use for routine gates; use night-market-operations.
---

# Night Market Debugging Playbook

Match the symptom to a row, run the one discriminating command, apply
the known fix. Every row below is a failure this repo has already paid
for, with the commit hash that settled it. Do not re-derive a diagnosis
that archaeology already produced.

## Vocabulary

Terms used throughout, defined once:

- **Hook**: a script Claude Code runs on events (PreToolUse,
  PostToolUse, Stop, SessionStart). Registered in a plugin's
  `hooks/hooks.json` with a `command` and a `timeout`.
- **Hook budget**: that registered `timeout` in seconds. The harness
  kills the hook when it expires, before any output is honored.
- **Host interpreter**: hooks run as `python3 ...` under the machine's
  system Python (floor: 3.9), NOT the repo's uv-managed 3.12 venv.
  Third-party packages a plugin declares are not guaranteed present.
- **skrills**: optional Rust binary for skill validation and analysis.
  Every Makefile target that uses it has a Python fallback.
- **Import chain**: everything a `import x` transitively pulls in,
  including the plugin's `__init__.py`.

## Symptom index

| # | Symptom | Likely cause | Story |
|---|---------|--------------|-------|
| 1 | PreToolUse hook error / ModuleNotFoundError on every `git commit` | Unguarded third-party import in a plugin `__init__.py` reachable from a hook | 45dd77ef, 9bfc0a7a |
| 2 | `python39-compat` is the only failing CI check | A 3.10+/3.11+ construct (`datetime.UTC`, bare `X \| Y` union) entered a hook import chain | 18c9340d, PR #511 |
| 3 | Hook exits 0 but never does anything | Hook reads `CLAUDE_TOOL_*` env vars instead of stdin JSON | CHANGELOG 1.9.14 |
| 4 | `capabilities-sync` CI fails | plugin.json registrations drifted from the book reference | capabilities-sync.yml |
| 5 | Root `pytest` raises ImportPathMismatchError | Plugin tests collected from repo root instead of per plugin | conftest.py, pyproject norecursedirs |
| 6 | `slop-check` fails on a PR | Slop score over 3.0 in a `docs/` or `book/src/` markdown file | slop-check.yml |
| 7 | Stop hook produces no verdict at all | Inner subprocess timeout >= registered hook budget | 268cff89 |
| 8 | CI broken on a GitHub action or tool pin | Stale or nonexistent pinned version | f81d89a5, 25bf5a9d |
| 9 | Scanner reports nothing on input you know is bad | Swallowed exception (except-and-continue) drops files silently | 666171c3, b6de71cf |
| 10 | `skrills: not found` | Missing optional binary (a Python fallback exists) | Makefile validate-skills |

## Triage runbooks

### 1. ModuleNotFoundError from a hook on every commit

First command (substitute the hook path from the error message):

```bash
echo '{}' | python3 plugins/gauntlet/hooks/precommit_gate.py; echo "exit=$?"
```

What the result means: a traceback names the module whose import chain
pulls in a package the host interpreter lacks. Exit 0 with no output
means the hook is import-safe and the problem is elsewhere (check the
hook registration in `hooks/hooks.json`).

Fix: guard the import at module level or defer it into the function
that needs it. The gauntlet incident: `precommit_gate.py` imported
`gauntlet.knowledge_store`, whose `__init__.py` eagerly imported
modules doing bare `import yaml` and `import anthropic`. Guarded in
45dd77ef (#518), deferred in 9bfc0a7a. Add a regression test that
blocks the package via a `sys.meta_path` blocker and re-imports the
hook (pattern in `plugins/gauntlet/tests/unit/test_challenges.py`).

### 2. python39-compat is the only failing check

The repo is Python 3.12, but hook scripts and their transitive imports
must stay importable under Python 3.9 (`.github/workflows/
python39-compat.yml`). First command:

```bash
uv run ruff check --select UP007 --target-version py39 plugins/<plugin>/hooks/
rg -n 'datetime\.UTC|from datetime import UTC' plugins/<plugin>/
```

What the result means: UP007 hits are bare `X | Y` union annotations
that raise TypeError at import time on 3.9. The `rg` hits are the
`datetime.UTC` alias (3.11+), which UP007 does not catch. Either one
in a hook import chain breaks every hook at once: on PR #511 a single
`datetime.UTC` in `leyline.quota_tracker` produced three cascade
failures (18c9340d).

Fix: use `from datetime import timezone` with `timezone.utc`, and
`typing.Union`/`Optional` or a `from __future__ import annotations`
line for unions. To mirror CI's Gate 2 locally (verified 2026-07-02):

```bash
uv venv --python 3.9 /tmp/hook39
VIRTUAL_ENV=/tmp/hook39 uv pip install pytest pyyaml
cd plugins/abstract
/tmp/hook39/bin/python -m pytest tests/hooks --override-ini="addopts="
```

The `addopts` override strips per-plugin coverage flags that need
packages the bare venv lacks. See also the linter trap below: ruff
will fight this fix.

### 3. Hook exits 0 but never does anything

First command:

```bash
rg -l 'CLAUDE_TOOL_' plugins/*/hooks/
rg -ln 'read_hook_payload' plugins/*/hooks/
```

What the result means: Claude Code never sets `CLAUDE_TOOL_*`
environment variables. The payload arrives as JSON on stdin. A hook
reading only env vars is a silent no-op: it exits 0, CI is green, and
nothing downstream ever happens. This starved the `[Learning]`
discussion digests for two months (last digest 2026-04-25) before
anyone noticed (CHANGELOG 1.9.14).

Fix: read stdin first via the canonical reader
`plugins/abstract/hooks/shared/hook_io.py` (`read_hook_payload`,
stdin-first with env-var fallback for the test harness). Then verify
the hook actually fires: pipe a realistic payload in and check for the
side effect rather than the exit code alone.

### 4. capabilities-sync CI fails

First command:

```bash
bash scripts/capabilities-sync-check.sh
```

What the result means: the script diffs every plugin's
`.claude-plugin/plugin.json` registrations against
`book/src/reference/capabilities-reference.md` and prints the drifted
entries. `PASSED: All capabilities are in sync` means the CI failure
was against an older commit. Rebase and rerun.

Fix: run the sanctum sync command with the fix flag:

```
/sanctum:sync-capabilities --fix
```

### 5. Root pytest raises ImportPathMismatchError

First command:

```bash
rg -n 'norecursedirs' pyproject.toml
```

What the result means: root pytest excludes `plugins/*` on purpose.
Plugins carry duplicate test module names and conftest fixtures, and
collecting them from the root collides (documented in `conftest.py`).
If you see this error you ran `pytest` across plugin boundaries.

Fix: run tests per plugin, never from the root against plugins:

```bash
cd plugins/imbue && uv run pytest tests/unit/test_deferred_capture.py -x -q
make sanctum-test          # delegation target, any plugin name works
./scripts/run-plugin-tests.sh --all
```

### 6. slop-check fails on a PR

First command: read the PR comment the workflow posts (it lists the
failing files and scores), then reproduce locally. The score is
tier-1 hits x3 plus tier-2 hits x2 plus em dashes, per 100 words,
threshold 3.0. Copy the `TIER1` and `TIER2` regexes from
`.github/workflows/slop-check.yml` rather than retyping the word
lists, then:

```bash
grep -o '—' docs/<file>.md | wc -l
grep -oiE "$TIER1" docs/<file>.md | wc -l
```

Fix: rewrite per `.claude/rules/slop-scan-for-docs.md`. Replace em
dashes with colons or periods, and replace the flagged vocabulary with
plain words. Never de-slop historical CHANGELOG entries.

### 7. Stop hook produces no verdict at all

First command:

```bash
rg -n '"timeout"' plugins/herald/hooks/hooks.json
rg -n 'TIMEOUT' plugins/herald/hooks/double_shot_latte.py
```

What the result means: if any subprocess or LLM-call timeout inside
the hook is greater than or equal to the registered hook budget, the
harness kills the whole hook before it can print a decision, and the
hook dies without emitting anything. Herald shipped `LLM_TIMEOUT_SECONDS =
30` inside a 10-second registered budget (fixed in 268cff89: capped to
8 with startup margin, and the LLM second shot gated to the single
ambiguous outcome).

Fix: cap every inner timeout strictly below the registered budget and
pin the invariant with a guard test, as in
`plugins/herald/tests/unit/test_double_shot_latte.py::`
`test_llm_timeout_fits_within_hook_timeout`. Deterministic tests do
not exercise optional LLM branches, so the timeout relation must be
asserted directly.

### 8. CI broken on an action or tool pin

First command:

```bash
python3 scripts/check_pinned_versions.py
```

What the result means: the script checks GitHub-sourced pins (CI
actions in `.github/workflows/*`, external `rev:` hooks in
`.pre-commit-config.yaml`) against upstream and prints stale or held
pins with reasons. Two settled incidents: `setup-uv@v8` failed because
the bare `v8` tag does not exist upstream (pinned to `v8.2.0`,
f81d89a5), and bandit 1.9+ dropped Python 3.9 support (held at 1.8.6,
25bf5a9d).

Fix: pin to a full existing tag, and when holding a version back,
record the reason where the checker reports it so the hold is visible.

### 9. Scanner reports nothing on input you know is bad

First command: feed the scanner one deliberately malformed file and
watch for an ADVISORY finding. Silence is the bug. Then look for the
swallow:

```bash
rg -n 'except' scripts/check_hook_modernization.py
```

What the result means: an except-and-continue block in a scanner loop
drops unparseable files without a trace, so the worst inputs are
exactly the ones never reported. Incidents B1-B4 (666171c3, #575, and
b6de71cf) covered hook-modernization scanning, strict-mode file drops,
and DORA metrics rating malformed tags as Elite.

Fix: Constitution rule 10. Errors are not optional: emit an advisory
finding for each skipped file or propagate. Never catch-and-continue
without output.

### 10. skrills not found

First command:

```bash
make validate-skills
```

What the result means: `skrills not available, using Python fallback`
followed by `scripts/check_plugin_hooks.py` output is normal
operation rather than an error. `make analyze-skills` falls back to
`scripts/generate_dependency_map.py`. Only build the binary if you
need the Rust path:

```bash
make skrills-build    # needs cargo and the skrills repo at $HOME/skrills
                      # (override with SKRILLS_REPO=/path)
```

## Traps that cost real time

### The linter fights the fix

Ruff's pyupgrade rule UP017 auto-rewrites `timezone.utc` back to the
3.11-only `datetime.UTC`, silently reverting the py39 fix on the next
`make lint`. This recurred at least three times (18c9340d, b0049fde,
709dafc9) before the durable defense landed: `UP017` in root
`pyproject.toml` `extend-ignore`, per-line suppression comments with a
stated reason where needed (Constitution rule 6 requires the reason),
and above all an AST-scanning invariant test
(`plugins/leyline/tests/test_python39_compat.py`) that fails CI on any
reintroduction. Lesson: when an autofixer keeps reverting your fix,
re-applying is attempt N of an infinite loop. Encode the invariant as
a test that scans the source.

### The green gate that checks nothing

A green check proves only that the gate's own spec was satisfied. A
gate can be quietly configured to check nothing and stay green. The
global mirrors-mypy pre-commit hook silently disabled 13 error codes,
and typecheck ran
`--changed` instead of `--all` (fixed in 1.9.12: neutered hook
removed, `run-plugin-typecheck --all`, `typecheck.yml` gating every
PR). Discriminating test for any suspicious gate: introduce one known
violation and confirm the gate goes red. If it stays green, the bug
is inside the gate itself.

### The cache-dir relative path

Plugins execute from Claude Code's cache directory rather than the
repo checkout, so a CWD-relative path in a hook resolves to nothing. The
conserve session-start hook broke exactly this way and was fixed by
inlining its JSON utilities (CHANGELOG 1.4.1; the inlined-copy sync
notice lives in `scripts/shared/json_utils.sh`). Rule: hooks resolve
paths from `${CLAUDE_PLUGIN_ROOT}` or relative to their own script
file, never from the working directory.

## The two-challenge rule

After two consecutive failed attempts of the same shape (same file,
same error class, same tool), do not try a third variation. Switch to
a read-only diagnostic: the discriminating command from the matching
row above, verbose test output, or printing the actual state. Then
report four things: what you believed, what the evidence now says,
what you would try differently, and an explicit ask. This discipline
comes from the global CLAUDE.md and is wired into
`plugins/sanctum/commands/fixit.md`. It exists to kill the
"47 edits to make a test pass" loop.

## When NOT to use

- Running tests, lint, releases, or publishing normally: use
  night-market-operations.
- Recreating the dev environment (uv, tool installs, first clone): use
  night-market-build-and-env.
- The history and rationale behind these battles (reverts, dead ends,
  the 2026-03-28 unbloat cascade): use night-market-failure-archaeology.
- Hook, skill, and plugin mechanics as reference material: use
  claude-code-plugin-reference.
- Deciding how a fix must be classified, gated, and reviewed: use
  night-market-change-control.
- Configuration axes and their defaults: use night-market-config-catalog.

## Exit Criteria

- [ ] The failure was matched to a symptom row, or explicitly
      identified as a new failure mode not in this table.
- [ ] The row's first command was run and its output captured before
      any fix was attempted.
- [ ] The applied fix matches the row's known remedy, or the deviation
      is stated with evidence.
- [ ] For hook fixes: the hook was re-run under bare `python3` with a
      stdin JSON payload and the side effect (beyond exit 0) was
      observed.
- [ ] For recurring-class fixes (py39, timeouts, swallowed errors): an
      invariant test now fails if the bug is reintroduced.
- [ ] If two same-shape attempts failed, work switched to a read-only
      diagnostic and a four-part report was produced.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15, branch discussions-fix-1.9.14.
All commit hashes verified with `git log --oneline -1 <hash>`. Facts
most likely to drift, with re-verification one-liners:

- Herald timeout values:
  `rg -n '"timeout"' plugins/herald/hooks/hooks.json` and
  `rg -n 'LLM_TIMEOUT_SECONDS' plugins/herald/hooks/double_shot_latte.py`
  (10 and 8 as of 2026-07-02).
- Slop threshold and tier lists:
  `rg -n 'THRESHOLD|TIER1|TIER2' .github/workflows/slop-check.yml`
  (3.0 as of 2026-07-02).
- py39 gates:
  `rg -n 'UP007|--python 3.9' .github/workflows/python39-compat.yml`.
- UP017 hold: `rg -n 'UP017' pyproject.toml`.
- Canonical hook reader exists:
  `rg -n 'def read_hook_payload' plugins/abstract/hooks/shared/hook_io.py`.
- Pin checker and sync checker exist:
  `ls scripts/check_pinned_versions.py scripts/capabilities-sync-check.sh`.
- skrills fallbacks: `rg -n -A 8 'validate-skills:' Makefile`.
- Root test exclusion: `rg -n 'norecursedirs' pyproject.toml`.
- Unverified beyond commit messages: none. PR #511 confirmed via
  `gh pr view 511` and the 18c9340d commit body.
