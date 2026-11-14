---
name: settled-battles
description: "Settled battles SB1-SB15: what was tried, why it failed or was reverted, and the guard that now holds."
---

## Settled battles

### SB1: tasks_manager cross-plugin DRY consolidation (reverted)

- Symptom: three near-identical `tasks_manager.py` copies in attune,
  sanctum, and spec-kit looked like textbook duplication.
- Root cause of the failure: consolidating them into a root
  `scripts/tasks_manager.py` (1,169 lines deleted across 6 files)
  broke plugin self-containment. Plugins are independent deployables
  that run from a Claude Code cache directory, so they cannot import
  from the repo root.
- Evidence: `054e2679` (consolidate, 2026-01-23), `29961cd2` (revert,
  same day), `d89a55c7` (differentiated per-plugin copies). All three
  copies exist today under `plugins/<p>/scripts/tasks_manager.py`.
  `docs/dependency-audit.md` tracks cross-plugin deps and fallbacks.
- Status: settled. Per-plugin copies are intentional.
- Lesson: DRY across plugin boundaries is an anti-pattern here. Do not
  "helpfully" re-consolidate duplicated plugin scripts.

### SB2: LSP proxy (speculative infrastructure, killed)

- Symptom: `scripts/lsp-proxy.py` added for "graceful server fallback"
  with no consumer demanding it.
- Root cause: speculative abstraction built ahead of need.
- Evidence: `2fcb256d` (add), killed in PR #193 review, `bc318947`
  (revert, 2026-02-11, restores `.cclsp.json`).
- Status: settled. Do not re-add without a concrete consumer.
- Lesson: infrastructure without a present consumer dies in review.
  See also `.claude/rules/shared-utility-consumer-rule.md`.

### SB3: Tier-3 unbloat over-deletion (2026-03-28, the big one)

- Symptom: unbloat deleted 182 files (66K lines) using only the Python
  import graph to decide what was dead.
- Root cause: skills and commands reference scripts from markdown, not
  Python imports. 28 actively referenced scripts plus 18 companion
  test files were classified dead and deleted.
- Evidence: `a3f11323` (the deletion), `3f280334` (restore the 28
  scripts and 18 tests), `b5f08bf7` (CI repair: dead docs workflow,
  missing capabilities entries), `d6c128f5` and `01a13e70` (further
  repair and governance follow-ups). Recovery point was branch
  `backup/unbloat-20260328`.
- Status: settled, with the highest single blast radius on record.
- Lesson: any deletion campaign must scan markdown references
  (skills, commands, agents), never imports alone. Always take a
  `backup/unbloat-<date>` branch first.

### SB4: bulk lint ignores (reverted)

- Symptom: global ruff ignores made parseltongue lint pass while
  hiding 73 real violations.
- Root cause: silencing the gate instead of fixing the findings.
- Evidence: `06b9b1db` (2026-03-10) reverts the bulk ignores and fixes
  all 73 at source. The commit body cites issue #296 as the
  anti-bulk-ignore policy anchor.
- Status: settled. Constitution rule 6 also bans bare suppressions.
- Lesson: a suppressed violation is a hidden defect. Fix at source or
  suppress per line with a stated reason.

### SB5: datetime.UTC breaking py39 hooks (fixed 3+ times)

- Symptom: hook import chains crash under host Python 3.9 because
  `datetime.UTC` is a 3.11+ alias. On PR #511 this was the sole
  failing check, with three cascade failures caused by one
  ImportError.
- Root cause: ruff's pyupgrade rule UP017 kept auto-rewriting
  `timezone.utc` back to `datetime.UTC`, silently re-breaking the fix.
  The linter was fighting the fix.
- Evidence: `18c9340d` (leyline quota_tracker, 2026-05-07),
  `b0049fde` (abstract), `709dafc9` (attune).
- Status: settled by a durable guard, not by the fixes themselves:
  an AST-scanning test (`plugins/leyline/tests/test_python39_compat.py`)
  fails CI on any reintroduction, root ruff config extend-ignores
  UP017, and the surviving per-line pyupgrade suppression markers each
  carry a stated reason.
- Lesson: when the linter fights the fix, only an AST invariant test
  holds the line. A fix commit alone will be reverted by tooling.

### SB6: unguarded yaml/anthropic imports in hook chains

- Symptom: every `git commit` emitted a PreToolUse hook
  ModuleNotFoundError.
- Root cause: gauntlet's `__init__` eagerly imported dependencies
  (yaml, anthropic) that the bare host interpreter running hooks does
  not have.
