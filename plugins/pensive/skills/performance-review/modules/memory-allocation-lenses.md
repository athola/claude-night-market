---
name: memory-allocation-lenses
description: Manual review lenses for unbounded collections, hot-path recompute, and serial blocking I/O that behavioral tests miss
category: performance-review
tags: [memory, allocation, unbounded, memoization, blocking-io, review-lens]
---

# Memory & Allocation Review Lenses

Three patterns that silently blow up on large inputs while unit
tests stay green. All three came out of one real investigation
into a TUI's network-graph memory profile on enterprise
networks. They are **manual review lenses**, not AST detectors:
no T-*/S-* automation exists for them, so the reviewer applies
them by reading the code. When reporting, name which failure
mode a finding is (see Caveats).

## Lens 1: Unbounded Collection from an External Source

A `Vec`/`HashMap` populated from data whose size the program
does not control (an ARP table, a DHCP lease list, a directory
scan, a DNS zone, an API page loop) and never bounded. Fine in
dev (8 entries); on a `/16` enterprise subnet it is thousands,
growing RSS and feeding downstream per-item work.

### Detection Heuristic

Flag a field or local that is:

1. a growable collection,
2. assigned from a function reading an OS, network, or
   filesystem source (`read_*`, `scan_*`, a sysctl or `/proc`
   read, an HTTP page loop), and
3. never truncated, capped, or LRU-evicted before storage.

Strongest signal: a wholesale replace (`self.x = scanned`)
with no cap.

### Fix Shape

Cap at the source with a named `MAX_*` const. Sort before
truncating if the source order is unstable, so the retained
set and any tests are deterministic. Show "N of M" in the UI
so truncation is visible, not silent.

## Lens 2: Hot-Path Recompute of Derived Data

Expensive derived data (a dedup + clone + sort, an O(n^2)
layout) recomputed on every frame of a fixed-FPS render loop,
and often again on every input event, when its inputs change
only occasionally. Not a leak, but sustained allocator churn
and CPU that dominates the profile of "opening the view".

### Detection Heuristic

Flag a function called from a render/draw path (or a 30/60fps
tick loop) that allocates collections, clones owned data, or
sorts, and whose inputs are fields mutated only by infrequent
events. Bonus signal: the same expensive helper is invoked
from both the render path and event handlers.

### Fix Shape

Memoize behind a generation counter (or dirty flag): bump it
where the inputs mutate, ideally at one central point, and
recompute lazily only when it advances. In a `&self` render
path, `RefCell`/`Cell` keeps the signature and stays
test-transparent. Guard the manual "every mutation bumps the
generation" invariant with a test on the real mutation path,
including the removal/shrink direction. A hand-rolled
invalidate in a unit test does not prove it.

## Lens 3: Serial Blocking I/O over an Unbounded Collection

```rust
for item in &items {            // items is unbounded (Lens 1)
    item.field = blocking_lookup(item);   // DNS, stat, HTTP
}
```

On a large `items` this serializes N blocking calls; with no
per-call timeout a few slow or hanging entries (PTR-less
hosts) stall the whole pass, every interval.

### Detection Heuristic

Flag a loop body containing a blocking call (DNS, filesystem,
sync HTTP, `spawn_blocking` awaited one-at-a-time) iterating a
collection whose length is not statically bounded,
particularly inside a periodic task.

### Fix Shape

Cap the set first (Lens 1), then bound concurrency
(`futures::stream::...buffer_unordered(N)`) with a per-call
timeout, or resolve lazily on demand instead of eagerly for
the whole set.

## Caveats Findings Must State

- Distinguish **persistent unbounded growth** (true RSS climb:
  Lens 1/3 data) from **transient per-frame churn** (Lens 2:
  spikes and frees, reducible by memoization, not eliminated
  by a cap). Name which one a finding is. "Capped the memory"
  over-promises on the churn case.
- A cap has a UX cost (hidden items). Pair it with a visible
  count; do not silently drop.
- The win from these lenses is usually by-construction, not
  measured. Ask for a count or diagnostic the user can read in
  their environment rather than claiming a measured
  improvement.

## Output Section

```markdown
## Memory & Allocation
- [file:line] Unbounded collection from <source>: [cap shape,
  growth mode: persistent]
- [file:line] Hot-path recompute in <render path>: [memoize
  behind generation counter, growth mode: churn]
- [file:line] Serial blocking I/O over unbounded set: [bound
  concurrency + timeout]
```
