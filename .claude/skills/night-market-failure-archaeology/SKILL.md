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
  and a note in the collective memory.

## How to use this chronicle

1. Before implementing, scan the battle titles and the recurring-class
   table for anything resembling your plan.
2. If a battle matches, read its lesson. Follow it, or write down why
   this time is different before overriding it.
3. Verify any hash you rely on: `git log --format='%h %s' -1 <hash>`.
4. When your own battle settles, add an entry (format at the bottom).

## Settled battles

SB1 to SB15, each with what was tried, why it failed, and the guard that
now holds, are in `modules/settled-battles.md`. Load it when a proposed
fix resembles one of the classes below.

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
