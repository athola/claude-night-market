# Stop Verifier

`tome.synthesis.verifier.verify_context` decides between passes
whether a session searches again. It adapts the context verifier
from OctoTools (arXiv 2502.11271), which asks the model after each
step whether its memory is complete and answers STOP or CONTINUE.

## Why the decision is not a judgment

A research agent grading whether its own search was enough is the
arrangement two 2026 results warn against. VRR-Stop
(arXiv 2607.17641) measured a verifier's acceptance rate rising while
true validity fell, and arXiv 2607.24300 found self-authored
verification unreliable in self-improving agents. So every criterion
reads a record no agent graded: the query log, the positive controls,
and the frontier verdict.

| OctoTools asks | Read from | Action when it fails |
|----------------|-----------|----------------------|
| Is the memory complete? | `channel_outcomes`: every dispatched channel `ok` or `empty` | `rerun` |
| Does a limitation need verifying? | `canary_outcomes`: an empty controlled channel passed its control | `rerun` |
| Is anything ambiguous or inconsistent? | `frontier_verdict` is not `CHANNEL_MISMATCH_SUSPECTED` | `reformulate` |
| Could an unused tool help? | a `THIN_FIELD_CANDIDATE` had every retrieval card in the plan | `add` |
| (step budget) | `passes_run < max_passes` | stop, list the gaps |

## What it cannot see

The frontier verdict's blind spots are this verifier's too. A field
published under different vocabulary looks absent, so a clean `STOP`
means the search was well formed, not that nothing exists. A channel
that is `ok` may still have missed most of what it could have found:
nothing here estimates recall inside a channel.

Recall-based stopping rules would close that gap: the knee and target
methods from technology-assisted review (arXiv 2106.09871,
arXiv 2108.12746) and species-discovery estimates (STADS,
arXiv 1803.02130). All three need to know which query first
surfaced each finding, and the query log records a count per query
with no attribution. ADR-0024 records them as the next step and names the
missing field.
