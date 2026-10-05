# P2: measure false-stop and false-continue rates

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
