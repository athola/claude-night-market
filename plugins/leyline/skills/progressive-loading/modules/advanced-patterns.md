# Advanced Patterns

This module covers progressive-loading techniques that go beyond
the basic hub-and-spoke setup: adaptive loading driven by runtime
signals, dependency graph resolution across modules, multi-tier
caches with eviction, and recovery patterns when a module load
fails mid-session. Read this after `loading-patterns.md` and
`selection-strategies.md` are familiar.

## When to Reach for Advanced Patterns

The basic patterns in `loading-patterns.md` cover most skills.
Use the advanced patterns here only when one of the following is
true:

- The skill exceeds the standard 800-1500 token target listed in
  `performance-budgeting.md` and cannot be split.
- Modules form a directed acyclic graph (DAG) of dependencies,
  not a flat list.
- Sessions are long enough that loaded modules outlive their
  usefulness and must be evicted.
- A module load can fail (missing file, parse error, dependency
  conflict) and the skill must degrade rather than abort.

## Pattern 1: Adaptive Loading

Adaptive loading shifts module selection based on telemetry from
the current session. The hub records which modules were actually
read and which were never accessed. On the next activation, low
hit-rate modules drop to a lower tier.

```python
from collections import Counter
from pathlib import Path

class AdaptiveSelector:
    def __init__(self, telemetry_path: Path) -> None:
        self.telemetry_path = telemetry_path
        self.hits: Counter[str] = self._load_hits()

    def _load_hits(self) -> Counter[str]:
        if not self.telemetry_path.exists():
            return Counter()
        return Counter(self.telemetry_path.read_text().splitlines())

    def tier_for(self, module: str, default: str = "common") -> str:
        count = self.hits.get(module, 0)
        if count >= 10:
            return "core"
        if count >= 3:
            return default
        return "edge"
```

This pattern is appropriate for skills used hundreds of times by
the same user. For one-shot skills the overhead is not justified.

## Pattern 2: Module DAG Resolution

When modules declare dependencies on other modules (see the
`dependencies` field in the frontmatter shown in
`loading-patterns.md`), the loader must resolve them topologically
to avoid loading a module before its prerequisites.

```python
from graphlib import TopologicalSorter

def resolve_load_order(modules: dict[str, list[str]]) -> list[str]:
    sorter: TopologicalSorter[str] = TopologicalSorter()
    for module, deps in modules.items():
        sorter.add(module, *deps)
    return list(sorter.static_order())
```

`graphlib` is in the Python standard library since 3.9 and raises
`CycleError` if the graph is not a DAG. Catch that exception and
report which modules form the cycle rather than letting the
loader hang.

## Pattern 3: Tiered Cache with Eviction

For skills with many small modules, a two-tier cache keeps recent
modules hot and evicts cold ones under context pressure.

```python
from collections import OrderedDict

class TieredCache:
    def __init__(self, hot_size: int = 5, warm_size: int = 15) -> None:
        self.hot: OrderedDict[str, str] = OrderedDict()
        self.warm: OrderedDict[str, str] = OrderedDict()
        self.hot_size = hot_size
        self.warm_size = warm_size

    def get(self, key: str) -> str | None:
        if key in self.hot:
            self.hot.move_to_end(key)
            return self.hot[key]
        if key in self.warm:
            value = self.warm.pop(key)
            self._promote(key, value)
            return value
        return None

    def _promote(self, key: str, value: str) -> None:
        self.hot[key] = value
        if len(self.hot) > self.hot_size:
            evicted_key, evicted_value = self.hot.popitem(last=False)
            self.warm[evicted_key] = evicted_value
            if len(self.warm) > self.warm_size:
                self.warm.popitem(last=False)
```

The hot tier holds modules read in the last few turns. The warm
tier holds older modules that may still be relevant. Eviction
happens only when the warm tier overflows.

## Pattern 4: Graceful Load Failure

If a module file is missing or malformed, the loader should log
the failure, fall back to a known-good substitute when one is
declared, and continue. Aborting the entire skill on a single
missing module penalizes the user for an authoring mistake.

```python
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def safe_load(module_path: Path, fallback: Path | None = None) -> str:
    try:
        return module_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("module missing: %s", module_path)
        if fallback and fallback.exists():
            return fallback.read_text(encoding="utf-8")
        return f"# Module unavailable: {module_path.name}\n"
    except UnicodeDecodeError as exc:
        logger.error("module decode failed: %s (%s)", module_path, exc)
        return f"# Module unreadable: {module_path.name}\n"
```

## Pitfalls

1. **Premature adaptation**: Telemetry-driven loading needs many
   sessions of data. Do not enable it for new skills with no
   usage history.
2. **DAG cycles in author error**: If two modules both list each
   other as dependencies, the loader will reject the graph. Surface
   the cycle path, do not silently break it.
3. **Cache invalidation on edits**: A cached module persists even
   after the source file changes on disk. Stamp cache entries with
   the file mtime and re-read when it differs.
4. **Hidden eviction**: If a module disappears from context after
   being loaded, the user may not notice until the skill produces
   stale output. Log evictions at INFO level.
5. **Fallback as silent feature**: A fallback that always succeeds
   masks missing modules. Emit a warning every time the fallback
   activates so authors can fix the root cause.

## Cross-Reference

See the parent `SKILL.md` for the hub-and-spoke overview and
`loading-patterns.md` for the basic loading mechanisms these
advanced patterns extend.
