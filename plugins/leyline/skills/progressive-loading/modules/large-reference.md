# Large Reference

This module covers progressive-loading patterns for handling
large reference content: API references, language standards,
RFC bodies, or vendor documentation that exceeds the per-turn
token budget by an order of magnitude. The technique is to load
a small index always and pull in sections on demand.

## When This Module Applies

Load this module when the skill needs to reference content that:

- Exceeds 2000 tokens in its complete form.
- Splits cleanly into self-contained sections.
- Is read in small slices per task, not whole.
- Updates rarely enough that a stable index is reasonable.

For dynamic content that changes frequently, this pattern is the
wrong fit. Use a real document store and query it on demand.

## The Index-and-Sections Pattern

Split the reference into two artifacts: a small index file with
section names, anchors, and one-line descriptions, and a set of
section files loaded only when their anchor is referenced.

```text
modules/reference/
  index.md            # 200 tokens: list of sections and descriptions
  errors.md           # 400 tokens: error code reference
  pagination.md       # 350 tokens: pagination semantics
  rate-limits.md      # 300 tokens: throttling rules
  webhooks.md         # 600 tokens: webhook payloads
```

The hub always loads `index.md`. When a turn needs error code
detail, the loader resolves the anchor and pulls in `errors.md`.
Other sections stay on disk.

## Index File Format

The index lists each section with a stable anchor and a one-line
purpose. The model uses the index to decide which section to
load.

```markdown
# Reference Index

## Sections

- `errors.md`: HTTP status codes, error envelope shape, and
  retry guidance.
- `pagination.md`: Cursor and page-number variants, limits, and
  ordering guarantees.
- `rate-limits.md`: Per-user and per-IP throttling, retry-after
  header, burst rules.
- `webhooks.md`: Event types, signature verification, and
  delivery retry policy.
```

The index never describes implementation detail. It is a routing
table, not a tutorial.

## Section Loader

A small helper resolves anchors to file paths and reads the
section content. Sections are cached by path so repeated
references in one session do not re-read the disk.

```python
from functools import lru_cache
from pathlib import Path

REFERENCE_ROOT = Path("modules/reference")

@lru_cache(maxsize=8)
def load_section(name: str) -> str:
    path = REFERENCE_ROOT / f"{name}.md"
    if not path.exists():
        return f"# Missing section: {name}\n"
    return path.read_text(encoding="utf-8")
```

`lru_cache(maxsize=8)` keeps the eight most recently loaded
sections in memory. For longer sessions, raise the size or use
the tiered cache from `advanced-patterns.md`.

## When Sections Need Subsections

If a single section grows past 1000 tokens, split it again
rather than loading the whole thing. The split heuristic is the
same as the index pattern: anchors with one-line descriptions.

```markdown
# errors.md

## Sections

- `errors-4xx.md`: Client-side error codes (400-499).
- `errors-5xx.md`: Server-side error codes (500-599).
- `errors-envelope.md`: Common envelope shape across all codes.
```

The recursion stops when each leaf section fits comfortably in
one turn. A 200-400 token leaf is a good target.

## Pitfalls

1. **Loading the whole reference at start**: Defeats the entire
   pattern. The index must be the only always-loaded artifact.
2. **Index drift**: If the index lists sections that no longer
   exist, the loader returns a missing-section stub and the
   user gets a confusing answer. Validate the index against
   disk during skill build.
3. **Anchors that change between versions**: Section names are
   public API. Renaming `errors.md` to `error-codes.md` breaks
   every cached anchor. Add an alias mechanism if you must
   rename.
4. **Caching across edits**: The `lru_cache` above does not
   notice file edits. For dev iteration, clear the cache when
   the source mtime changes.
5. **Treating the index as content**: The index is for routing.
   Putting tutorial prose in it bloats the always-loaded
   footprint and reintroduces the original problem.

## Cross-Reference

See `loading-patterns.md` for the incremental-loading pattern
this module implements at scale, and the parent `SKILL.md` for
the hub-and-spoke contract.
