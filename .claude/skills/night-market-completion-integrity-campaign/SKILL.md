---
name: night-market-completion-integrity-campaign
description: Bind loop 'done' to unfakeable gates. Use to harden egregore/herald loops or promote completion_integrity. Not for QA gates; use night-market-validation-and-qa.
---

# Night Market Completion-Integrity Campaign

This is an executable campaign, phased and decision-gated, against the
hardest live problem in this repository: making "done" in autonomous
loops mean something the agent cannot fake, and earning the promotion
of `completion_integrity` from default-off to default-on. Every command
below was run against the repo on 2026-07-02 (v1.9.15) unless marked
candidate. Run the phases in order. Each phase ends at a gate with
expected observations and branch instructions.

## Definitions

| Term | Meaning |
|------|---------|
| Autonomous loop | A session that keeps working without a human turn: egregore's orchestrator (`/egregore:summon`), the externally installed ralph-wiggum loop, herald's auto-continue Stop hook |
| Stop hook | A Claude Code hook fired when the agent tries to end its turn. It prints `{"decision": "approve"}` (allow stop) or `{"decision": "block", "reason": ...}` (keep working) |
| Completion integrity | The property that a loop's "done" signal is bound to a verifier the agent does not control, instead of the agent's own say-so |
| False stop | The loop halts while verifiable work remains, or accepts a claimed completion that a check would have rejected |
| False continue | The loop keeps working (blocks the stop) on a turn that was genuinely finished |
| Verdict | The egregore quality-gate outcome: `pass`, `pass-with-warnings`, or `fix-required` (computed after a 3-attempt auto-fix loop) |

## Problem statement

Three assets exist today. None of them, alone, binds "done" to an
unfakeable gate:

| Asset | What it does | Default | Key commits |
|-------|--------------|---------|-------------|
| `plugins/egregore/scripts/config.py` field `PipelineConfig.completion_integrity` | When true, a `fix-required` verdict counts as a step failure (the item cannot reach `completed` with blocking findings) and merge is held for human review regardless of `auto_merge` | `False` | 83281337 (gate), cd903cbf (raw-JSON opt-in test) |
| `plugins/herald/hooks/double_shot_latte.py` (Stop hook) | Deterministic continue/stop judge over the last assistant message, with an opt-in LLM second shot for the single ambiguous outcome | Deterministic only | 268cff89 (timeout cap + gating) |
| `plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md` | The theory: a gate earns trust only if the spec is validated separately from the code and the check is proven able to fail | Prose guidance | 29081fda |

The load-bearing weakness, verified by reading commit 83281337: the
`completion_integrity` flag is real code with a tested load path, but
its enforcement lives in agent instructions
(`plugins/egregore/agents/orchestrator.md`, the `egregore:quality-gate`
skill, and `skills/summon/modules/pipeline.md`). No Python code path
blocks a pipeline transition. The manifest that records item status
(`.egregore/manifest.json`) is written by the same agent the gate is
supposed to bind. The campaign exists to close that gap with evidence.

## Evidence bar

Success is measured, never judged by eye. The standing rules are
drawn from two 2026-07-01 research passes, whose evidence now lives
in `.claude/rules/prefer-invariants-over-fallbacks.md` (harness-loop
findings) and
`plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md`
(verifier findings), plus the load-bearing claims inlined below:

- State the numbers a hypothesis predicts BEFORE running the
  measurement. A threshold chosen after seeing the data is not a gate.
- One mechanism must explain all observations, including the negative
  ones.
- Never let the generator be its own judge: LLM self-verification is
  measurably unreliable and self-critique can degrade output, so
  verdicts come from an independent verifier (prover-verifier
  separation, arXiv 2402.08115; see
  `plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md`).
- A green check proves spec satisfaction, never correctness. Every
  gate you add must itself be proven able to go red (verifier-integrity
  Guard 2: mutation or revert test).

## Campaign map

| Phase | Question it answers | Gate to pass |
|-------|--------------------|--------------|
| P0 | Do today's gate and judge suites pass as documented? | Exact pass counts reproduced |
| P1 | What does the gate log when enabled on real work? | Opt-in path exercised on a bounded item, logs captured |
| P2 | What are the false-stop and false-continue rates? | Pre-registered numbers met |
| P3 | Can the loop satisfy the gate without doing the work? | Refutation attempts run, holes documented or closed |
| P4 | Is the default flip earned? | Change control passed |

