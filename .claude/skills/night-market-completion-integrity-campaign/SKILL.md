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

Run every suite from inside its plugin directory. Root pytest sets
`norecursedirs = plugins/*`, so running from the repo root silently
collects nothing (or raises `ImportPathMismatchError`). Every `cd`
in this skill is relative to the repo root: start each command block
from there.

```bash
cd plugins/egregore
uv run pytest tests/ -q
```

Expected (2026-07-02): `477 passed` in about 2 seconds, preceded by a
coverage table.

```bash
cd plugins/egregore
uv run pytest tests/test_config.py tests/test_quality_gate.py -q
```

Expected: `27 passed`. `tests/test_config.py` alone is `13 passed` and
includes the two completion-integrity guards:
`test_completion_integrity_opt_in_roundtrip` and
`test_completion_integrity_loads_from_raw_json` (the real user opt-in
path, added in cd903cbf. It also guards the field against silent
removal, because `_filter_fields` would drop the key).

```bash
cd plugins/herald
uv run pytest tests/ -q
```

Expected: `105 passed` in under 2 seconds. This suite contains
`test_llm_timeout_fits_within_hook_timeout`, which asserts
`LLM_TIMEOUT_SECONDS` (8) is strictly below the Stop-hook timeout
registered in `plugins/herald/hooks/hooks.json` (10).

```bash
cd plugins/imbue
uv run pytest tests/unit/skills/test_proof_of_work.py -q
```

Expected: `17 passed`. Note: imbue's pytest addopts force coverage
artifacts on every run. There is no dedicated test for the
verifier-integrity module itself (verified 2026-07-02 by grepping
`plugins/imbue/tests/` for `verifier-integrity`): the module is prose,
covered only by the skill-structure test above.

Smoke-test the herald judge directly. All three probes below were run
and their outputs captured verbatim on 2026-07-02:

```bash
echo '{"session_id":"probe","transcript_path":"/nonexistent"}' \
  | python3 plugins/herald/hooks/double_shot_latte.py
```

Expected:

```json
{"decision": "approve", "reason": "Double Shot Latte: No transcript available; allowing stop."}
```

```bash
D=$(mktemp -d)
printf '%s\n' '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Now let me fix the failing tests."}]}}' \
  > "$D/t.jsonl"
echo "{\"session_id\":\"p1\",\"transcript_path\":\"$D/t.jsonl\"}" \
  | python3 plugins/herald/hooks/double_shot_latte.py
```

Expected:

```json
{"decision": "block", "reason": "Double Shot Latte: Assistant stated explicit intent to keep working."}
```

Gate P0 branches:

- Pass counts lower than stated, or any failure: the repo has drifted
  since 2026-07-02. Stop the campaign. Triage with
  `night-market-debugging-playbook`, then update the counts in this
  skill's Provenance section before proceeding.
- `ImportPathMismatchError` or `no tests ran`: you ran pytest from the
  wrong directory. Re-run from inside the plugin.
- Hook probe emits nothing or a traceback: the hook contract is broken
  (it must always exit 0 and print a decision). That is a P0 incident,
  not a campaign step. File it.

## P1: shadow observation, then opt-in on a bounded item

### P1a: shadow read (no behavior change)

Verdicts are recorded in the manifest even with the flag off (the
`egregore:quality-gate` skill records every verdict as a decision entry
`{"step": ..., "chose": ..., "why": ...}`). So the flag-off world
already contains the shadow data: items that advanced to `completed`
despite a `fix-required` verdict. Count them in any repo where egregore
has run:

```bash
python3 - <<'EOF'
import json
from pathlib import Path

path = Path(".egregore/manifest.json")
if not path.exists():
    print(json.dumps({"error": "no manifest; egregore has not run here"}))
    raise SystemExit(0)
data = json.loads(path.read_text())
items = data.get("work_items") or data.get("items") or []
flagged = [
    {"id": i.get("id"), "status": i.get("status")}
    for i in items
    if any(d.get("chose") == "fix-required" for d in i.get("decisions", []))
]
print(json.dumps(
    {"total_items": len(items), "items_with_fix_required": flagged},
    indent=2,
))
EOF
```

