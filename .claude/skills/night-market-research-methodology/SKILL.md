---
name: night-market-research-methodology
description: "Turn hunches into accepted results: worthiness score, evidence bar, research-to-rules. Use when vetting ideas. Not for QA; use night-market-validation-and-qa."
---

# Night Market Research Methodology

The discipline that turns a hunch into an accepted result in this
repo. An "accepted result" is a change that survived the evidence bar
and landed through change control as a rule, a skill module, a config
gate, or an ADR. Everything else is either a local working note or a
documented retirement. This skill covers the full path: score the
idea, experiment behind a default-off flag, meet the evidence bar,
land the durable artifact, or retire the idea on the record.

## The evidence bar

A claim graduates from hunch to result only when it passes all four
tests.

1. **One mechanism explains all observations, including negatives.**
   If the hypothesis explains the three failing cases but not why the
   fourth case passed, it is incomplete. Keep digging until a single
   mechanism accounts for everything you saw.

2. **Predict numbers before running.** Write down the expected
   measurement first, then measure. In-repo anchor: the forced-eval
   harness labels expected activations in
   `prototypes/forced-eval/activation_cases.json` before any run,
   then compares baseline against treatment with a McNemar paired
   test (a significance test for paired binary outcomes).

3. **Survive assigned adversarial refutation.** Assign a reviewer or
   agent whose explicit job is to break the claim. Use
   `Skill(attune:war-room)` for hard-to-reverse decisions and
   `Skill(imbue:rigorous-reasoning)` to counter agreement bias. A
   claim nobody tried to break is unproven.

4. **Never let the generator judge itself.** The agent that produced
   the work must not be its sole verifier. See
   `plugins/imbue/skills/proof-of-work/modules/independent-verification.md`.
   Prefer executable checks over an LLM judge, and prove the check
   can fail before trusting it (Guards 2 and 3 in
   `plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md`).

Corollary from verifier-integrity: a green check proves the code
satisfies the spec as written. It cannot prove the spec says what you
meant, and it proves nothing if the check cannot fail. Validate the
spec separately from the code, and mutation-test the check itself.

## Idea lifecycle

An idea moves through four gates in order. Skipping a gate is how
speculative infrastructure gets built and reverted.

### Gate 1: score worthiness before building

Formula and thresholds from `docs/backlog/queue.md` (a local,
gitignored working file):

```
Worthiness = (Business Value + Time Criticality + Risk Reduction)
           / (Complexity + Token Cost + Scope Drift)
```

| Score | Action |
|-------|--------|
| > 2.0 | Implement now |
| 1.0 to 2.0 | Discuss before proceeding |
| < 1.0 | Keep in backlog |

Queue rules: at most 10 active items. Items untouched for 30 days are
archived to a GitHub issue (labels `backlog,deferred`) and removed
from the queue. Because `docs/backlog/` and `docs/research/` are
gitignored, the durable record of a deferred idea is the issue, not
the queue file.

### Gate 2: experiment behind a default-off flag

Exemplar: the egregore completion-integrity gate.

- Commit `83281337` added the gate with
  `completion_integrity: bool = False` in
  `plugins/egregore/scripts/config.py` (still False as of
  2026-07-02).
- Commit `cd903cbf` added a test covering the raw-JSON opt-in path.

Pattern: land the mechanism off by default, cover the opt-in path
with a test, and collect usage before proposing a default change.

### Gate 3: data-collection window before structural change

ADR-0015 (`docs/adr/0015-orchestrator-skill-simplification.md`)
requires 30 days of usage data before simplifying the over-built
orchestrator skills. Apply the same bar to any promotion or
simplification: name the data window in the PR, not an intuition.

### Gate 4: adopt through change control or retire on the record

Adoption goes through the process in night-market-change-control.
Retirement is written down, never silent. ADR-0012 (confidence-tagged
claims) and ADR-0013 (Naur theory-building) carry Status: Superseded
by ADR-0017, which is Accepted and rules "Do not build an enforcement
mechanism. Permit voluntary use." A documented no is a valid result.

## The research-to-rules pipeline

1. Run multi-channel research (`Skill(tome:research)` or manual) into
   a dated synthesis at `docs/research/YYYY-MM-DD-<topic>.md`. Match
   the shape of the existing docs: Thesis, What the evidence says,
   solution pattern, Mapping to the night-market ecosystem, Evidence
   gaps and caveats.

2. Map every gap against existing ecosystem assets before proposing
   new code. Most gaps turn out to be covered already (see case
   study 3).

3. Land each real gap as the smallest durable artifact: a
   `.claude/rules/` file, a module inside an existing skill, or a
   config gate. A new skill is the last resort
   (`.claude/rules/shared-utility-consumer-rule.md` requires 2+
   consumers within 30 days).

4. Fold the load-bearing evidence out of the synthesis and into the
   artifact that relies on it, as a table of sources and findings with
   resolvable identifiers (arXiv IDs, URLs), plus the caveats that
   bound them. Then delete the citation to the research file.