## P0: baseline the gate and judge suites

Gate: exact pass counts reproduced, running every suite from inside its
plugin directory.
Commands, expected observations and branch instructions:
`modules/p0-baseline.md`.

## P1: shadow observation, then opt-in on a bounded item

Gate: the opt-in path exercised on a bounded item, with its logs
captured. P1a reads verdicts in shadow, and P1b enables the gate on a
bounded run.
Commands, expected observations and branch instructions:
`modules/p1-shadow-and-opt-in.md`.

## P2: measure false-stop and false-continue rates

Gate: pre-registered numbers met. Write the thresholds down and date
them before measuring.
Commands, expected observations and branch instructions:
`modules/p2-measure-rates.md`.

## P3: adversarial self-test (design the refutation)

Gate: refutation attempts run, holes documented or closed. Attack A
talks past the herald judge, Attack B fakes the egregore manifest, and
Attack C mutation-proves every gate added.
Commands, expected observations and branch instructions:
`modules/p3-adversarial.md`.

## Solution menu, ranked

Ranked by fake-resistance. Each carries a theory obligation the
implementation must discharge.

1. Deterministic gate expansion (a). Grow the executable side of the
   verdict: convention checks, tests, lints, result artifacts that run
   outside the agent's narrative. Obligation: every check
   mutation-proven (Guard 2) and, where a property exists, asserted as
   a property rather than pinned examples (Guard 4). The principle
   from the harness research: the agent "can still cut a corner, it
   just can't cut this one past a check it doesn't control."
2. Separated verifier agent (b). A second session, with no access to
   the producer's reasoning, evaluates the diff against the acceptance
   criteria and returns localized findings. Obligation:
   prover-verifier separation (the generator never judges itself:
   LLM self-verification is measurably unreliable), localized feedback
   piped back for targeted repair, and a hard attempt cap after which
   the failure is reported instead of forced green. Status: candidate,
   no implementation in this repo yet.
3. LLM judge second shot (d). Acceptable only as a tiebreaker for a
   single ambiguous outcome, exactly as herald gates it: the LLM is
   consulted only when the deterministic verdict is the default-stop
   reason, its subprocess timeout stays strictly below the registered
   hook budget with a guard test, and a recursion-guard env var stops
   the judge's own Stop hook from spawning judges. Obligation: never
   let it override a confident deterministic verdict.
4. Human checkpoint (c). Hold the merge open for human review, which
   is what `completion_integrity` already does. Open question, on
   record in `.claude/rules/prefer-invariants-over-fallbacks.md`:
   whether the discipline of keeping a human judge survives competitive
   and security pressure is the contested point between Ronacher and
   his critics. Keep the human checkpoint as the backstop, and never
   count it as the automated gate.

## Known wrong paths (fenced off)

| Wrong path | Evidence | What happened |
|------------|----------|---------------|
| Subprocess timeout at or above the registered hook budget | 268cff89, and the guard test `test_llm_timeout_fits_within_hook_timeout` | herald's LLM call outlived the registered hook budget, so the harness killed the hook before it printed any decision at all (full record: night-market-failure-archaeology SB7). Cap child timeouts strictly below the registered budget and pin the relation with a test |
| Letting the generator judge its own output | arXiv 2402.08115, folded into `imbue:proof-of-work/verifier-integrity` | Self-verification is frequently no better than generation and self-critique can degrade output. Verdicts must come from an independent verifier |
| Assuming hook payloads arrive in env vars | CHANGELOG 1.9.14 ("Hooks read the tool payload from stdin, not unset env vars") | Hooks reading `CLAUDE_TOOL_*` were silent no-ops for months (full record: night-market-failure-archaeology SB9). Payload is JSON on stdin. Use `shared/hook_io.read_hook_payload` |
| Shipping an optional branch no test exercises | 268cff89 added 81 test lines for the LLM path | The deterministic suite was green while the opt-in LLM branch was broken by construction. Every opt-in branch needs at least one test that walks it |
| Treating "done" text as a completion gate | Attack A in `modules/p3-adversarial.md`, plus the harness research: a completion promise must pair with an iteration cap and manual abort | String-matched completion is trivially fakeable and herald proves it live |
| Prompt-only enforcement of a code-level guarantee | P1/P3 findings in this campaign | The flag flips real code, but nothing in code blocks the transition, so a non-compliant orchestrator defeats it. Move at least one enforcement point into a hook or script |