Expected: a JSON summary. Any entry with `"status": "completed"` in
`items_with_fix_required` is a shadow-mode false completion: the exact
event the gate exists to prevent. Record the count as the P2 baseline.

Branch: no manifest exists in this repo's root (egregore is typically
summoned in target repos, and `.egregore/` state lives where it ran).
If you have no manifest anywhere, skip to P1b and generate one.

### P1b: enable the gate on a bounded run

The opt-in path is hand-editing the config JSON. This exact shape is
what `test_completion_integrity_loads_from_raw_json` covers:
unspecified pipeline fields keep their defaults.

```bash
mkdir -p .egregore
cat > .egregore/config.json <<'EOF'
{"pipeline": {"completion_integrity": true}}
EOF
```

Warning: if `.egregore/config.json` already exists, edit the existing
`pipeline` object instead of overwriting the file, or you will reset
overseer and alert settings to defaults.

Then run a small, disposable work item in bounded mode (bounded mode
stops when the time window expires, so the loop cannot run away while
you observe):

```
/egregore:summon "<one small, well-specified task>" --bounded --window 5h
```

Before summoning, read "Stopping and relaunch machinery" at the end
of this section: bounded mode expires on its own, but the watchdog
and SessionStart hook can still resurrect the loop.

What it logs and where:

- `.egregore/manifest.json`: per-item `status` (`active`, `paused`,
  `pending` count as unfinished for the Stop hook, while `completed`
  and `failed` are terminal), `attempts`, `max_attempts` (default 3),
  and the `decisions` array holding each quality verdict.
- `.egregore/relaunch-prompt.md`: the re-injection prompt the egregore
  Stop hook (`plugins/egregore/hooks/stop_hook.py`) uses when it blocks
  an exit with active work remaining.
- Overseer alerts per `.egregore/config.json` (`pipeline_failure`
  fires when an item exhausts attempts).

Expected observations with the flag on, per the documented contract in
`plugins/egregore/skills/quality-gate/SKILL.md` and
`agents/orchestrator.md`:

1. A `fix-required` verdict routes to failure handling: the item
   retries in place, and after `max_attempts` it is marked `failed`
   with the overseer alerted. It is never silently `completed`.
2. Merge is held for human review regardless of `auto_merge`: the PR
   is prepared but left open.
3. The loop itself does not halt: it continues with the next active
   item.

Gate P1 branches:

- An item reaches `completed` with an unresolved `fix-required`
  decision while the flag is true: the orchestrator ignored its
  instructions. This confirms the prompt-level enforcement gap in the
  problem statement. Record the manifest as evidence and carry it into
  P3. The finding argues for solution (a) or (b) below, which move
  enforcement out of the prompt.
- The item loops in retry forever: `max_attempts` is not being
  incremented. That is an orchestrator bug, not a gate result. File it
  with the manifest attached.

#### Stopping and relaunch machinery

Know the stop path before you summon. The loop runs indefinitely by
default and never stops on its own
(`plugins/egregore/commands/dismiss.md`).

- `/egregore:dismiss` is the only sanctioned stop. It pauses all
  active items in the manifest, cancels the orchestrator's cron jobs,
  and removes the pidfile (`.egregore/pid`).
- The pidfile is what the watchdog daemon polls. If
  `/egregore:install-watchdog` has run on the machine,
  `plugins/egregore/scripts/watchdog.sh` fires every 5 minutes via
  launchd or systemd and relaunches a session whenever the manifest
  has unfinished work, the budget allows it, and no pidfile marks a
  live session. Killing a session without dismissing therefore gets
  you silently relaunched sessions.