Caution: `docs/research/` and `docs/superpowers/` are both gitignored,
so a tracked doc that cites a path under either is a dangling reference
for every checkout but the author's. Step 4 is what prevents this, and
it is not optional. Five syntheses were folded back into their consumers
on 2026-07-27 for exactly this reason, and a brainstorm design record
cited by `.claude/rules/ceremony-requires-need.md` survived that pass
because the check below only looked at `docs/research/`. Verify with:

```bash
rg -o --hidden 'docs/(research|superpowers)/[A-Za-z0-9._/-]+\.md' \
   -g '!docs/research/**' -g '!docs/superpowers/**' -g '!.git/**' . \
  | sed 's/.*://' | sort -u \
  | while read -r p; do
      git check-ignore -q "$p" && echo "DANGLING: $p"
    done
```

`docs/backlog/` is gitignored too but stays out of the alternation on
purpose. Every tracked citation of it is framed as a local convention,
which `.claude/skills/night-market-docs-and-writing/SKILL.md` states
outright, so adding it here would report three intentional hits and
train the next reader to skip the output.

The failure it does invite is different, and ADR-0019 nearly shipped it:
a tracked doc of record delegating its *content* to a gitignored path.
Citing the backlog as the local ranking list is fine. Saying "the design
is recorded in `docs/backlog/queue.md`" is not, because on a fresh clone
nothing is recorded anywhere. A doc of record carries its own content.

Silence means every cited background path resolves on a fresh clone.
The check tests whether the cited path is gitignored rather than
matching on filename shape, so `{session}`-style templates in tome's
own docs do not trip it. Add any newly ignored docs directory to the
alternation, or the next draft cited from a rule repeats this.

The research doc is background, not the record.

### Case study 1: coming loop (one doc, two artifact types)

The 2026-07-01 synthesis of Armin Ronacher's "The Coming Loop" pulled
in the METR randomized trial (arXiv 2507.09089: 16 developers, 246
tasks), GitClear 2025 (211M changed lines), and Karpathy's "mortal
terror of exceptions". It produced two artifacts:

- a review-time rule,
  `.claude/rules/prefer-invariants-over-fallbacks.md`
  (commit `9f771794`), and
- a runtime gate, egregore `completion_integrity`, default off
  (commit `83281337`).

Lesson: one research doc can fan out into different artifact types.
Match the artifact to where the failure occurs (review time versus
runtime).

### Case study 2: prover-verifier (module, not skill)

The 2026-07-01 prover-verifier synthesis landed as commit `29081fda`:
a 146-line module with six guards,
`plugins/imbue/skills/proof-of-work/modules/verifier-integrity.md`,
inside the existing proof-of-work skill. No new skill was created.
Lesson: extend the consumer that already exists.

### Case study 3: karpathy-derivation (build only the delta)

`docs/karpathy-derivation/project-brief.md` (tracked in git) maps
four Karpathy principles against existing skills in a coverage matrix
and concludes "~90% coverage exists." Only the delta was built:
`imbue:karpathy-principles`, a compact synthesis with an anti-pattern
catalog. The same matrix was later reused as the lens for the April
2026 skill audit. Lesson: run the coverage analysis first. The most
common honest research outcome is "we already have this."

## The audit protocol

As practiced in Discussion #449, the April 2026 skill-audit synthesis
(category [Knowledge]).

1. Tier 1 first: git history and `rg` scans
   (`Skill(pensive:tiered-audit)`). Escalate only what Tier 1 flags.

2. Targeted parallel agents require output contracts, per
   `.claude/rules/plan-before-large-dispatch.md` (plan mode at 4+
   agents). Contract schema in
   `plugins/imbue/skills/proof-of-work/modules/output-contracts.md`:
   `required_sections`, `min_evidence_count` (minimum `[EN]` evidence
   tags in findings), `strictness` (strict/normal/lenient). Findings
   carry file:line evidence. An empty findings list is a valid
   result. Report "no findings" as such rather than padding.

3. Findings land as waves of inline fixes.

4. Policy-shaped findings become issues, and landed issues become
   rules. Issues #454 (Exit Criteria required in every SKILL.md) and
   #457 (utility skills need 2+ consumers) both followed this path,
   are CLOSED, and live on as `.claude/rules/skill-exit-criteria.md`
   and `.claude/rules/shared-utility-consumer-rule.md`.

5. The deferred remainder gets a tracking issue: #574 (Wave-3
   skill-audit backlog, OPEN as of 2026-07-02).

Reading Discussions requires GraphQL. The `gh discussion` subcommand
does not exist:

```bash
gh api graphql -f query='query {
  repository(owner: "athola", name: "claude-night-market") {
    discussion(number: 449) { title body }
  }
}'
```

## Proof-and-analysis recipes

### Activation lift: does a skill actually fire?

