# Context Map Scanner v2 - Design Spec

**Date**: 2026-04-07
**Status**: Approved
**Base**: `plugins/conserve/scripts/context_scanner.py` (v1, 1616 lines)

## Overview

Extend the context map scanner with five CodeSight-inspired
capabilities for deeper token conservation. All new features
are enabled by default with `--no-*` opt-out flags.

**Reference**: [CodeSight](https://github.com/Houseofmvps/codesight)

## Feature 1: Per-File Blast Radius

BFS traversal over the existing import graph to find all
transitively affected files when a given file changes.

**CLI**:

```bash
python context_scanner.py --blast src/models/user.py .
```

**Output**:

```
# Blast Radius: src/models/user.py
Direct dependents: 5 | Transitive: 12

## Direct (imported by)
  src/routes/users.py
  src/routes/admin.py
  src/services/auth.py

## Transitive (2nd+ degree)
  src/main.py (via src/routes/__init__.py)
  ...4 more
```

**Implementation**: `blast_radius(graph, target)` performs
BFS over `graph.imported_by`, tracking depth. Returns a
dict of `{file: (depth, via_path)}`. The CLI flag
`--blast FILE` triggers this mode instead of a full scan.

**Data structure**:

```python
@dataclass
class BlastResult:
    target: str
    direct: list[str]           # depth 1
    transitive: list[tuple[str, str]]  # (file, via)
    total_affected: int
```

## Feature 2: Scan Caching

Cache scan results as JSON so repeated invocations return
instantly when nothing changed.

**Cache file**: `.codesight-cache.json` in project root.

```json
{
  "version": 1,
  "fingerprint": "a3f8c9...",
  "timestamp": "2026-04-08T03:15:00Z",
  "scan_result": { ... }
}
```

**Fingerprint**: Hash of (file count + max mtime across
top-level dirs + sorted top-level directory names). Cheap
to compute, catches additions/deletions/renames/most edits.

**Invalidation**: Fingerprint mismatch triggers full rescan.
`--no-cache` forces fresh scan and overwrites cache.

**Gitignore**: Scanner prints a suggestion if
`.codesight-cache.json` is not in `.gitignore`.

## Feature 3: Wiki Knowledge Articles

Per-topic markdown articles for selective context loading.
CodeSight's "Layer 2" reduction (59-131x compound savings).

**Output directory**: `.codesight/`

```
.codesight/
  INDEX.md          # Topic index with summaries
  auth.md           # Auth patterns, middleware, files
  database.md       # Models, schemas, migrations
  api.md            # Route groups by resource
  config.md         # Env vars, settings, feature flags
  testing.md        # Test layout, fixtures, commands
```

**Topic classification** (pattern-based, not semantic):

| Topic | Path/import patterns |
|-------|---------------------|
| auth | auth, login, jwt, oauth, session, permission |
| database | model, schema, migration, orm, database, db |
| api | Files containing detected routes |
| config | Env vars, settings files, .env, config |
| testing | test_, .test., .spec., conftest, fixtures |

Files can appear in multiple topics. Unclassifiable files
are omitted (covered by the main context map). Topics with
no matching files are not generated.

**CLI**:

```bash
# Default: generates .codesight/ alongside main map
python context_scanner.py .

# Opt out
python context_scanner.py . --no-wiki

# Wiki only (no stdout output)
python context_scanner.py . --wiki-only
```

## Feature 4: Schema/Model Extraction

Detect ORM model and schema definitions via regex patterns.

**Patterns detected**:

| Pattern | Framework |
|---------|-----------|
| `class X(Base):` / `class X(db.Model):` | SQLAlchemy |
| `class X(models.Model):` | Django |
| `model X {` | Prisma |
| `class X(BaseModel):` | Pydantic |
| `CREATE TABLE` | Raw SQL |

**Output in main context map**:

```
## Models/Schemas
  User      src/models/user.py    (5 fields)
  Post      src/models/post.py    (4 fields)
  ...3 more
```

**Field extraction**: Read the class body (up to next class
or dedent), pull column/field name tokens. Count only, no
type information in the summary (keeps output bounded).

**CLI**: Included by default. `--no-schema` to opt out.

## Feature 5: Section Queries

Output a single section of the context map for targeted,
low-token queries.

```bash
python context_scanner.py --section routes .
python context_scanner.py --section models .
python context_scanner.py --section env .
python context_scanner.py --section hot-files .
python context_scanner.py --section deps .
python context_scanner.py --section structure .
```

Uses cache when available. Returns only the requested
section (typically 100-500 tokens vs 5K for full map).

## CLI Summary

```
python context_scanner.py [PATH]              # full scan
python context_scanner.py --blast FILE PATH   # blast radius
python context_scanner.py --section NAME PATH # single section
python context_scanner.py --wiki-only PATH    # wiki only

Opt-out flags (all features on by default):
  --no-cache     Force fresh scan
  --no-wiki      Skip wiki article generation
  --no-schema    Skip schema/model extraction

Output flags:
  --format json  JSON output
  --max-tokens N Adjust truncation (default: 5000)
  --output FILE  Write to file instead of stdout
```

## Architecture

All features add to the existing single-file architecture
(`context_scanner.py`). No new source files except tests.

**New data structures**: `BlastResult`, `SchemaModel`,
`WikiArticle`, `CacheEntry`.

**New functions**:

| Function | Feature |
|----------|---------|
| `blast_radius(graph, target)` | BFS traversal |
| `render_blast_radius(result)` | Blast output |
| `compute_fingerprint(root)` | Cache key |
| `load_cache(root)` / `save_cache(root, result)` | Cache I/O |
| `classify_topics(result)` | Wiki topic assignment |
| `generate_wiki(root, result)` | Write .codesight/ |
| `detect_schemas(root)` | Schema extraction |
| `render_section(result, name)` | Section queries |

**Estimated growth**: ~500-600 lines added to
`context_scanner.py` (from 1616 to ~2200).

## Success Criteria

- [ ] `--blast FILE` shows direct and transitive dependents
      via BFS, with "via" path for transitive files
- [ ] Cached scan returns in under 100ms when fingerprint
      matches
- [ ] Wiki generates per-topic articles; loading one article
      costs under 500 tokens
- [ ] Schema detection covers SQLAlchemy, Django, Pydantic,
      and Prisma patterns
- [ ] `--section NAME` outputs a single section under 500
      tokens
- [ ] All existing 83 tests continue to pass
- [ ] New features have test coverage

## Constraints

- Stdlib only (no new dependencies)
- Single-file architecture maintained
- Regex-based detection (no AST parsing)
- Cache file is gitignored (generated artifact)
- Wiki directory is gitignored (generated artifact)

## Trade-offs Accepted

- **Schema extraction is lossy**: Regex can miss complex
  class bodies. Acceptable for summary-level accuracy.
- **Cache fingerprint is coarse**: Won't catch every edit.
  `--no-cache` is the escape hatch.
- **Topic classification is simple**: Path patterns, not
  NLP. False positives are cheap (extra file in an article),
  false negatives are expensive (missing context).
- **No incremental wiki updates**: Full regeneration each
  time. Acceptable since generation is fast (file I/O only).