- A SessionStart hook (matcher `startup|resume` in
  `plugins/egregore/hooks/hooks.json`) auto-resumes orchestration in
  new and resumed sessions while egregore state is active. Closing
  the terminal is not a stop either.
- `.egregore/budget.json` bounds spend. The watchdog checks it before
  relaunching, so an exhausted budget halts relaunches even without a
  dismiss.

## P2: measure false-stop and false-continue rates

Fix the acceptance numbers before running anything. The numbers below
are candidates recorded at authoring time. Whoever executes P2 must
confirm or amend them, in writing, before the first measurement run.

| Metric | Definition | Candidate gate |
|--------|-----------|----------------|
| Egregore false completions | Items `completed` with an unresolved `fix-required` verdict, flag on | 0 over N >= 20 work items |
| Egregore false failures | Items `failed` whose findings a human reviewer judges non-blocking | <= 2 of 20 (candidate) |
| Herald false continue | Judge blocks a stop on a turn a human labels finished | <= 5% over N >= 30 labeled transcripts (candidate) |
| Herald false stop | Judge approves a stop on a turn with explicit stated intent to continue | <= 10% over the same set (candidate) |

The asymmetry is deliberate: herald's false continue burns tokens and
nags a finished session, while its false stop merely hands control to
the human. The judge is biased to stop by design, so tolerate more
false stops than false continues.

Herald measurement harness (candidate, offline and read-only): collect
real session transcripts, hand-label the final assistant message of
each as finished / awaiting-user / continuing, then score the
deterministic judge against the labels:

```bash
for t in "$HOME"/.claude/projects/*/*.jsonl; do
  verdict=$(printf '{"session_id":"m","transcript_path":"%s"}' "$t" \
    | python3 plugins/herald/hooks/double_shot_latte.py)
  echo "$t $verdict"
done
```

Notes for the harness: the event omits `stop_hook_active`, so the
throttle counter is not consulted, and `DOUBLE_SHOT_LATTE_LLM` unset
keeps the run deterministic and network-free. Compute the confusion
matrix against your labels by hand or with a 20-line script. Commit the
labeled set alongside the numbers so the measurement is reproducible.

Egregore measurement: repeat P1b across N >= 20 items (candidate N) and
tally the manifest with the P1a script. Do not curate which items go
in. Take a contiguous slice of real backlog.

Gate P2 branches:

- Numbers met: proceed to P3.
- Herald false-continue rate blows the gate: inspect which
  `_CONTINUE_PATTERNS` regex fired on finished turns and tighten it.
  That is deterministic gate expansion, solution (a); re-run the same
  labeled set after the change.
- Egregore false completions are nonzero: enforcement is not binding.
  Do not tune thresholds to pass. Go to P3 and then to solution (a) or
  (b).

## P3: adversarial self-test (design the refutation)

The question: can the loop satisfy the gate without doing the work? Run
each attack, record the result, and either close the hole or document
it as accepted residual risk with an owner.

### Attack A: talk your way past the herald judge

Verified on 2026-07-02: a transcript whose final assistant message is
"Everything is done and verified, tests passing green." gets

```json
{"decision": "approve", "reason": "Double Shot Latte: Assistant signaled the work is complete."}
```

with zero checks run. The judge is a conversation-state classifier over
the last 800 characters of assistant text (`TAIL_CHARS`), by design. It
answers "does the agent intend to continue?", never "is the work
actually done?". Conclusion, standing: herald's verdict must never be
used as completion proof. Any design that treats a Stop-hook approve as
evidence of completion fails this attack by construction.

### Attack B: fake the egregore manifest

With `completion_integrity` true, hand-edit one work item in
`.egregore/manifest.json` from `active` to `completed` while its
decisions still contain a `fix-required`. Then feed the egregore Stop
hook a stop event:

```bash
echo '{}' | python3 plugins/egregore/hooks/stop_hook.py
```

