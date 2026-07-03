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
| 2 | Skill-graph governance at scale | forced-eval activation harness + ratchets | Open |
| 3 | Collective memory across context resets | ADR-0007 Discussions + memory-palace | Open, partially blocked |
| 4 | Insight-palace bridge under a hook budget | Draft spec v0.1.0 + hook infrastructure | Open, spec drafted |
| 5 | Behavioral contract attestation | ADR-0008 SLSA path + trust workflow | Open |

## 1. Completion integrity in autonomous loops

### Why current SOTA fails

Autonomous agents self-report "done." The repo's two research
syntheses (`docs/research/2026-07-01-the-coming-loop-agentic-harness-guardrails.md`
and `docs/research/2026-07-01-prover-verifier-loops-formal-verification.md`;
note that `docs/research/` is gitignored and machine-local, so these
files are absent on fresh clones and the load-bearing claims are
inlined here) collect the evidence: the METR randomized trial
(arXiv 2507.09089)
found experienced developers 19% slower with AI while believing they
were faster, so self-assessment of completion is miscalibrated even
for humans in the loop. On the verifier side, a green check proves
spec-satisfaction, not correctness: the spec can be wrong, or the
check can be hollow (a test that passes no matter what the code does).
An agent that judges its own work optimizes the judge, not the work.
No published harness binds "done" to gates the agent cannot fake.

### This repo's specific asset

Three shipped, tested mechanisms that most agent frameworks lack:

- egregore's opt-in completion-integrity gate:
  `completion_integrity: bool = False` in
  `plugins/egregore/scripts/config.py` (commit 83281337, default off).
  When true, a "fix-required" quality verdict blocks the ship step and
  merge is held for human review regardless of `auto_merge`. The
  raw-JSON opt-in path is covered by tests (commit cd903cbf).
- herald's deterministic-first Stop-hook judge:
  `plugins/herald/hooks/double_shot_latte.py`. Deterministic verdict by
  default. An optional LLM second shot fires only on the single
  ambiguous outcome and is capped at `LLM_TIMEOUT_SECONDS = 8` inside
  the 10s registered hook budget (commits 3d22f02a, 268cff89).
- imbue's verifier-integrity module:
  `plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md`
  (commit 29081fda): proves the check was worth passing, distinct from
  proving it passed.

### First three steps in this repo

1. Read the executable plan in
   night-market-completion-integrity-campaign. That skill owns the
   campaign. This entry only frames the research question.
2. Run egregore on a small manifest with the gate on (raw-JSON opt-in,
   `completion_integrity: true`) and again with it off, on the same
   work items. Log every quality verdict.
3. Compare false-done rates: items the ungated loop shipped that the
   gated loop held as fix-required, adjudicated by a human.

### You have a result when

A measured false-done rate delta between gated and ungated runs on the
same work items exists, with the human adjudication recorded, and the
delta survives a second run. If the delta is zero or the gate holds
only items a human calls genuinely done, the gate as designed is
falsified: record that too. The promotion question (default-off to
default-on) is open until this number exists.

## 2. Skill-graph governance at scale

### Why current SOTA fails

This repo carries 197 registered skills (198 SKILL.md files on disk,
find count 2026-07-02) against a finite skill discovery budget of
about 16K characters. Skills past the budget are dropped silently
(`docs/quality-gates.md`, Follow-on work section). The activation
layer does near-keyword matching, so relevant skills fail to fire
(`prototypes/forced-eval/README.md`). No one, here or elsewhere, has
published a principled activation-quality metric: a way to say "this
skill library activates the right skill X% of the time, and change Y
moved that number."

### This repo's specific asset

- An activation-lift measurement harness:
  `prototypes/forced-eval/measure_activation.py` (commit 5683e89b).
  It runs labeled prompts through `claude -p` with and without a
  forced-eval hook, counts expected `Skill()` events, tracks
  false activations on true-negative cases, and applies a paired
  McNemar significance test. The dataset
  (`prototypes/forced-eval/activation_cases.json`) is deliberately
  small. The README says to expand it before trusting the rates.
- Ratchets that already hold the graph steady:
  `scripts/check_skill_graph_drift.py` (dangling Skill() refs) and
  `scripts/check_skill_exit_criteria_drift.py`.
- A role taxonomy (entrypoint / library / hook-target) in
  `docs/skill-integration-guide.md`.
