# Drift Detection

Step 1 of the sweep. Deterministic, read-only, no model in the loop.
The output of this step is the input to research, so run it first and
keep the report.

## Run it

```bash
# Human-readable
python3 scripts/check_upstream_drift.py

# Machine-readable, for feeding the research step
python3 scripts/check_upstream_drift.py --json > /tmp/drift.json
```

Exit codes follow the house gate convention.

| Code | Meaning |
|------|---------|
| `0` | No drift. Nothing to sweep. |
| `1` | Drift found. Continue to research. |
| `2` | Ledger missing, malformed, or failing schema validation. |

A `2` is never drift. Fix the ledger before reading anything else,
because every later comparison depends on it.

## The ledger

`.claude/upstream-baseline.json` is the watermark and the only place
that records what upstream looked like last time.

| Field | Holds |
|-------|-------|
| `harness.version` | Claude Code version at the last migration |
| `models.tiers` | Tier aliases accepted at the last migration |
| `models.ids` | The concrete model ID behind each tier |
| `vocabularies.effort_levels` | Effort levels the harness accepted |
| `ratchets.dated_ids_backlog` | Capped count of pre-existing dated IDs |
| `last_migration` | The previous run: trigger, delta, report path |
| `history` | Every prior `last_migration`, append-only |

Three invariants hold:

1. Every tier in `models.tiers` has an entry in `models.ids`. A tier
   with no ID behind it cannot be resolved.
2. `history` is append-only. A rewritten history destroys the audit
   trail the ledger exists to provide.
3. The ledger is written only after the verification step passes.

## Reading the four classes

### `harness`

The installed `claude --version` differs from `harness.version`. Fully
deterministic. This is the trigger for a harness sweep.

If the version cannot be read at all, the detector reports that rather
than assuming a match. A missing binary is a condition to investigate,
never a silent pass.

### `vocabulary`

A gate's frozen set omits a value the ledger records. The detector
parses `VALID_MODELS` and `VALID_EFFORTS` out of
`scripts/check_agent_model_matrix.py` with `ast`, never by importing
it, because importing a gate runs its module-level path resolution.

The ledger is a floor here, not a ceiling. A gate accepting more than
the ledger records is not drift. Only values the ledger knows about and
the gate rejects count.

This class caught the Fable case: Fable shipped, the ledger recorded
it, and the gate rejected every agent that tried to pin it.

### `dated_ids`

Dated model IDs such as `claude-opus-4-6` outside the surfaces
`check_agent_model_matrix.py` already covers. Agent files and
`SKILL.md` are skipped here precisely because that gate owns them, and
reporting them twice would double-count one violation.

This class is a **ratchet**, not a hard gate. The repo carries a
pre-existing backlog in docs, tests, and historical notes where a dated
ID is often correct. Failing on every one would hold the gate
permanently red and train everyone to ignore it. The detector fails
only when the count exceeds `ratchets.dated_ids_backlog`, and prints
the available slack when the count has fallen.

### `unknown_tier`

Markdown frontmatter naming a tier absent from the roster. Read only
from the leading YAML block of `.md` files. A bare `model:` line in
prose is documentation showing the reader what to write, and
`model: str` in a Python dataclass is a type annotation. Both produced
false positives before the check was narrowed.

## What the detector skips, and why

| Skipped | Reason |
|---------|--------|
| `worktrees/`, `.worktrees/` | Duplicate the tree, double-count findings |
| `context-archive/` | Historical snapshots, not authored pins |
| `data/staging/` | Memory-palace web captures, other people's text |
| `agents/`, `SKILL.md` (for `dated_ids`) | Owned by the matrix gate |

Anything skipped is skipped by the sweep too. The detector and the
sweep must agree on scope or the report will not match the work.
