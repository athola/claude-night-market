# Performance

This module covers progressive-loading patterns for performance
analysis: which profiling, benchmarking, and complexity-review
modules to load based on the symptom (slow runtime, high memory,
high allocations) and the target language. Loading every
performance tool at once wastes context when only one symptom
is being investigated.

## When This Module Applies

Load this module when the task involves:

- Profiling slow code or finding hot loops.
- Measuring memory use or allocation rate.
- Reviewing algorithmic complexity (big-O) of a function.
- Establishing performance baselines before a refactor.

For token-budget performance of skills themselves, load
`performance-budgeting.md`. This module is about runtime
performance of user code.

## Symptom-Driven Loading

Performance work splits into three distinct symptom categories,
each with its own toolchain. Load only the relevant module.

| Symptom | Tool Module | Token Estimate |
|---------|-------------|----------------|
| Wall-clock slow | `cpu-profiling.md` | 500 |
| Memory high | `memory-profiling.md` | 500 |
| Algorithmic | `complexity-review.md` | 400 |
| Throughput low | `benchmarking.md` | 400 |
| Concurrency | `async-profiling.md` | 600 |

The user usually states the symptom first. If they say "this
endpoint takes 8 seconds", load `cpu-profiling.md`. If they
say "memory grows over time", load `memory-profiling.md`. Do
not load both speculatively.

## Language-Specific Sub-Loading

Each symptom module dispatches to a language-specific tool. The
hub picks the language from project metadata.

```bash
# Python: cProfile, py-spy, scalene
python -m cProfile -s cumulative script.py

# Rust: cargo-flamegraph, perf, criterion
cargo flamegraph --bin myapp

# Node: --prof, clinic.js, 0x
node --prof script.js
```

`py-spy` and `scalene` are real PyPI packages. `cargo
flamegraph` is provided by the `flamegraph` crate. `clinic.js`
is on npm. The language sub-modules document install commands
and read paths for the resulting profile artifacts.

## Baseline Before Optimizing

A common failure mode is optimizing without a baseline. The
benchmarking module enforces a measure-first protocol.

```python
import time
from statistics import mean, stdev


def baseline(func, *args, runs: int = 10, **kwargs):
    times: list[float] = []
    for _ in range(runs):
        start = time.perf_counter_ns()
        func(*args, **kwargs)
        times.append((time.perf_counter_ns() - start) / 1_000_000)
    return {
        "mean_ms": mean(times),
        "stdev_ms": stdev(times) if len(times) > 1 else 0.0,
        "min_ms": min(times),
        "max_ms": max(times),
    }
```

`time.perf_counter_ns` is monotonic and high-resolution. For
microsecond-scale operations, use `timeit.repeat` instead, which
disables garbage collection between runs.

## Complexity Review

For algorithmic concerns, the complexity module documents the
common pitfalls.

```python
# O(n^2): nested membership check on a list
def has_duplicate_slow(items: list[int]) -> bool:
    for i, item in enumerate(items):
        if item in items[i + 1:]:  # O(n) inside O(n)
            return True
    return False


# O(n): set-based membership
def has_duplicate_fast(items: list[int]) -> bool:
    seen: set[int] = set()
    for item in items:
        if item in seen:
            return True
        seen.add(item)
    return False
```

The complexity module surfaces these patterns through static
inspection rather than measurement. It pairs with the
`pensive:performance-review` skill for a real AST walk.

## Pitfalls

1. **Profiling without a baseline**: "It's faster" with no
   numbers is meaningless. Always record before/after with the
   benchmarking module loaded.
2. **Loading the memory module for CPU symptoms**: They use
   different tools and produce different artifacts. Match the
   module to the symptom.
3. **Profiling production code unprepared**: Profilers add
   overhead. `cProfile` in particular slows execution
   noticeably. Document the overhead in the profile output.
4. **Treating mean as the only number**: Mean hides tail
   latency. Always report at least mean, p99, and max.
5. **Optimizing the wrong layer**: A microsecond improvement in
   a function called once per request matters less than a
   millisecond in a function called per-row in a 10000-row
   loop. The complexity module addresses this by walking the
   call graph.

## Cross-Reference

See `performance-budgeting.md` for skill token performance,
`troubleshooting.md` for diagnostic workflows, and the parent
`SKILL.md` for how performance modules plug into the
hub-and-spoke pattern.