- ADR-0015 (usage-data gates before simplifying over-built skills)
  and the issue #574 backlog: 9 pensive review-named skills, of which
  at least 5 repeat the same "Approve / Approve with actions / Block"
  verdict scaffold (`rg -l "Approve with actions"
  plugins/pensive/skills/*/SKILL.md` matches 7 files, 2026-07-02).

### First three steps in this repo

1. Expand `prototypes/forced-eval/activation_cases.json` with labeled
   positive and true-negative prompts for the pensive review skills.
2. Baseline: run the harness dry, then live.

   ```bash
   cd prototypes/forced-eval
   uv run python measure_activation.py            # dry run, spends nothing
   uv run python measure_activation.py --live \
       --root "$PWD/../../plugins/pensive" --repeats 3
   ```

3. Consolidate `pensive:shell-review` and `pensive:makefile-review`
   into `pensive:unified-review` as modules (issue #574 item 1, one PR
   per skill, thin command alias stubs kept), then re-run step 2.

### You have a result when

A measured activation-lift delta exists for the pensive consolidation:
activation rate on the labeled set before versus after, with McNemar
significance, plus the discovery-budget character count saved. A
result where consolidation saves budget without degrading activation
is publishable. A result where activation drops is the falsification
and blocks further consolidation. Candidate follow-on, unproven: turn
the harness into a CI gate for any skill-count change.

## 3. Agent collective memory across context resets

### Why current SOTA fails

Published agent-memory work centers on single-agent vector stores.
Retrieval precision is rarely measured, and nothing binds memory to a
team of agents whose contexts reset constantly. The failure mode is
documented in this repo's own history: the abstract Stop hook that
posts daily [Learning] digests read env vars Claude Code never sets
and was a silent no-op for months (fixed in 1.9.14 via the shared
stdin-first payload reader). Memory systems fail silently, and nobody
notices until the knowledge is needed.

### This repo's specific asset

- ADR-0007: GitHub Discussions as shared agent memory, written by
  distributed plugin hooks through leyline GraphQL wrappers. The
  `gh discussion` subcommand does not exist, so all access is
  `gh api graphql`.
- A promotion pipeline:
  `plugins/memory-palace/skills/knowledge-intake/modules/discussion-promotion.md`
  routes reviewed Discussions knowledge into palace storage.
- `plugins/memory-palace/skills/memory-clarity-probe/SKILL.md`: dual
  anchor questions probing whether a summary preserves task progress
  and information gaps across a handoff.
- The digest producer itself:
  `plugins/abstract/hooks/post_learnings_stop.py`.

### Open blockers

