# Model and Harness Update Workflow: Implementation Plan

**Date**: 2026-08-02
**Status**: Ready for execution
**Spec**: `docs/model-harness-updates/specification.md`

## Approach

Build the deterministic engine first, then the workflow that drives it.
A skill that tells a model to "check for drift" without a script behind
it produces a different answer every run. The script is the contract;
the skill is the procedure around it.

Order matters for one reason beyond preference: the drift script must
be able to detect the Fable vocabulary gap **before** that gap is
fixed. Fixing the gate first would erase the only live test case the
repo currently has.

## Tasks

### Phase 1: ledger and drift engine (TDD)

| # | Task | Proof |
|---|------|-------|
| T01 | Write failing tests for ledger read, write, and schema validation | pytest red |
| T02 | Write failing tests for all four drift classes | pytest red |
| T03 | Implement `scripts/check_upstream_drift.py` | pytest green |
| T04 | Create `.claude/upstream-baseline.json` recording current state | Script exits 1 (Fable gap live) |

### Phase 2: prove the engine catches real drift

| # | Task | Proof |
|---|------|-------|
| T05 | Run drift script against the untouched repo | Reports the `fable` and `xhigh`/`max` vocabulary gaps |
| T06 | Capture that output as the bootstrap migration evidence | Report file written |

### Phase 3: close the drift the engine found

| # | Task | Proof |
|---|------|-------|
| T07 | Write failing test: gate accepts `fable`, `xhigh`, `max` | pytest red |
| T08 | Widen `VALID_MODELS` and `VALID_EFFORTS` in `check_agent_model_matrix.py` | pytest green |
| T09 | Update `docs/agent-model-matrix.md` for the widened vocabulary | Gate exits 0 |
| T10 | Re-run drift script | Exits 0 |

### Phase 4: the skill

| # | Task | Proof |
|---|------|-------|
| T11 | Author `SKILL.md` hub with frontmatter and Exit Criteria | Frontmatter parses |
| T12 | Author `modules/drift-detection.md` | Referenced from hub |
| T13 | Author `modules/research-protocol.md` (tome, web fallback) | Referenced from hub |
| T14 | Author `modules/asset-sweep.md` | Referenced from hub |
| T15 | Author `modules/verification.md` | Referenced from hub |

### Phase 5: close the loop

| # | Task | Proof |
|---|------|-------|
| T16 | Write the bootstrap migration report | File exists, ledger points at it |
| T17 | Update ledger `last_migration` after proofs pass | Schema validates |
| T18 | Run repo gates (markdown, slop, exit-criteria, skill-graph) | All pass |

## Risk classification

| Task group | Tier | Rationale |
|------------|------|-----------|
| T01 to T06 | GREEN | New files only, no existing behavior touched |
| T07 to T10 | YELLOW | Widens a hard gate; a mistake weakens an active guard |
| T11 to T15 | GREEN | New skill files |
| T16 to T18 | GREEN | Documentation and ledger |

T07 to T10 carry the only real risk. The mitigation is that the
vocabulary only widens. No existing accepted value is removed, so no
currently passing agent can start failing.

## Out of scope

Rewriting the 48 files that carry dated model IDs outside gated
surfaces. The drift script reports them; fixing them is a follow-up
sweep with its own review, because most are historical references in
docs and tests where a dated ID is correct.
