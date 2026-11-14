---
name: night-market-research-frontier
description: Map open problems where this repo can advance SOTA. Use when scoping research. Do not use to run the campaign; use night-market-completion-integrity-campaign.
---

# Night Market Research Frontier

This file lists the open problems where this repository holds assets
that the published state of the art does not. SOTA (state of the art)
here means the best result shipped or published anywhere, not the best
result in this repo. Every entry is a candidate. Nothing below is a
claimed capability, and citing this file as evidence that a capability
exists is an error.

Read this skill when choosing what research bet to place next, when
framing an experiment, or when someone asks "what could this project
contribute beyond itself?"

## Ground rules

Follow these before starting any problem below.

- Everything here stays labeled open or candidate until it clears the
  repo evidence bar: one mechanism must explain all observations
  including negatives, the hypothesis must predict numbers before the
  run, and the generator is never its own judge. The pipeline from
  hunch to accepted result is night-market-research-methodology.
- Experiments are changes. They go through the same gates as any other
  change (night-market-change-control). This skill authorizes no
  shortcuts.
- When a problem produces an accepted result, write the dated synthesis
  in `docs/research/`, update the changelog, and remove or re-scope the
  entry here. A frontier list that never shrinks is a wish list.

## Problem index

| # | Problem | Primary repo asset | Status |
|---|---------|--------------------|--------|
| 1 | Completion integrity in autonomous loops | egregore gate + herald judge + imbue verifier-integrity | Open, active campaign |
| 2 | Skill-graph governance at scale | ratchets + skill graph (activation harness removed) | Open |
| 3 | Collective memory across context resets | ADR-0007 Discussions + memory-palace | Open, partially blocked |
| 4 | Insight-palace bridge under a hook budget | Draft spec v0.1.0 + hook infrastructure | Open, spec drafted |
| 5 | Behavioral contract attestation | ADR-0008 SLSA path + trust workflow | Open |
| 6 | Continuation for autonomous loops | egregore night-run driver + watchdog + bounded Stop hook | Open, cost baseline measured |

Each problem's full write-up (why current SOTA fails, this repo's asset,
the first three steps, and what counts as a result) is in
`modules/problems.md`. Load it after picking a row from the index.

## What beyond-SOTA means here

Inferred from the project's own research docs, and labeled as
inference: the ambition is harness-level guardrails that keep
autonomous loops honest and legible. The six problems above are one
thread: gates the agent cannot fake (1), a skill library whose
activation is measured rather than hoped (2), memory that survives
resets and proves its retrieval (3), cross-plugin composition under
hard budgets (4), trust signals that cover behavior, not bytes (5),
and a loop that continues on a mechanism meant to carry it (6).
Advancing any one of them past its milestone is a contribution the
wider agent-tooling field does not yet have.

## When NOT to use

- Executing the completion-integrity work: use
  night-market-completion-integrity-campaign, which owns the runnable
  plan. This entry only frames the research question.
- Running the hunch-to-result process for any experiment: use
  night-market-research-methodology.
- Looking up what already failed and was settled: use
  night-market-failure-archaeology. Do not reopen settled battles as
  "research."
- Day-to-day test/lint/release commands: use night-market-operations.
- Understanding the invariants an experiment must not break: use
  night-market-architecture-contract.

## Exit Criteria

- [ ] A specific problem number (1 to 6) was chosen and its listed
      first three steps were either started as written or a documented
      deviation exists in the work log or PR description.
- [ ] Any claimed result names its "you have a result when" milestone
      and shows the milestone's check passing (numbers, test output,
      or merged artifact).
- [ ] No statement from this file was cited as evidence of a shipped
      capability, and every borrowed claim kept its open/candidate
      label.
- [ ] The experiment's changes passed the normal gates (failing test
      first for plugin Python, pre-commit clean, no bypass flags).
- [ ] If a result was accepted, a dated synthesis exists in
      `docs/research/` and this file's entry was updated or removed.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 (branch
discussions-fix-1.9.14). Problem 6 was added 2026-08-23 against branch
fix/minimax-cli-contract. Volatile facts and how to re-verify them:

- Skill count (198 SKILL.md files, 2026-07-02):
  `find plugins -name SKILL.md | wc -l`
- egregore gate default (off, 2026-07-02):
  `rg -n "completion_integrity" plugins/egregore/scripts/config.py`
- herald LLM timeout (8s, 2026-07-02):
  `rg -n "LLM_TIMEOUT_SECONDS" plugins/herald/hooks/double_shot_latte.py`
- Insight-palace spec still current (Draft v0.1.0, 2026-04-13):
  `head -5 docs/specification.md`
- Stop-hook budget (8.5s):
  `rg -n "_BUDGET_SECONDS" plugins/abstract/hooks/post_learnings_stop.py`
- Issue states (#574 open, #553 open, 2026-07-02):
  `gh issue view 574 --json state -q .state` (same for 553)
- Pensive verdict-scaffold duplication (7 files, 2026-07-02):
  `rg -l "Approve with actions" plugins/pensive/skills/*/SKILL.md | wc -l`
- Discovery-budget note:
  `rg -n "16K characters" docs/quality-gates.md`
- Stop-hook stall bound (default 3, 2026-08-23):
  `rg -n "DEFAULT_MAX_STALLS" plugins/egregore/hooks/stop_hook.py`
- ralph-wiggum's iteration bound (2026-08-23, plugin 1.0.0):
  `rg -n "MAX_ITERATIONS" ~/.claude/plugins/cache/claude-code-plugins/ralph-wiggum/1.0.0/hooks/stop-hook.sh`
- Commits cited: 83281337, cd903cbf, 29081fda, 3d22f02a, 268cff89,
  5683e89b. Re-verify with `git log --oneline -1 <hash>`.

Unverified in this compilation: the exact 16K-character discovery
budget figure is the repo's own estimate ("about 16K characters" in
docs/quality-gates.md), not an upstream-documented limit. The claim
that no published activation-quality metric exists is a
literature-absence claim as of 2026-07-02. Re-check before publishing
externally.