`prototypes/forced-eval/` (commit `5683e89b`) measures whether a
forced-evaluation hook lifts skill activation:

- `activation_cases.json` holds labeled prompts with expected
  `Skill()` activations, recorded before measurement.
- `measure_activation.py` runs each prompt via `claude -p
  --output-format stream-json --max-turns 1 --allowedTools Skill`,
  baseline (hook off) against treatment (hook on), and applies the
  McNemar paired test. True-negative cases count false activations,
  so a high positive rate alone is not treated as success.

Status: PROTOTYPE, not wired into any plugin.json. The harness is
unit-tested but the live lift is unmeasured as of 2026-07-02 (the
README says so). Run the harness tests:

```bash
uv run python -m pytest prototypes/forced-eval/ -q
```

Verified 2026-07-02: 20 passed.

### Mutation testing: are the tests real?

Mutation testing mutates source code and checks whether the tests
notice. A surviving mutant is a test that cannot fail on that
behavior, which is the "hollow check" failure mode from
verifier-integrity Guard 2. CI runs it weekly plus on dispatch
(`.github/workflows/mutation-testing.yml`). Exit codes: 0 means no
survivors, 2 means survivors found, anything else is a crash. Local,
per plugin:

```bash
cd plugins/<plugin>
uv pip install mutmut --quiet
uv run mutmut run --paths-to-mutate=scripts/,src/ --tests-dir=tests/
```

Adjust `--paths-to-mutate` to the directories that exist. CI builds
the list from the plugin's top-level `scripts/` and `src/` dirs.

### Ratchet baselines: debt burndown you can prove

A ratchet baseline freezes today's debt count in a JSON file. The
check fails only when new debt appears, and prints when the count
drops so you can tighten the baseline and lock the win. Two live
ratchets, both pre-commit hooks and standalone scripts:

```bash
python3 scripts/check_skill_graph_drift.py
python3 scripts/check_skill_exit_criteria_drift.py
```

Verified output on 2026-07-02: dangling `Skill()` refs at 5 against a
baseline of 31, and SKILL.md files missing Exit Criteria at 1 against
a baseline of 127. Each script names the baseline key to lower. The
shrinking baseline diff is the burndown proof: cite it in the PR.

## Where good ideas came from

| Source | Path taken |
|--------|-----------|
| External research | Ronacher, METR, Karpathy syntheses became rules and gates (case studies above) |
| PR-review pain | Recurring finding classes became pre-commit guards and `.claude/rules/` entries |
| Audits | Discussion #449 became issues #454/#457, which became rules |
| Incident lessons | See night-market-failure-archaeology for the chronicle |

## When NOT to use

- Running tests, coverage, or the evidence gates for a concrete
  change: use night-market-validation-and-qa instead.
- Classifying, gating, and landing a change: use
  night-market-change-control instead.
- Mechanics of Discussions, the decision journal, or ADR practice:
  use night-market-collective-memory instead.
- Understanding settled incidents and reverts: use
  night-market-failure-archaeology instead.
- Choosing an open problem worth attacking: use
  night-market-research-frontier instead.
- Executing the completion-integrity work: use
  night-market-completion-integrity-campaign instead.

## Exit Criteria

- [ ] The idea has a written worthiness score with all six factors,
      and any score at or below 2.0 was discussed or queued, not
      built.
- [ ] Predicted numbers were recorded before the measurement ran.
- [ ] One mechanism explains every observation, including the cases
      that did not fail.
- [ ] Verification names an independent check the generator cannot
      influence, and that check has been shown able to fail.
- [ ] Any experiment shipped behind a default-off flag with a test
      covering the opt-in path.
- [ ] The outcome is on the record: a landed rule, module, gate, or
      ADR, or a superseding ADR documenting retirement.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15, branch
discussions-fix-1.9.14. Commit anchors (`9f771794`, `83281337`,
`cd903cbf`, `29081fda`, `5683e89b`) are stable. Volatile facts and
one-line re-verification:

- completion_integrity still default False:
  `rg -n "completion_integrity" plugins/egregore/scripts/config.py`
- Ratchet counts (5/31 dangling refs, 1/127 missing Exit Criteria on
  2026-07-02): rerun `python3 scripts/check_skill_graph_drift.py`
  and `python3 scripts/check_skill_exit_criteria_drift.py`
- Issue states (#454 CLOSED, #457 CLOSED, #574 OPEN on 2026-07-02):
  `gh issue view 574 --json state -q .state`
- Forced-eval lift still unmeasured:
  `rg -n "not measured" prototypes/forced-eval/README.md`
- Background doc dirs still gitignored:
  `git check-ignore docs/research docs/backlog docs/superpowers`
- Mutation exit-code semantics:
  `rg -n "Exit codes" .github/workflows/mutation-testing.yml`
- Worthiness thresholds: reread `docs/backlog/queue.md`. It is a
  local file, absent on fresh clones. The thresholds are restated
  above.