- Evidence: `45dd77ef` (guard yaml import, #518, 2026-05-08),
  `9bfc0a7a` (defer anthropic import to function scope). Regression
  tests block re-imports with a `sys.meta_path` blocker
  (`plugins/gauntlet/tests/unit/test_challenges.py`).
- Status: settled.
- Lesson: hook entrypoints and everything they transitively import
  must be import-safe under a bare interpreter with no third-party
  packages.

### SB7: herald LLM timeout exceeding the hook budget

- Symptom: the herald double-shot-latte Stop-hook judge produced no
  verdict at all in the failure case.
- Root cause: `LLM_TIMEOUT_SECONDS = 30` inside a hook registered with
  a 10-second budget. The harness killed the whole hook before the LLM
  subprocess returned, so even the deterministic path's verdict was
  lost.
- Evidence: `3d22f02a` (the judge), `268cff89` (2026-05-30: cap LLM
  timeout to 8s, gate the LLM second shot to the single ambiguous
  outcome). A guard test asserts `LLM_TIMEOUT_SECONDS` is below the
  registered hook timeout
  (`plugins/herald/tests/unit/test_double_shot_latte.py`).
- Status: settled.
- Lesson: assert every subprocess timeout against the registered hook
  budget in a test. Deterministic tests do not exercise optional
  branches, so the optional branch needs its own guard.

### SB8: silent scanner failures B1-B4

- Symptom: quality scanners silently dropped files on malformed input,
  so broken inputs produced clean-looking reports. One metric reported
  Elite on malformed tags.
- Root cause: except-and-continue blocks in scanner loops swallowed
  parse errors.
- Evidence: `666171c3` (2026-06-18, fixes #575, findings B1-B4 from
  PR #521), `b6de71cf` (plugin-check: bound hangs, unmask failures).
- Status: settled. Scanners now emit ADVISORY findings instead of
  skipping silently.
- Lesson: except-continue in a scanner is a landmine. A scanner that
  cannot parse an input must say so in its output.

### SB9: hooks reading env vars Claude Code never sets

- Symptom: the `[Learning]` discussion digest went quiet after
  2026-04-25. That starvation was the only visible symptom.
- Root cause: PreToolUse/PostToolUse hooks (`skill_execution_logger`,
  `pre_skill_execution`, `homeostatic_monitor` in abstract, leyline
  `noqa_guard`, sanctum `deferred_item_watcher`) read `CLAUDE_TOOL_*`
  environment variables that Claude Code never populates. The payload
  arrives as JSON on stdin. The hooks exited 0 without doing anything,
  for months.
- Evidence: CHANGELOG 1.9.14 (2026-06-27). Fix: canonical stdin-first
  reader `read_hook_payload` in
  `plugins/abstract/hooks/shared/hook_io.py`, with env-var fallback
  for the test harness. Consumers: the five hooks above.
- Status: settled.
- Lesson: a hook that exits 0 is not a hook that worked. Verify hooks
  actually fire and consume the real payload contract (stdin JSON).

### SB10: neutered mypy gate

- Symptom: typecheck was green while real type errors accumulated.
- Root cause: the global mirrors-mypy pre-commit hook silently
  disabled 13 error codes, and the typecheck hook ran `--changed`
  instead of `--all`.
- Evidence: CHANGELOG 1.9.12 (2026-06-18): neutered hook removed,
  per-plugin strict mypy with `--all`, new `typecheck.yml` workflow
  gating every PR.
- Status: settled.
- Lesson: a green gate that disables checks is worse than no gate.
  Audit what a gate actually runs, not whether it passes.

### SB11: CI pin breakage (recurring)

- Symptom: CI failures from tool pins that were never valid or aged
  out.
- Root cause: `setup-uv@v8` bare tag does not exist upstream, and
  bandit newer than 1.8.6 dropped Python 3.9 support needed by hooks.
- Evidence: `f81d89a5` (pin setup-uv to v8.2.0), `25bf5a9d` (pin
  bandit 1.8.6).
- Status: settled by standing guards `scripts/check_pinned_versions.py`
  and `scripts/check_ruff_version.py` (pre-commit, run only when the
  relevant files are staged).
- Lesson: pin exact tags and let the guard scripts flag drift. Never
  trust a major-version alias tag to exist.

### SB12: gh discussion CLI does not exist

- Symptom: playbooks called `gh discussion create/comment/list` and
  failed. There is no such gh subcommand.
- Root cause: hallucinated CLI surface. GitHub Discussions are
  reachable only through the GraphQL API.
- Evidence: CHANGELOG (minister playbook repair replaced the calls
  with GraphQL mutations). Working templates are in
  `plugins/leyline/skills/git-platform/modules/command-mapping.md`
  using `gh api graphql`.
- Status: settled.
- Lesson: Discussions equal GraphQL only. Any script touching
  Discussions goes through `gh api graphql`, never a `gh discussion`
  subcommand.

### SB13: pensive break halted multi-hit overflow detection

- Symptom: pensive's integer-overflow scan reported at most one hit
  per file (PEN-013).
- Root cause: a loop `break` after the first finding.
- Evidence: `4993273b` (2026-06-22).
- Status: settled.
- Lesson: in detection loops, collect all findings. An early exit in a
  scanner is a correctness bug.

### SB14: broken relative paths from the plugin cache directory

- Symptom: conserve's session-start hook failed when the plugin ran
  from the Claude Code cache directory instead of the repo checkout.
- Root cause: a relative path assumed the repo layout. Installed
  plugins execute from a cache dir where sibling repo paths do not
  exist.
- Evidence: CHANGELOG ("Inlined JSON utilities in conserve
  session-start hook"), later generalized in `a8c9e4e9` (vendor
  `json_utils.sh` per plugin).
- Status: settled.
- Lesson: plugins run from a cache dir. No relative paths out of the
  plugin root, ever. Vendor small utilities per plugin (see SB1: this
  duplication is intentional).

### SB15: imbue body-text fallback over-classification

- Symptom: imbue classified unrelated skills as review-workflow
  because a fallback matched loose body text when frontmatter did not
  answer.
- Root cause: a defensive fallback standing in for data that should be
  authoritative. The fallback masked the real signal instead of
  failing loudly.
- Evidence: `69fbd32c` (2026-06-24, remove the fallback). Pattern
  codified in `.claude/rules/prefer-invariants-over-fallbacks.md`
  (`9f771794`) and the imbue verifier-integrity module (`29081fda`).
- Status: settled.
- Lesson: a fallback that guesses is worse than a loud miss. Prefer
  invariants over fallbacks.
