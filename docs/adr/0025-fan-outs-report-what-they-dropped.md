# ADR-0025: Fan-Outs Report What They Dropped, Scanners Prove They Can See

**Date**: 2026-09-18
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Related**: ADR-0024 (tome channel cards and record-based stop, the
source of the four patterns), ADR-0020 (positive controls)

## Context

ADR-0024 gave tome four things: typed cards pinned to the code by
drift tests, a stop decision read from records inside a pass budget,
positive controls before an empty result counts, and ranked candidates
from a keyword router. Three read-only surveys then asked where else in
the repository the same defects live. Their findings, each checked
against the file before anything was changed:

- Seventeen of the twenty-three workflows called `.filter(Boolean)` on
  their agent results (the survey counted ten; the repo guard written
  afterward found the rest). A subagent that dies returns null, so a
  crashed reviewer and a reviewer that found nothing were the same
  thing. In
  herald's judge panel the majority was computed over survivors, so
  two dropped judges let the third return `complete` alone.
- No test tied a workflow's `agentType` literal to an agent file.
  Eleven scripts name plugin agents. A renamed agent degrades the
  dispatch to the default agent and the workflow reports success.
- Every loop backed by Python already read records and carried a
  bound (egregore `verdict.py`, `night_run.py`, `stop_hook.py`; herald
  `double_shot_latte.py`; imbue `contract_validator.py`). Every loop
  that was prose only stopped on the model's own judgment, and four of
  six carried no bound at all. One told the agent to resume past a
  harness stop signal.
- attune's paradigm recommender read modifier keys the data file does
  not use (`preferred_paradigm` in code, `preferred` in YAML), so no
  modifier had ever changed a recommendation, and it returned
  `confidence="high"` however close the runner-up was. The same key
  drift OctoTools' tool cards carry.
- Six scanners could report "clean" without proving they could find
  anything: the slop gate on a pattern table that parses to nothing,
  pensive harden on a path with no Python, gauntlet's graph build with
  no parser, conserve's duplicate detector after its own filters
  emptied the file list, abstract's skill-graph audit if its regex
  stopped matching, and memory-palace's search over zero palaces. The
  memory-palace locator skill also cited `scripts/palace_manager.py`
  and three subcommands that do not exist.

## Decision

1. **A fan-out names what it dropped.** Every workflow that filters
   null agent results computes the dropped items by position and
   returns them (`missing`, `unread`, `unscored`, `unchecked`) beside
   the results, and logs them. `tests/test_shipped_workflows.py` fails
   a script that calls `.filter(Boolean)` without one of those names.
   herald's panel divides by the roster and returns `inconclusive`
   when any judge is missing.
2. **Every `agentType` literal resolves.** The same test file checks
   each `agentType: 'plugin:name'` against `plugins/<plugin>/agents/`.
   The harness's own types carry no plugin prefix and never match.
   Mutation-checked: a renamed agent fails it.
3. **List-shaped synthesis stages carry a schema.** spec-kit's gaps,
   scribe's ranking, leyline's stale contracts, cartograph's
   disagreements and conserve's cross-area duplication were free
   prose the caller iterated over. They now validate.
4. **Scanners run a positive control before a clean verdict.** A
   planted fixture with a known answer is committed beside each:
   `tests/fixtures/slop/planted.md` (CI runs it before the docs scan),
   pensive `tests/fixtures/harden/planted.py`, conserve
   `tests/fixtures/duplication/`, abstract
   `tests/fixtures/skill_graph/`. Where the defect was an exit code,
   the scanner now fails on a scan of nothing: harden returns 3 when
   zero files were read and reports `files_scanned`; `detect_duplicates`
   returns 2; `graph_build.py` returns 2 on a full build that created
   no nodes; the memory-palace CLI says "No palaces indexed" and
   returns false instead of "No matches found".
5. **The paradigm recommender ranks.** `ArchitectureResearcher.rank()`
   scores every paradigm the matrix cell and the modifiers name, using
   the keys the data file has, and names the rule behind each point.
   `recommend()` is the top of that list with the runners-up attached
   and confidence read from the margin. A test holds the consumed keys
   equal to the data file's keys.
6. **Prose loops get a record and a bound.** pensive code-refinement
   no longer resumes past a harness stop and reads its gate from
   `.review/findings.json` under `max_waves`. sanctum fix-workflow
   bounds Do/Check/Act at two retries and takes its outcome from the
   validator's exit codes. attune dorodango converges clarity and
   consistency on linter and formatter exit codes and un-converges a
   dimension on regression. conserve clear-context re-scores at most
   twice and caps the handoff chain at depth 3. attune's iteration
   governor caps Option C restarts at two. egregore's orchestrator
   prose reads success from `verdict.py`. Drift tests pin the pensive,
   attune and conserve text.
7. **Routers rank.** abstract methodology-curator loads the top two
   domain modules by term overlap; attune's paradigm-selection module
   describes the scorer instead of an override table.

## What was measured, and what was not

The workflow changes are text-tested and syntax-checked (each script
parsed inside an async wrapper, which caught one duplicate declaration
in leyline's plugin-health); the scripts were not executed. A dropped agent's new `missing` entry
has not been observed in a live run. The positive controls were run:
the planted slop file scores 38.24 against a threshold of 3.0, the
harden fixture fails `--strict` with exit 2, the duplicate pair is
found at default settings, the skill-graph fixture returns its known
answer, and a one-file tree builds a graph of two nodes.

The paradigm recommender's weights (matrix primary 4, secondary 2,
preference 1, recommendation 2, avoid minus 3) are the first set that
makes the shipped data file produce sensible answers on the six
contexts the tests name. They are not calibrated against any record
of which recommendation a project later kept.

egregore's `completion_integrity` default stays off. The campaign
skill gates promotion on a shadow read, then a measured false-stop and
false-continue rate over at least twenty items, then an ADR. The
shadow read (P1a) was run on 2026-09-18 from this repository and found
no `.egregore/manifest.json`, which is the documented branch for a
repository egregore has not been summoned in: the baseline has to be
taken where it ran.

attune's research phase was a stub: `perform_online_research` printed
the queries and returned `{}`, so `recommend_paradigm` had never
received anything. The session now writes what the queries argued for
as `{"preferred": [...], "avoid": [...]}` and passes `--research-file`;
`rank()` applies it as a fourth modifier whose rules say "research",
and a key outside that vocabulary is an error. The script still cannot
search, and says so.

memory-palace's `fixtures/semantic_queries.json` was deleted. Nothing
read it, no semantic search over the wiki exists to wire it into, and
its only history was an import-order fix.

## Consequences

- A new workflow must name its dropped items or the repo suite fails.
  The vocabulary is fixed (`failed`, `missing`, `unread`, `unreported`,
  `dropped`, `unscored`); a script that needs another word adds it to
  the test.
- Four fixtures are committed slop, security findings, duplication and
  a broken skill reference on purpose. The slop ratchet excludes
  `tests/fixtures/slop/`; the others live under `tests/fixtures/` and
  are not scanned by CI's docs gate.
- `harden --strict` on a path with no Python now fails CI where it
  used to pass. That is the intended change.
- The libraries the surveys found already compliant were not touched.
