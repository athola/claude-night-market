# Verifiable Goals: A Reformulation Template

Vague tasks generate vague work. The fix is a
mechanical reformulation: rewrite the request as a
goal that has an unambiguous "done" signal. Then loop
until the signal fires.

This module makes the reformulation explicit, with a
template and worked examples.

## The Template

```
Original request: <user's words>

Reformulated goal:
  Success signal: <something a script or test can check>
  Test that proves the signal fires: <how>
  Out-of-scope cleanups noticed: <list, do not fix>
```

The success signal must be checkable without human
judgment. "It feels faster" is not a signal.
"p95 under 200ms on the seed dataset" is.

## Worked Examples

### Example 1: "Add validation"

```
Original: Add validation to the user signup endpoint.

Reformulated:
  Success signal: requests with invalid email,
    missing username, or password under 8 chars
    return HTTP 400 with a JSON error.
  Test: three pytest cases, one per failure mode,
    asserting status 400 and a specific error key.
  Out of scope: rate limiting, password complexity
    rules, captcha. Mention but do not implement.
```

### Example 2: "Fix the bug"

```
Original: Fix the bug where empty emails crash the
  validator.

Reformulated:
  Success signal: validate_user with email '' or
    None raises ValueError, not AttributeError or
    TypeError.
  Test: test_validate_user_empty_email and
    test_validate_user_none_email, both asserting
    ValueError before the fix lands.
  Out of scope: improving username validation, adding
    docstrings, refactoring quote style.
```

This pattern is the heart of `Skill(imbue:proof-of-work)`
and the Iron Law: write the failing test first.

### Example 3: "Refactor X"

```
Original: Refactor the upload service.

Reformulated:
  Success signal: the existing test suite for
    upload (12 tests) is green before the refactor,
    green after, with no test changes.
  Test: pytest tests/upload/ both before and after
    the diff, with diff capture.
  Out of scope: anything that requires changing a
    test. If a test must change, the request is
    behavior change, not refactor, and needs a new
    spec.
```

### Example 4: "Make it faster"

```
Original: Make the search faster.

Reformulated:
  Success signal: median latency on the seed query
    set drops from current N ms to under M ms (M
    chosen with the user).
  Test: a benchmark script that runs 100 queries
    against the seed dataset and reports median.
    Captured before and after the change.
  Out of scope: throughput optimization, perceived
    speed, frontend caching. These are different
    "faster" axes. Confirm which one before starting.
```

This example also illustrates AP-2 (Multiple
Interpretations): when "faster" is ambiguous, name
the axis before reformulating.

### Example 5: "Improve UX"

```
Original: Improve the checkout UX.

Reformulated:
  Success signal: a test user completes the checkout
    flow in 4 clicks or fewer (current: 7), with no
    blocking validation surprises.
  Test: a Playwright or manual click-through script
    that records click count and timestamp per step.
  Out of scope: visual redesign, copy revisions,
    accessibility audit. Mention but do not bundle.
```

### Example 6: "Add rate limiting"

```
Original: Add rate limiting to the API.

Reformulated:
  Success signal (step 1): the 11th request to
    /signup in 60 seconds returns 429.
  Test: a curl loop in CI plus a pytest that
    simulates 11 sequential calls.
  Out of scope (this step): Redis backend,
    per-endpoint configuration, monitoring. Each
    is a separate reformulation.
```

This example illustrates AP-8 (Multi-Step Plan
Without Verification Gates): each step gets its own
reformulation, its own success signal, its own test.

## Why This Works

When the success signal is a script or test, three
things become true:

1. The agent can loop independently. No need to ask
   "is it good now?" The test answers.
2. The user can review by running the test, not by
   reading 300 lines of diff.
3. The work is self-documenting. The next person can
   see what "done" meant for this task.

## Cross-References

- `Skill(imbue:proof-of-work)` is the contract that
  enforces this template under the Iron Law.
- `Skill(superpowers:test-driven-development)` is the
  RED-GREEN-REFACTOR loop this template feeds.
- `/spec-kit:speckit-clarify` command helps when the
  reformulation surfaces an ambiguity that needs the
  user's input first.
