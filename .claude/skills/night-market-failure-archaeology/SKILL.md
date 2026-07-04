---
name: night-market-failure-archaeology
description: Chronicles settled battles, reverts, and dead ends. Use when a fix echoes a past failure. Do not use for live triage; use night-market-debugging-playbook.
---

# Night Market Failure Archaeology

This is a reference document, not a runbook. It records every major
investigation, dead end, rejected fix, and revert in this repo as
symptom, root cause, evidence, status, and lesson, so nobody re-fights
a settled battle. For triage of a failure happening right now, use
`night-market-debugging-playbook`. Come here when a proposed change
smells like something the repo already tried and rejected.

Jargon used below:

- "py39 hooks": hook scripts run under the host system Python (3.9
  floor), while the rest of the repo requires Python 3.12. Enforced by
  `.github/workflows/python39-compat.yml`.
- "unbloat": the conserve plugin's dead-code deletion campaign.
- "Stop hook": a Claude Code hook that runs when a session turn ends.
- "settled": the fight is over. Re-opening it requires new evidence
  and a note in the collective memory, not a hunch.

## How to use this chronicle

1. Before implementing, scan the battle titles and the recurring-class
   table for anything resembling your plan.
2. If a battle matches, read its lesson. Follow it, or write down why
   this time is different before overriding it.
3. Verify any hash you rely on: `git log --format='%h %s' -1 <hash>`.
4. When your own battle settles, add an entry (format at the bottom).

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
  failing check, with three cascade failures rooted in one
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
  with GraphQL mutations). Working templates live in
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
  scanner is a correctness bug, not an optimization.

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

## Recurring failure classes (ranked)

Ranked by observed cost across the repo's history. Hashes are sample
evidence, not complete lists.

| Rank | Class | Shape | Sample evidence | Standing guard |
|------|-------|-------|-----------------|----------------|
| RC1 | Silent failure / swallowed exceptions | except-continue, exit 0 on failure, dropped files | `e0d1c464`, `10b4b790`, `52ae1459`, `fedb1c5b`, `0d28a260`, `bfebb1ad`, `7987649c`, `89faaaf7` | Constitution rule 10 and the narrow-bare-except campaign |
| RC2 | py39 / host-Python import fragility | hooks crash under system Python | SB5, SB6 hashes | `python39-compat.yml`, AST test, meta_path tests |
| RC3 | PR-review rework churn | long fix-chains after review | tautological tests `a94240e2`, `f1cbbcf1`, `30e58586`, `42f7ce84`; AI-slop prose `2a039760`, `62f598e9`; stale wiring `204b927c`, `332bcb75` | shift-left pre-commit guards, slop-check CI |
| RC4 | Unbloat over-deletion | import-graph-only deletion | SB3 hashes | markdown-reference scan, backup branches |
| RC5 | CI pin breakage | invalid or stale tool pins | SB11 hashes | `check_pinned_versions.py`, `check_ruff_version.py` |
| RC6 | Version drift | manifests and SKILL.md frontmatter out of lockstep | fan-out via `plugins/sanctum/scripts/update_versions.py` | sanctum:version-updates flow |
| RC7 | Fallback over-classification | guessing fallback masks bad data | SB15 hashes | prefer-invariants-over-fallbacks rule |

## Dead ends: fenced off

These branches are superseded. Do not resume work on them. They stay
for archaeology only.

| Branch | Why it is dead |
|--------|----------------|
| `attune-tasks-poc` | Superseded. Its lineage spawned the reverted SB1 consolidation. |
| `agent-coordination` | 2026-03-17 experiment, superseded by conjure and egregore. |
| `feature/knowledge-brain` | Pre-1.0 prototype, superseded by memory-palace. |
| `feat/slop-clean-before-post` | Superseded by scribe Tier-5 patterns on master (`509bffaf`). |

The `backup/unbloat-*` branches (a dozen as of 2026-07-02) are
recovery snapshots and the institutional memory of RC4.
`backup/unbloat-20260328` was the recovery point for SB3. Do not
delete them casually.

## The costliest three (judgment call)

