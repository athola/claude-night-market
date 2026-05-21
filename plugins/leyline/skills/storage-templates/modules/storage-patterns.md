---
name: storage-patterns
description: Storage backend patterns for templates and lifecycle data with retention, atomic writes, and selection criteria
category: storage
tags: [storage, files, sqlite, json, retention, atomic-writes]
dependencies: [storage-templates]
complexity: beginner
estimated_tokens: 800
---

# Storage Patterns

Storage backend patterns for the templates and lifecycle data
described in the parent skill. Covers when to use plain files,
when to reach for SQLite, when JSON or YAML is the right
serialization, how to expire data, and how to write without
corruption.

## Backend Selection

Pick the simplest backend that meets the access pattern. Each
step up adds operational cost: schemas to migrate, locks to
manage, indexes to maintain. Start at file-based and move up
only when a measured limit forces it.

| Pattern | Use When | Avoid When |
|---------|----------|------------|
| Plain markdown files | Human reads/edits, low write rate, full-text search via grep is enough | Random-access lookup by key dominates |
| JSON file per record | Single writer, typed data, want diff-friendly history | Many concurrent writers |
| JSONL append log | Append-only event stream, replay is cheap | Need random update or delete |
| SQLite database | Index-heavy queries, joins, transactional updates | Single-writer markdown is enough |
| YAML config file | Human-edited settings, rare writes | Frequent programmatic mutation |

### Real-File Examples

These backends are in use today; cite them when explaining the
pattern to a caller:

| Backend | Real File |
|---------|-----------|
| JSONL append log | `plugins/memory-palace/data/intake_queue.jsonl` |
| YAML config | `plugins/memory-palace/data/seed_topics.yaml` |
| JSON-per-session | `plugins/memory-palace/data/sessions/<uuid>.json` |
| SQLite | `plugins/memory-palace/src/memory_palace/knowledge_graph.py` |
| Markdown staging | `plugins/memory-palace/data/staging/*.md` |

## File-Based Storage

The default. One file per record, organized by maturity (see
`lifecycle-stages.md`) or by date prefix.

### Layout

```
data/
  evergreen/
    functional-core-pattern.md
  growing/
    async-patterns.md
  seedlings/
    2025-12-05-template-idea.md
  archive/
    2024-06-01-old-pattern.md
```

### Read Path

```python
from pathlib import Path
import frontmatter   # python-frontmatter

def load_record(path: Path) -> dict:
    """Read a markdown record with YAML frontmatter."""
    post = frontmatter.load(path)
    return {"metadata": post.metadata, "body": post.content}
```

### When File-Based Wins

- Humans edit the records by hand
- Diffs are reviewed in pull requests
- Total record count stays under ~10k
- Search is "grep over directory"

### When File-Based Hurts

- Lookup-by-key dominates (every read needs a scan)
- Multiple writers race on the same file
- The record count breaks filesystem listing performance

## SQLite Storage

Reach for SQLite when you need indexed lookup, joins, or
transactional updates across multiple records. The pattern in
`plugins/memory-palace/src/memory_palace/knowledge_graph.py`
shows the shape: schema declared as `CREATE TABLE IF NOT
EXISTS` statements, connection per process, row factory set
for dict-style access.

### Minimal Schema Pattern

```python
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    maturity    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    body        TEXT
);

CREATE INDEX IF NOT EXISTS idx_records_maturity
    ON records(maturity);
"""

def open_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
```

### Migration

Schema changes are append-only when possible. Add new columns
with `ALTER TABLE ... ADD COLUMN`. For destructive changes,
copy into a new table and drop the old one inside a single
transaction. The `migration.py` module in memory-palace shows
the JSON-side equivalent for record-level migrations.

### When SQLite Wins

- Need to ask "all records with maturity=growing updated in
  the last week" without scanning the whole directory
- Need transactional updates across two related records
- Record count is in the tens of thousands or higher

### When SQLite Hurts

- Humans want to edit records directly
- Records belong in version control alongside code
- A single writer with under 1k records is the whole story

## JSON and JSONL

JSON is the right format when the record is typed data
without long prose, when it ships across a process boundary,
or when a tool downstream expects it.

### JSON-Per-Record

One file per record, named by stable id. Used for sessions in
`plugins/memory-palace/data/sessions/`.

```python
import json
from pathlib import Path

def write_session(session_dir: Path, session_id: str,
                  data: dict) -> None:
    target = session_dir / f"{session_id}.json"
    write_atomic_json(target, data)   # see Atomic Writes
```

