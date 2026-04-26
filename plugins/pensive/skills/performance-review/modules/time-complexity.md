---
module: time-complexity
description: AST patterns for time-complexity hotspot detection
parent_skill: performance-review
category: code-quality
tags:
- time-complexity
- ast
- python
---

# Time Complexity Detectors

Six AST patterns that signal likely time-complexity hotspots.
Each detector cites the AST node it matches, the heuristic, and
a concrete fix.

## T1: Nested loop over the same iterable (HIGH)

**AST shape**: `ast.For` whose `iter` is `ast.Name`, where the
same `Name.id` already appears in an enclosing `ast.For`'s iter
on the loop stack.

**Why it matters**: `for x in items: for y in items: ...` is
O(n²) and rarely intentional. When `items` is large, this
becomes the hot spot.

**Fix**:

- If pairwise comparison is needed, sort once and use two
  pointers (O(n log n)).
- If membership is needed, build a set once outside the outer
  loop.
- If the nested work is independent, consider
  `itertools.product` for clarity (same complexity but signals
  intent).

## T2: List `in` lookup inside a loop (HIGH)

**AST shape**: `ast.Compare` with `ast.In` op, right-hand
operand `ast.Name`, found while the loop stack is non-empty.

**Why it matters**: `if x in ys` is O(n) when `ys` is a list,
making the enclosing loop O(n²). Static analysis can't prove
the variable's type, so the detector flags every `in <Name>`
inside a loop with a conditional suggestion.

**Fix**: If `ys` is a list and won't mutate during the loop:

```python
ys_set = set(ys)
for x in xs:
    if x in ys_set:  # O(1) per lookup
        ...
```

## T3: `re.compile()` inside a loop body (MEDIUM)

**AST shape**: `ast.Call` whose `func` is the attribute access
`re.compile`, found while the loop stack is non-empty.

**Why it matters**: Python's regex engine caches compiled
patterns internally, but the cache is bounded and not
guaranteed for every pattern. Hoisting the compile is cheap
and explicit.

**Fix**:

```python
_PAT = re.compile(r"\d+")

def matches(items):
    return [s for s in items if _PAT.search(s)]
```

## T4: String `+=` accumulator in a loop (MEDIUM)

**AST shape**: `ast.AugAssign` with `ast.Add` op, target an
`ast.Name` previously bound to a string literal in the same
function, occurring inside a loop.

**Why it matters**: Each `+=` allocates a new string and copies
the prefix. For long iterations this becomes O(n²) on total
size.

**Fix**:

```python
parts = []
for r in rows:
    parts.append(",".join(r) + "\n")
return "".join(parts)
```

`io.StringIO` is also acceptable.

## T5: Recursive function without memoization (LOW)

**AST shape**: `ast.FunctionDef` (or `AsyncFunctionDef`) whose
body contains `ast.Call` to the function's own name, with no
`@functools.cache`, `@functools.lru_cache`, or `@cache`
decorator on the def.

**Why it matters**: Naive recursion (e.g., textbook
`fib(n) = fib(n-1) + fib(n-2)`) has exponential repeat work.
Memoization makes the same recurrence linear.

**Fix**:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

If the recursion is intentionally non-memoized (e.g., side
effects on each call), suppress with a comment marker:

```python
# perf-review: intentional, side-effects on each call
def walk(node):
    ...
```

## T6: List comprehension passed to a reducer (LOW)

**AST shape**: `ast.Call` to one of `sum`, `max`, `min`, `any`,
`all`, `sorted`, `set`, `frozenset`, with first arg
`ast.ListComp`.

**Why it matters**: The list materializes the entire result in
memory, then the reducer walks it. A generator expression skips
the intermediate.

**Fix**: Drop the brackets.

```python
# Before
return sum([x * 2 for x in xs])

# After
return sum(x * 2 for x in xs)
```

For `sorted` / `set` / `frozenset` the materialization is
unavoidable, so the detector still flags them but a fix is
optional and may be cosmetic.

## Test references

Tests for each detector live at
`plugins/pensive/tests/skills/test_performance_review.py`. Each
detector is paired with at least one BDD-style scenario test
(`test_t1_*`, `test_t2_*`, ...). New detectors should ship with
a failing test first per the Iron Law.