1. The PR-review rework loop (RC3). Roughly 140 fix-chain commits
   spent repairing review findings after the fact (estimate from the
   2026-07 repo audit, exact count unverified). Response: shift
   quality left into pre-commit guards so review stops being the
   first gate.
2. The 2026-03-28 unbloat cascade (SB3). Highest single blast radius:
   one commit, 182 files, multi-commit recovery, CI repair.
3. py39 hook fragility (SB5, SB6). Each occurrence was a total hook
   outage, and the linter actively fought the fix until an AST
   invariant test ended it.

## Adding an entry when a new battle settles

What counts as a settled battle:

- a revert of a merged change (with the reason understood)
- a bug fixed more than once before a durable guard landed
- a feature or abstraction killed in review or post-merge
- an incident with a multi-commit repair chain

Format: copy the SB block shape. Five fields, all required: Symptom,
Root cause, Evidence (commit hashes, each verified with
`git log --format='%h %s' -1 <hash>` before you write it down),
Status, Lesson. Assign the next SB number. Add the class to the RC
table if it recurs.

Where the lesson must also land (this file is not the system of
record for policy):

- GitHub Discussions `[Learning]` or `[PR Finding]` post, and the
  decision journal (`docs/tradeoffs.md`, `docs/lessons-learned.md`,
  append-only). See `night-market-collective-memory`.
- If the lesson is a durable behavioral policy, graduate it to
  `.claude/rules/` through the pipeline in
  `night-market-research-methodology`, subject to
  `night-market-change-control`.

## When NOT to use

- A failure is happening right now and you need triage steps: use
  `night-market-debugging-playbook`.
- You need the release/test/lint command anatomy behind a fix: use
  `night-market-operations`.
- You are deciding how to classify or gate a change: use
  `night-market-change-control`.
- You want the design invariants these battles produced (plugin
  self-containment, hook import-safety): use
  `night-market-architecture-contract`.
- You are recording a decision or lesson into Discussions or the
  decision journal: use `night-market-collective-memory`.

## Exit Criteria

- [ ] Every commit hash cited in this file resolves: the loop in
      Provenance below prints no MISSING lines.
- [ ] For the change at hand, the matching SB/RC entries were read,
      and any override of a lesson is written down with a rationale.
- [ ] Any newly added entry has all five fields and at least one
      verified commit hash.
- [ ] The new entry's lesson is cross-posted per the collective-memory
      skill (Discussions post or decision-journal line exists).

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15, branch master history
(1,247 commits). Volatile facts: branch list, RC ranking, and the
costliest-three judgment reflect the repo as of that date. The ~140
fix-chain commit count for RC3 is an unverified estimate.

Re-verification commands:

```bash
# All cited hashes still resolve
for h in 054e2679 29961cd2 d89a55c7 2fcb256d bc318947 a3f11323 \
  3f280334 b5f08bf7 d6c128f5 01a13e70 06b9b1db 18c9340d b0049fde \
  709dafc9 45dd77ef 9bfc0a7a 3d22f02a 268cff89 666171c3 b6de71cf \
  f81d89a5 25bf5a9d 4993273b a8c9e4e9 69fbd32c 9f771794 29081fda \
  509bffaf e0d1c464 10b4b790 52ae1459 fedb1c5b 0d28a260 bfebb1ad \
  7987649c 89faaaf7 a94240e2 f1cbbcf1 30e58586 42f7ce84 2a039760 \
  62f598e9 204b927c 332bcb75; do
  git log --format=%h -1 "$h" >/dev/null 2>&1 || echo "MISSING $h"
done
```

```bash
# Dead-end and backup branches still present
git branch --list 'backup/unbloat-*' attune-tasks-poc \
  agent-coordination 'feature/knowledge-brain' \
  'feat/slop-clean-before-post'
```

```bash
# Standing guards still in place
ls plugins/leyline/tests/test_python39_compat.py \
  plugins/abstract/hooks/shared/hook_io.py \
  scripts/check_pinned_versions.py scripts/check_ruff_version.py
rg -q "meta_path" plugins/gauntlet/tests/unit/test_challenges.py
rg -q "LLM_TIMEOUT_SECONDS < hook_timeout" \
  plugins/herald/tests/unit/test_double_shot_latte.py
```