Expected (run from a directory whose walk-up finds that manifest): the
hook checks only `status in ("active", "paused", "pending")` via
`has_active_work` and prints `{"decision": "approve"}`. Nothing
cross-checks decisions against status. This demonstrates the residual
hole: the manifest is agent-writable state, so an orchestrator that
lies in the manifest defeats the gate. Candidate hardening (unbuilt):
teach the Stop hook to refuse `completed` status on items whose most
recent quality decision is `fix-required`, which moves one enforcement
point out of the prompt and into code the agent does not author
mid-loop. Treat that as a P4 prerequisite discussion item, not a given.

### Attack C: mutation-prove every gate you add

Any new deterministic check earns trust only by going red on a real
break (verifier-integrity Guard 2). For each check added during this
campaign, record evidence in the module's format:

```markdown
[V1] Check: <the test or gate>
     Encodes requirement: <observable behavior, stated from intent>
     Fake-resistance: <mutation applied> -> <check went RED: yes/no>
     Independence: <executable / who verified>
     Passing run: <command + output reference>
```

A single surviving mutation is a hole in the gate, not a rounding
error.

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
| Treating "done" text as a completion gate | Attack A above, plus the harness research: a completion promise must pair with an iteration cap and manual abort | String-matched completion is trivially fakeable and herald proves it live |
| Prompt-only enforcement of a code-level guarantee | P1/P3 findings in this campaign | The flag flips real code, but nothing in code blocks the transition, so a non-compliant orchestrator defeats it. Move at least one enforcement point into a hook or script |

## P4: promotion through change control

Flipping `completion_integrity` to default-on changes the documented
posture of every egregore deployment. It routes through
`night-market-change-control`. Do not shortcut it.

Preconditions, all required:

- [ ] P2 numbers met at the pre-registered thresholds, raw data
      committed.
- [ ] P3 attacks run, with Attack B either closed by a code-side check
      or formally accepted in the ADR with an owner.
- [ ] The promotion decision drafted as a numbered ADR in `docs/adr/`
      (next free number: ADR-0017 is the highest as of 2026-07-02),
      because this reverses a deliberate recorded default.

Implementation order (Iron Law: failing test first):

1. Branch per convention: `<topic>-<version>`, from `master`.
2. Turn the default's tests red first: in
   `plugins/egregore/tests/test_config.py`, change
   `test_pipeline_defaults` to expect `completion_integrity is True`
   and run it. Expected: 1 failure, proving the test binds the default.
3. Flip the default in `plugins/egregore/scripts/config.py`
   (`PipelineConfig.completion_integrity: bool = True`) and re-run:

   ```bash
   cd plugins/egregore
   uv run pytest tests/test_config.py tests/test_quality_gate.py -q
   ```

4. Update every document that states the default is off. Verified
   list as of 2026-07-02 (re-derive with the rg command in Provenance):
   `plugins/egregore/scripts/config.py` (comment),
   `plugins/egregore/tests/test_config.py` (comment),
   `plugins/egregore/agents/orchestrator.md`,
   `plugins/egregore/skills/quality-gate/SKILL.md`,
   `plugins/egregore/skills/summon/modules/pipeline.md`,
   `plugins/egregore/README.md`.
5. Add a CHANGELOG entry under `[Unreleased]` in Keep a Changelog
   format. Never rewrite historical entries.
6. Check the diff against the 200-line AI-commit cap (CONSTITUTION
   rule 2). The code flip is tiny, but the doc sweep plus ADR may
   exceed it: if so, the ADR itself is the required planning doc;
   reference it in the commit body.
7. Run the standard gates before committing (`make lint`,
   `make typecheck`, plugin tests) and follow the PR flow in
   `night-market-operations`.

Rollback: the flag remains user-overridable either way
(`{"pipeline": {"completion_integrity": false}}` in
`.egregore/config.json`), so promotion is reversible per-deployment
without a code change. State this in the ADR.

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