### JSONL Append Log

One line per event. Used for the intake queue at
`plugins/memory-palace/data/intake_queue.jsonl`. Cheap to
append, easy to tail, replay by line.

```python
def append_event(log_path: Path, event: dict) -> None:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
```

JSONL does not support in-place edit. To update an event,
write a new tombstone or rebuild the log from scratch.

## Atomic Writes

Any process that crashes mid-write can leave a half-written
file. The fix is to write to a sibling tempfile and rename
into place. On POSIX, `os.replace` is atomic on the same
filesystem.

The reference implementation is in
`plugins/memory-palace/src/memory_palace/migration.py` as
`_atomic_write_json`. Copy the shape:

```python
import json, os, tempfile, contextlib
from pathlib import Path
from typing import Any

def write_atomic_json(target: Path, data: dict[str, Any]) -> None:
    """Write JSON to target atomically via a sibling tempfile."""
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(target.parent),
            prefix=target.name + ".",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp_path = tmp.name
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, str(target))
        tmp_path = None
    except OSError:
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
        raise
```

Three properties matter:

1. The tempfile is in the same directory as the target so
   `os.replace` is a same-filesystem rename.
2. `flush()` then `fsync()` before the rename, so a crash
   between rename and the next sync still leaves the data on
   disk.
3. On error the original file is untouched and the tempfile
   is cleaned up.

For SQLite, the equivalent is to wrap the change in a
transaction. SQLite's WAL mode handles the atomic-rename
problem internally.

## Retention Policies

Storage grows. Without retention, a working store becomes a
landfill. Pick a policy per backend.

### Retention Tiers

| Tier | Default Retention | Trigger |
|------|-------------------|---------|
| Seedling | 90 days | Age since `created` |
| Growing | 12 months | Age since last `updated` |
| Evergreen | None | Manual archive only |
| Reference | Until version expires | `expires` field |
| Archive | 24 months | Age since archived |
| JSONL log | Rolling 30 days | Rotate to `.gz` past window |
| SQLite snapshot | Daily for 7 days | Backup script |

### Retention Implementation

```python
from datetime import datetime, timedelta
from pathlib import Path
import frontmatter

def find_expired_seedlings(root: Path,
                           max_age_days: int = 90) -> list[Path]:
    """Return seedling files older than max_age_days."""
    cutoff = datetime.now() - timedelta(days=max_age_days)
    out: list[Path] = []
    for path in (root / "seedlings").glob("*.md"):
        post = frontmatter.load(path)
        created = datetime.fromisoformat(post.get("created", ""))
        if created < cutoff:
            out.append(path)
    return out
```

Run retention on a schedule, not at write time. Combining the
two slows writes and makes the policy harder to audit.

### Archive vs Delete

Archive by default. Move to `archive/YYYY-MM-DD-topic.md` with
a frontmatter note explaining why. Delete only when the data
is regenerable (caches, derived indexes) or when retention
policy explicitly requires it (privacy, compliance).

## Concurrency Notes

| Backend | Concurrent Writers | Notes |
|---------|--------------------|-------|
| Markdown files | One per file | Use file lock if a script may run twice |
| JSON-per-record | One per file | Atomic write covers single-writer case |
| JSONL append | Many | OS append is atomic for writes under PIPE_BUF |
| SQLite | Many readers, one writer | WAL mode allows concurrent readers |
| YAML config | One | Treat as human-edited; lock during scripts |

For multi-process writers on plain files, add `fcntl.flock`
around the read-modify-write cycle, or move to SQLite.

## Anti-Patterns

- **Database-as-config**: Putting human-edited settings in
  SQLite. Reviewers cannot diff binary blobs in pull requests.
- **Markdown-as-database**: Storing 100k records as one file
  per record when every read does a directory scan. Move to
  SQLite once lookup-by-key dominates.
- **Direct overwrite**: Writing to the target file directly,
  skipping the tempfile dance. A crash mid-write corrupts the
  record.
- **Retention by deletion only**: No archive tier, so any
  pruning is destructive. The first wrongly-tuned policy
  takes data with it.
- **Schema in many places**: Defining the record shape in the
  template, the SQLite schema, and the JSON serializer
  separately. Each release drifts.
- **Append-log forever**: Letting a JSONL file grow without
  rotation. Tail latency degrades and tools that load the
  whole log run out of memory.

## Cross-Reference

See `template-patterns.md` for record shapes that are in
these backends, and `lifecycle-stages.md` for the maturity
transitions retention policies enforce.
