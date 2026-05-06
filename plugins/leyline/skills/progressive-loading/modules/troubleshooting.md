# Troubleshooting

This module covers progressive-loading patterns for diagnostic
work: which diagnostic modules to load when something is broken,
how to gather evidence without overloading context, and how to
escalate from quick checks to deep investigation. The driving
question is "what is the cheapest read that confirms or
disconfirms my current hypothesis?".

## When This Module Applies

Load this module when:

- A test fails unexpectedly and the cause is not obvious.
- A skill produces wrong output and you need to find why.
- A loaded module fails to apply, or a hook rejects an action.
- The user reports an error and you must reproduce it.

For routine code review without an active failure, load the
review-specific modules instead. This module is for active
debugging.

## Three Diagnostic Tiers

Diagnostic work splits into three tiers by cost. Always start
at tier 1 and escalate only when needed.

| Tier | Focus | Module | Token Budget |
|------|-------|--------|--------------|
| 1 | Read error output | `error-reading.md` | 200 |
| 2 | Reproduce locally | `reproduction.md` | 400 |
| 3 | Bisect or instrument | `bisect-and-instrument.md` | 600 |

Most failures resolve at tier 1: the error message names the
problem. Tier 2 covers cases where the error is opaque or
non-deterministic. Tier 3 is for bugs that survive both.

## Tier 1: Read the Error Carefully

The cheapest diagnostic is reading the error message and the
surrounding context. The tier-1 module documents what to
extract.

```bash
# Re-run with verbose output and capture full traceback
pytest -xvs path/to/test_file.py::test_name

# For shell scripts, add -x to trace each command
bash -x ./script.sh

# For Python, show the full traceback (not the truncated form)
python -X tracebackshow=longest script.py
```

`pytest -x` stops at the first failure. `-v` shows test names.
`-s` disables output capture so `print` statements appear.

## Tier 2: Reproduce in Isolation

If the error is non-obvious or intermittent, reduce to a
minimal reproduction. The tier-2 module documents the bisection
of inputs.

```python
# Halving strategy: if a 1000-line file fails, try the first
# 500. If that passes, try 500-1000. Halve until you find the
# minimal failing line range.
def reduce_input(input_lines: list[str], test_fn) -> list[str]:
    if len(input_lines) <= 1:
        return input_lines
    mid = len(input_lines) // 2
    if test_fn(input_lines[:mid]):
        return reduce_input(input_lines[mid:], test_fn)
    if test_fn(input_lines[mid:]):
        return reduce_input(input_lines[:mid], test_fn)
    return input_lines  # both halves needed
```

This is a manual delta-debugging step. Real delta debugging
tools (e.g., `creduce` for C, `picireny` for Python) automate
the process for complex inputs.

## Tier 3: Bisect History

For regressions, `git bisect` finds the introducing commit
without manual narrowing.

```bash
# Mark current HEAD as bad
git bisect start
git bisect bad

# Mark a known-good commit
git bisect good v1.9.3

# bisect runs the test on each midpoint commit
git bisect run pytest -x path/to/test_file.py::test_name

# When done
git bisect reset
```

`bisect run` automates the process by running a command at each
step. The command must exit 0 for "good" and nonzero for "bad".

## Tier 3: Instrument with Logging

If bisect cannot find the cause (the bug existed forever or is
non-deterministic), add temporary logging at suspected points.

```python
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

def suspect_function(value):
    logger.debug("entering with value=%r", value)
    result = expensive_compute(value)
    logger.debug("returning %r", result)
    return result
```

Use `%r` formatting for inputs so quotes and types are visible.
A debug line that says `"entering with value=hello"` hides
whether the value was the string `"hello"` or `b"hello"`.

## Loading Decision

The hub picks the tier based on signals from the user.

- "Test fails, here's the output": tier 1.
- "It works for me but not in CI": tier 2.
- "It worked yesterday, broken now": tier 3 with bisect.
- "It fails 1 in 10 runs": tier 3 with instrumentation.

## Pitfalls

1. **Jumping to tier 3 immediately**: Bisecting takes minutes
   when reading the error takes seconds. Always start at
   tier 1.
2. **Removing the original error context**: When reproducing,
   keep the original error output. The reproduction may produce
   a different error and confuse the diagnosis.
3. **Permanent debug logging**: Tier-3 logging is temporary.
   Remove or downgrade to TRACE before merging.
4. **Bisecting a flaky test**: If the test is non-deterministic,
   bisect will mark commits randomly as good or bad. Stabilize
   the test first or skip bisection for that bug class.
5. **Reading the wrong error**: Long pipelines (CI, hooks,
   subagent dispatch) show errors from the wrapper, not the
   root cause. Drill to the deepest stack frame before
   forming a hypothesis.

## Cross-Reference

See `performance.md` for performance-specific diagnostics and
the parent `SKILL.md` for how troubleshooting modules plug into
the hub-and-spoke pattern.