## P4: promotion through change control

Gate: change control passed. The default flip routes through
`night-market-change-control`.
Commands, expected observations and branch instructions:
`modules/p4-promotion.md`.

## When NOT to use

- Routine test, lint, or release execution: use
  `night-market-operations`.
- General evidence standards and coverage thresholds outside the loop
  problem: use `night-market-validation-and-qa`.
- Hook mechanics, timeouts, and registration syntax: use
  `claude-code-plugin-reference`.
- The history of why these guards exist (SB7, SB9, and friends): use
  `night-market-failure-archaeology`.
- Classifying and gating the promotion change itself: this skill
  routes there, but the authority is `night-market-change-control`.
- Open research directions beyond this campaign (for example
  hook-side manifest cross-checks as a general pattern): use
  `night-market-research-frontier`.

## Exit Criteria

- [ ] P0 pass counts reproduced from inside each plugin directory
      (egregore full suite, herald suite, imbue proof-of-work test) and
      all three herald smoke probes emit the documented JSON verdicts.
- [ ] P1b executed at least once: a bounded egregore run with
      `pipeline.completion_integrity` true, with the resulting
      `.egregore/manifest.json` captured as evidence.
- [ ] P2 thresholds written down and dated BEFORE the measurement
      runs, and the labeled data plus confusion matrix committed
      alongside the computed rates.
- [ ] P3 Attacks A and B executed with recorded outcomes, and every
      gate added during the campaign has a `[V1]`-format
      fake-resistance record showing a mutation went red.
- [ ] Promotion either completed through P4 (ADR merged, default
      flipped, docs and CHANGELOG updated, tests green) or explicitly
      parked with the blocking metric named in the ADR draft.
- [ ] No step of the campaign treated a Stop-hook approve or an
      agent's completion message as evidence of completed work.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15, branch state
discussions-fix-1.9.14. "Stopping and relaunch machinery" subsection
added to P1b on 2026-07-03. Volatile facts and how to re-verify them:

- Test pass counts (477 egregore, 27 config+quality, 13 config alone,
  105 herald, 17 imbue proof-of-work) date from 2026-07-02. Re-run the
  P0 commands and update this file when they drift.
- Gate implementation and defaults:
  `rg -n "completion_integrity" plugins/egregore/` should list
  config.py, test_config.py, orchestrator.md, quality-gate SKILL.md,
  pipeline.md, and README.md. A new hit means new enforcement surface
  to fold into P4 step 4.
- Herald timeout relation: `rg -n "LLM_TIMEOUT_SECONDS" \
  plugins/herald/hooks/double_shot_latte.py` (expect 8) and the
  `"timeout"` value in `plugins/herald/hooks/hooks.json` (expect 10).
- Herald judge env switches: `DOUBLE_SHOT_LATTE_LLM=1` enables the
  second shot, `DOUBLE_SHOT_LATTE_MODEL` picks the model (default
  `haiku`), `DOUBLE_SHOT_LATTE_MAX_CONTINUATIONS` overrides the cap of
  10 per 300-second window. Re-verify with
  `rg -n "os.environ" plugins/herald/hooks/double_shot_latte.py`.
- Stop and relaunch machinery: re-verify with
  `head -30 plugins/egregore/commands/dismiss.md`,
  `head -25 plugins/egregore/scripts/watchdog.sh` (manifest, budget,
  and pidfile paths), and
  `rg -n "startup|resume" plugins/egregore/hooks/hooks.json`
  (SessionStart matcher). Verified 2026-07-03.
- Key commits: `git show --stat 83281337 cd903cbf 268cff89 29081fda`.
- Research grounding: `.claude/rules/prefer-invariants-over-fallbacks.md`
  ("Evidence base" table) and
  `plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md`
  ("Reusable verifier techniques"). Both are tracked, so the citations
  resolve on a fresh clone.
- Highest ADR number: `ls docs/adr/ | sort | tail -1` (0017 as of
  compilation).
- Candidate items in this file (P2 thresholds and N values, the P2
  herald harness loop, the Attack B hook-side hardening, solution (b)
  verifier agent) are unproven by definition. Remove the label only
  with committed evidence.