- Retrieval precision over the Discussions corpus is unmeasured.
- The RL training path for the memory-clarity probe is blocked on
  logprob access (issue #553, open as of 2026-07-02).

### First three steps in this repo

1. Build a labeled retrieval set: sample 30 to 50 existing [Learning]
   and [Knowledge] discussions via `gh api graphql`, and for each
   write 1 to 2 queries a future session would plausibly ask.
2. Measure `memory-palace:knowledge-locator` precision and recall
   against that set. Record the numbers in a dated
   `docs/research/` synthesis.
3. Instrument the promotion pipeline: log how often promoted knowledge
   is retrieved within 30 days, versus knowledge left in Discussions.

### You have a result when

Precision and recall numbers exist for a labeled query set, and one
curation change (for example, promoting versus not promoting a batch)
produces a predicted, then measured, retrieval delta. Issue #553
unblocks a stronger result (an RL-trained clarity probe), but the
retrieval measurement does not wait on it.

## 4. Insight-palace bridge under a hard hook budget

### Why current SOTA fails

Plugin ecosystems either share a runtime registry (tight coupling) or
do not exchange data at all. ADR-0001 forbids a shared registry here:
plugins detect each other via the filesystem and degrade gracefully.
Moving structured findings between two isolated plugins inside a
Stop hook's hard latency budget, with graceful failure when the peer
plugin is absent, is an unsolved composition problem, and hook-budget
overruns are a known repo failure class (herald's LLM timeout once
exceeded its registered budget and the harness killed the hook with no
verdict at all).

### This repo's specific asset

A drafted, unimplemented specification: `docs/specification.md`
(Insight-Palace Bridge, v0.1.0, Draft, 2026-04-13), with
`docs/project-brief.md` and `docs/implementation-plan.md`. Key
verified constraints:

- The Stop hook budget is 8.5s: `_BUDGET_SECONDS = 8.5` in
  `plugins/abstract/hooks/post_learnings_stop.py`, leaving headroom
  inside the 10s hook timeout.
- AC-3.1: ingestion of up to 10 findings completes in under 500ms.
- AC-3.2: the bridge checks remaining budget and skips if less than
  1s remains. AC-3.4: it never raises to the caller.
- Cross-plugin absence is handled by an ImportError guard
  (`_HAS_INSIGHT_ENGINE`): with memory-palace or the insight engine
  missing, the bridge silently does nothing.

Caution: the brief, specification, and implementation plan under
`docs/` are overwritten per feature cycle. Confirm the spec on disk is
still the insight-palace bridge before building against it.

### First three steps in this repo

1. Read `docs/specification.md` and `docs/implementation-plan.md` end
   to end, and confirm the Draft status and version are unchanged.
2. Implement the bridge script per TR-1 with the
   `_HAS_INSIGHT_ENGINE` guard and the remaining-budget check, tests
   first (Iron Law applies).
3. Add a timing test proving AC-3.1 (10 findings under 500ms) and a
   test proving the ImportError path is a silent no-op, using a
   `sys.meta_path` import blocker as the existing hook regression
   tests do.

### You have a result when

The bridge is merged with both tests green, a benchmark artifact shows
10-finding ingestion under 500ms on CI hardware, and the spec's status
line moves from Draft. Falsification: if the 500ms budget cannot be
met without dropping findings, that is a spec revision, not a reason
to remove the budget check.

## 5. Behavioral contract attestation for plugin marketplaces

### Why current SOTA fails

Supply-chain attestation (SLSA provenance, signed via Sigstore) proves
which bytes came from which workflow. It does not prove what the
artifact does. ADR-0008 states the gap directly: there is no mechanism
to prove that a plugin's behavioral contract holds. A marketplace can
today verify a plugin is unmodified and still ship a plugin whose
hooks do something other than what its README claims. SLSA is the
state of the art for artifacts. Behavior verification has no SOTA
to beat, only a vacancy.

### This repo's specific asset

- ADR-0008 (Accepted, self-superseded 2026-03-15: the ERC-8004
  blockchain path was dropped for cost in favor of GitHub
  Attestations/SLSA).
- A live attestation pipeline: `.github/workflows/trust-attestation.yml`
  runs `make test` on master pushes and produces a signed SLSA
  attestation of `trust-report.json`.
- A consumer: the `leyline:verify-plugin` command
  (`plugins/leyline/commands/verify-plugin.md`) checks a plugin's
  attestation history.

### First three steps in this repo

1. Define what `trust-report.json` would need to assert for behavior,
   not provenance: candidate schema is per-hook contract tests (input
   payload, expected verdict/exit) whose pass results are attested.
2. Add one behavioral contract test to the trust report for a single
   hook (herald's Stop-hook judge is the best-instrumented candidate)
   and attest it through the existing workflow.
3. Extend `leyline:verify-plugin` to compare the attested behavioral
   claims against the plugin currently on disk and flag divergence.

### You have a result when

`leyline:verify-plugin` distinguishes, in a test, a plugin whose
attested behavior diverged from an unmodified one. Candidate and
unproven beyond that: whether behavioral attestation generalizes past
hooks (skills and agents are prose, with no test harness for their
behavior yet). Label any generalization claim open until one exists.

## What beyond-SOTA means here

Inferred from the project's own research docs, and labeled as
inference: the ambition is harness-level guardrails that keep
autonomous loops honest and legible. The five problems above are one
thread: gates the agent cannot fake (1), a skill library whose
activation is measured rather than hoped (2), memory that survives
resets and proves its retrieval (3), cross-plugin composition under
hard budgets (4), and trust signals that cover behavior, not bytes
(5). Advancing any one of them past its milestone is a contribution
the wider agent-tooling field does not yet have.

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

- [ ] A specific problem number (1 to 5) was chosen and its listed
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
discussions-fix-1.9.14). Volatile facts and how to re-verify them:

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
- Commits cited: 83281337, cd903cbf, 29081fda, 3d22f02a, 268cff89,
  5683e89b. Re-verify with `git log --oneline -1 <hash>`.

Unverified in this compilation: the exact 16K-character discovery
budget figure is the repo's own estimate ("about 16K characters" in
docs/quality-gates.md), not an upstream-documented limit. The claim
that no published activation-quality metric exists is a
literature-absence claim as of 2026-07-02. Re-check before publishing
externally.
