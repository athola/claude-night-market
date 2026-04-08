# Context Map Scanner v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Add five CodeSight-inspired capabilities to the
conserve context scanner: per-file blast radius, scan
caching, wiki knowledge articles, schema/model extraction,
and section queries.

**Architecture:** All features extend the existing
single-file `context_scanner.py`. New dataclasses,
functions, and CLI flags are appended following the
established pattern. Wiki generation writes to a
`.codesight/` directory. Cache writes to
`.codesight-cache.json`.

**Tech Stack:** Python stdlib only (pathlib, json,
hashlib, argparse, re, dataclasses). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-04-07-context-map-v2-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `plugins/conserve/scripts/context_scanner.py` | Modify | All five features |
| `plugins/conserve/tests/test_context_scanner.py` | Modify | Tests for all features |
| `plugins/conserve/skills/context-map/SKILL.md` | Modify | Document new CLI flags |

---

## Task 1: Blast Radius -- Data Structure and BFS

**Files:**
- Modify: `plugins/conserve/scripts/context_scanner.py:265` (after TokenEstimate)
- Modify: `plugins/conserve/tests/test_context_scanner.py` (append)

- [ ] **Step 1: Write failing tests for blast radius**

Append to `plugins/conserve/tests/test_context_scanner.py`:

```python
class TestBlastRadius:
    """Tests for per-file blast radius BFS."""

    def test_direct_dependents(self, tmp_path):
        """Blast radius shows files that directly import the target."""
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import core\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = context_scanner.build_import_graph(tmp_path)
        result = context_scanner.blast_radius(graph, "core.py")

        assert set(result.direct) == {"a.py", "b.py"}

    def test_transitive_dependents(self, tmp_path):
        """Blast radius includes 2nd+ degree dependents with via path."""
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = context_scanner.build_import_graph(tmp_path)
        result = context_scanner.blast_radius(graph, "core.py")

        assert result.direct == ["a.py"]
        assert len(result.transitive) == 1
        file, via = result.transitive[0]
        assert file == "b.py"
        assert via == "a.py"

    def test_no_dependents(self, tmp_path):
        """File with no importers has empty blast radius."""
        (tmp_path / "lonely.py").write_text("x = 1\n")

        graph = context_scanner.build_import_graph(tmp_path)
        result = context_scanner.blast_radius(graph, "lonely.py")

        assert result.direct == []
        assert result.transitive == []
        assert result.total_affected == 0

    def test_unknown_file_returns_empty(self, tmp_path):
        """Blast radius of a file not in the graph is empty."""
        (tmp_path / "a.py").write_text("x = 1\n")

        graph = context_scanner.build_import_graph(tmp_path)
        result = context_scanner.blast_radius(graph, "nonexistent.py")

        assert result.total_affected == 0

    def test_total_count(self, tmp_path):
        """total_affected is sum of direct and transitive."""
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import core\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = context_scanner.build_import_graph(tmp_path)
        result = context_scanner.blast_radius(graph, "core.py")

        assert result.total_affected == len(result.direct) + len(result.transitive)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestBlastRadius -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: FAIL with `AttributeError: module 'context_scanner' has no attribute 'blast_radius'`

- [ ] **Step 3: Add BlastResult dataclass and blast_radius function**

Insert after the `TokenEstimate` class (line ~265) in `context_scanner.py`:

```python
@dataclass
class BlastResult:
    """Result of a per-file blast radius analysis."""

    target: str
    direct: list[str] = field(default_factory=list)
    transitive: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total_affected(self) -> int:
        return len(self.direct) + len(self.transitive)
```

Insert after `detect_hot_files` (line ~1029) in `context_scanner.py`:

```python
def blast_radius(graph: ImportGraph, target: str) -> BlastResult:
    """BFS over imported_by to find all files affected by changing target.

    Returns direct dependents (depth 1) and transitive dependents
    (depth 2+) with the intermediate file they're reached through.
    """
    result = BlastResult(target=target)

    if target not in graph.imported_by:
        return result

    # BFS
    visited: set[str] = {target}
    # queue entries: (file, depth, via_file)
    queue: list[tuple[str, int, str]] = [
        (dep, 1, target) for dep in sorted(graph.imported_by.get(target, set()))
    ]

    while queue:
        current, depth, via = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        if depth == 1:
            result.direct.append(current)
        else:
            result.transitive.append((current, via))

        for next_dep in sorted(graph.imported_by.get(current, set())):
            if next_dep not in visited:
                queue.append((next_dep, depth + 1, current))

    result.direct.sort()
    result.transitive.sort()
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestBlastRadius -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/conserve/scripts/context_scanner.py plugins/conserve/tests/test_context_scanner.py
git commit -m "feat(conserve): add per-file blast radius BFS"
```

---

## Task 2: Blast Radius -- CLI Flag and Renderer

**Files:**
- Modify: `plugins/conserve/scripts/context_scanner.py:1555` (main function)
- Modify: `plugins/conserve/tests/test_context_scanner.py` (append)

- [ ] **Step 1: Write failing tests for blast CLI and rendering**

Append to `plugins/conserve/tests/test_context_scanner.py`:

```python
class TestBlastRadiusCLI:
    """Tests for --blast CLI flag and output rendering."""

    def test_blast_flag_produces_output(self, tmp_path, capsys):
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")

        exit_code = context_scanner.main(
            ["--blast", "core.py", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Blast Radius: core.py" in captured.out
        assert "a.py" in captured.out

    def test_blast_unknown_file_shows_no_dependents(self, tmp_path, capsys):
        (tmp_path / "a.py").write_text("x = 1\n")

        exit_code = context_scanner.main(
            ["--blast", "nope.py", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Direct dependents: 0" in captured.out

    def test_blast_shows_transitive_via(self, tmp_path, capsys):
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import a\n")

        exit_code = context_scanner.main(
            ["--blast", "core.py", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert "via" in captured.out.lower() or "a.py" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestBlastRadiusCLI -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: FAIL (unrecognized argument --blast)

- [ ] **Step 3: Add render_blast_radius and CLI flag**

Insert after `render_json` (line ~1547) in `context_scanner.py`:

```python
def render_blast_radius(result: BlastResult) -> str:
    """Render blast radius result as markdown."""
    lines = [
        f"# Blast Radius: {result.target}",
        f"Direct dependents: {len(result.direct)}"
        f" | Transitive: {len(result.transitive)}",
        "",
    ]

    if result.direct:
        lines.append("## Direct (imported by)")
        for f in result.direct:
            lines.append(f"  {f}")
        lines.append("")

    if result.transitive:
        lines.append("## Transitive (2nd+ degree)")
        for f, via in result.transitive:
            lines.append(f"  {f} (via {via})")
        lines.append("")

    if result.total_affected == 0:
        lines.append("No dependents found.")

    return "\n".join(lines)
```

In the `main()` function, add argument after the `--output` argument:

```python
    parser.add_argument(
        "--blast",
        type=str,
        default=None,
        metavar="FILE",
        help="Show blast radius for a specific file",
    )
```

In `main()`, add blast radius handling after `root.is_dir()` check, before
`result = scan_directory(root)`:

```python
    if args.blast:
        graph = build_import_graph(root)
        blast_file = args.blast
        br = blast_radius(graph, blast_file)
        output = render_blast_radius(br)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
        return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestBlastRadiusCLI -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: 3 passed

- [ ] **Step 5: Run all existing tests to verify no regressions**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py -v --override-ini="addopts=" 2>&1 | tail -10`
Expected: 91 passed (83 existing + 8 new)

- [ ] **Step 6: Commit**

```bash
git add plugins/conserve/scripts/context_scanner.py plugins/conserve/tests/test_context_scanner.py
git commit -m "feat(conserve): add --blast CLI flag for per-file blast radius"
```

---

## Task 3: Scan Caching

**Files:**
- Modify: `plugins/conserve/scripts/context_scanner.py` (new functions + CLI flag + main)
- Modify: `plugins/conserve/tests/test_context_scanner.py` (append)

- [ ] **Step 1: Write failing tests for caching**

Append to `plugins/conserve/tests/test_context_scanner.py`:

```python
class TestScanCaching:
    """Tests for scan result caching."""

    def test_compute_fingerprint_stable(self, tmp_path):
        """Same directory produces same fingerprint."""
        (tmp_path / "a.py").write_text("x = 1\n")
        fp1 = context_scanner.compute_fingerprint(tmp_path)
        fp2 = context_scanner.compute_fingerprint(tmp_path)
        assert fp1 == fp2

    def test_fingerprint_changes_on_new_file(self, tmp_path):
        """Adding a file changes the fingerprint."""
        (tmp_path / "a.py").write_text("x = 1\n")
        fp1 = context_scanner.compute_fingerprint(tmp_path)
        (tmp_path / "b.py").write_text("y = 2\n")
        fp2 = context_scanner.compute_fingerprint(tmp_path)
        assert fp1 != fp2

    def test_save_and_load_cache(self, tmp_path):
        """Cache round-trips through save/load."""
        (tmp_path / "a.py").write_text("x = 1\n")
        result = context_scanner.scan_directory(tmp_path)
        context_scanner.save_cache(tmp_path, result)

        cache_file = tmp_path / ".codesight-cache.json"
        assert cache_file.exists()

        loaded = context_scanner.load_cache(tmp_path)
        assert loaded is not None
        assert loaded.project_name == result.project_name
        assert loaded.total_files == result.total_files

    def test_load_cache_returns_none_when_missing(self, tmp_path):
        """No cache file returns None."""
        loaded = context_scanner.load_cache(tmp_path)
        assert loaded is None

    def test_load_cache_returns_none_on_fingerprint_mismatch(self, tmp_path):
        """Stale cache returns None."""
        (tmp_path / "a.py").write_text("x = 1\n")
        result = context_scanner.scan_directory(tmp_path)
        context_scanner.save_cache(tmp_path, result)

        # Change the project
        (tmp_path / "b.py").write_text("y = 2\n")

        loaded = context_scanner.load_cache(tmp_path)
        assert loaded is None

    def test_no_cache_flag_skips_cache(self, tmp_path, capsys):
        """--no-cache forces a fresh scan."""
        (tmp_path / "a.py").write_text("x = 1\n")

        # First scan creates cache
        context_scanner.main([str(tmp_path)])
        assert (tmp_path / ".codesight-cache.json").exists()

        # Second scan with --no-cache still works
        exit_code = context_scanner.main(
            ["--no-cache", str(tmp_path)]
        )
        assert exit_code == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestScanCaching -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: FAIL with `AttributeError: module 'context_scanner' has no attribute 'compute_fingerprint'`

- [ ] **Step 3: Implement caching functions**

Add `import hashlib` to the imports at the top of `context_scanner.py` (after `import json`).

Insert after the `blast_radius` function in `context_scanner.py`:

```python
# ---------------------------------------------------------------------------
# Scan Caching
# ---------------------------------------------------------------------------

_CACHE_VERSION = 1
_CACHE_FILENAME = ".codesight-cache.json"


def compute_fingerprint(root: Path) -> str:
    """Compute a cheap fingerprint for cache invalidation.

    Hashes: file count, max mtime, sorted top-level dir names.
    """
    root = root.resolve()
    file_count = 0
    max_mtime = 0.0
    top_dirs: list[str] = []

    for entry in sorted(root.iterdir()):
        if entry.name in EXCLUDED_DIRS or entry.name.startswith("."):
            continue
        if entry.is_dir():
            top_dirs.append(entry.name)
            for dirpath, dirs, files in _walk_limited(entry, max_depth=6):
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
                file_count += len(files)
                for f in files:
                    try:
                        mt = (Path(dirpath) / f).stat().st_mtime
                        if mt > max_mtime:
                            max_mtime = mt
                    except OSError:
                        pass
        elif entry.is_file():
            file_count += 1
            try:
                mt = entry.stat().st_mtime
                if mt > max_mtime:
                    max_mtime = mt
            except OSError:
                pass

    raw = f"{file_count}:{max_mtime:.6f}:{','.join(top_dirs)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_cache(root: Path, result: ScanResult) -> None:
    """Save scan result to cache file."""
    root = root.resolve()
    cache_path = root / _CACHE_FILENAME
    fingerprint = compute_fingerprint(root)

    data = {
        "version": _CACHE_VERSION,
        "fingerprint": fingerprint,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_result": json.loads(render_json(result)),
    }
    cache_path.write_text(json.dumps(data, indent=2))


def _rebuild_scan_result(data: dict) -> ScanResult:
    """Reconstruct a ScanResult from cached JSON data."""
    sr = data["scan_result"]
    directories = [
        DirectoryInfo(
            path=d["path"],
            file_count=d["file_count"],
            primary_language=d.get("primary_language"),
        )
        for d in sr.get("directories", [])
    ]
    ecosystems = []
    for eco in sr.get("ecosystems", []):
        ecosystems.append(
            EcosystemResult(
                name=eco["name"],
                package_manager=eco.get("package_manager"),
                dependencies=[
                    Dependency(
                        name=d["name"],
                        version=d.get("version"),
                        category=d.get("category", "runtime"),
                    )
                    for d in eco.get("dependencies", [])
                ],
                frameworks=[
                    FrameworkMatch(
                        name=f["name"],
                        locations=f.get("locations", []),
                        confidence=f.get("confidence", 1.0),
                    )
                    for f in eco.get("frameworks", [])
                ],
                entry_points=[
                    EntryPoint(path=e["path"], kind=e.get("kind", "main"))
                    for e in eco.get("entry_points", [])
                ],
            )
        )
    routes = [
        RouteInfo(method=r["method"], path=r["path"], file=r["file"])
        for r in sr.get("routes", [])
    ]
    env_vars = [
        EnvVarInfo(
            name=v["name"], file=v["file"], has_default=v.get("has_default", False)
        )
        for v in sr.get("env_vars", [])
    ]
    middleware = [
        MiddlewareInfo(name=m["name"], kind=m["kind"], file=m["file"])
        for m in sr.get("middleware", [])
    ]
    te_data = sr.get("token_savings", {})
    token_estimate = TokenEstimate(
        route_tokens=te_data.get("route_tokens", 0),
        hot_file_tokens=te_data.get("hot_file_tokens", 0),
        env_var_tokens=te_data.get("env_var_tokens", 0),
        file_scan_tokens=te_data.get("file_scan_tokens", 0),
    )
    hot_files = sr.get("hot_files", [])

    return ScanResult(
        project_name=sr["project_name"],
        total_files=sr["total_files"],
        directories=directories,
        ecosystems=ecosystems,
        config_files=sr.get("config_files", []),
        hot_files=hot_files,
        routes=routes,
        env_vars=env_vars,
        middleware=middleware,
        token_estimate=token_estimate,
    )


def load_cache(root: Path) -> ScanResult | None:
    """Load cached scan result if fingerprint matches."""
    root = root.resolve()
    cache_path = root / _CACHE_FILENAME

    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    if data.get("version") != _CACHE_VERSION:
        return None

    current_fp = compute_fingerprint(root)
    if data.get("fingerprint") != current_fp:
        return None

    return _rebuild_scan_result(data)
```

In the `main()` function, add `--no-cache` argument:

```python
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Force fresh scan, ignore cached results",
    )
```

In `main()`, replace `result = scan_directory(root)` with:

```python
    # Try cache first
    result = None
    if not args.no_cache:
        result = load_cache(root)

    if result is None:
        result = scan_directory(root)
        save_cache(root, result)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestScanCaching -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: 6 passed

- [ ] **Step 5: Run all tests for regression check**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py -v --override-ini="addopts=" 2>&1 | tail -10`
Expected: 97 passed

- [ ] **Step 6: Commit**

```bash
git add plugins/conserve/scripts/context_scanner.py plugins/conserve/tests/test_context_scanner.py
git commit -m "feat(conserve): add scan caching with fingerprint invalidation"
```

---

## Task 4: Schema/Model Extraction

**Files:**
- Modify: `plugins/conserve/scripts/context_scanner.py` (new dataclass, detector, renderer section)
- Modify: `plugins/conserve/tests/test_context_scanner.py` (append)

- [ ] **Step 1: Write failing tests for schema detection**

Append to `plugins/conserve/tests/test_context_scanner.py`:

```python
class TestSchemaDetection:
    """Tests for ORM model and schema extraction."""

    def test_detects_sqlalchemy_model(self, tmp_path):
        (tmp_path / "models.py").write_text(
            "from sqlalchemy.orm import DeclarativeBase\n"
            "class Base(DeclarativeBase): pass\n"
            "class User(Base):\n"
            "    __tablename__ = 'users'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    email = Column(String)\n"
            "    name = Column(String)\n"
        )
        schemas = context_scanner.detect_schemas(tmp_path)
        assert len(schemas) == 1
        assert schemas[0].name == "User"
        assert schemas[0].field_count >= 2

    def test_detects_django_model(self, tmp_path):
        (tmp_path / "models.py").write_text(
            "from django.db import models\n"
            "class Post(models.Model):\n"
            "    title = models.CharField(max_length=200)\n"
            "    body = models.TextField()\n"
            "    created = models.DateTimeField(auto_now_add=True)\n"
        )
        schemas = context_scanner.detect_schemas(tmp_path)
        assert len(schemas) == 1
        assert schemas[0].name == "Post"
        assert schemas[0].field_count >= 2

    def test_detects_pydantic_model(self, tmp_path):
        (tmp_path / "schemas.py").write_text(
            "from pydantic import BaseModel\n"
            "class UserCreate(BaseModel):\n"
            "    email: str\n"
            "    name: str\n"
            "    password: str\n"
        )
        schemas = context_scanner.detect_schemas(tmp_path)
        assert len(schemas) == 1
        assert schemas[0].name == "UserCreate"

    def test_detects_prisma_model(self, tmp_path):
        (tmp_path / "schema.prisma").write_text(
            "model User {\n"
            "  id    Int    @id @default(autoincrement())\n"
            "  email String @unique\n"
            "  name  String\n"
            "}\n"
        )
        schemas = context_scanner.detect_schemas(tmp_path)
        assert len(schemas) == 1
        assert schemas[0].name == "User"

    def test_no_models_returns_empty(self, tmp_path):
        (tmp_path / "utils.py").write_text("def helper(): pass\n")
        schemas = context_scanner.detect_schemas(tmp_path)
        assert schemas == []

    def test_skips_test_files(self, tmp_path):
        (tmp_path / "test_models.py").write_text(
            "class FakeUser(Base):\n"
            "    id = Column(Integer)\n"
        )
        schemas = context_scanner.detect_schemas(tmp_path)
        assert schemas == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestSchemaDetection -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: FAIL with `AttributeError: module 'context_scanner' has no attribute 'detect_schemas'`

- [ ] **Step 3: Implement SchemaModel dataclass and detect_schemas**

Add after the `BlastResult` dataclass in `context_scanner.py`:

```python
@dataclass
class SchemaModel:
    """A detected ORM model or schema definition."""

    name: str
    file: str
    field_count: int = 0
    framework: str = ""  # "SQLAlchemy" | "Django" | "Pydantic" | "Prisma"
```

Add `schemas: list[SchemaModel] = field(default_factory=list)` to the
`ScanResult` dataclass, after the `middleware` field.

Add `--no-schema` argument to `main()`:

```python
    parser.add_argument(
        "--no-schema",
        action="store_true",
        default=False,
        help="Skip schema/model extraction",
    )
```

Insert the detector function after the middleware detection section:

```python
# ---------------------------------------------------------------------------
# Schema/Model Extraction
# ---------------------------------------------------------------------------

# Python ORM base classes that indicate a model definition
_PYTHON_MODEL_BASES = {
    "Base": "SQLAlchemy",
    "db.Model": "SQLAlchemy",
    "DeclarativeBase": "SQLAlchemy",
    "models.Model": "Django",
    "Model": "Django",
    "BaseModel": "Pydantic",
}

_PYTHON_MODEL_RE = re.compile(
    r"^class\s+(\w+)\s*\(\s*("
    + "|".join(re.escape(b) for b in _PYTHON_MODEL_BASES)
    + r")\s*\)\s*:",
    re.MULTILINE,
)

# Prisma: model Name {
_PRISMA_MODEL_RE = re.compile(r"^model\s+(\w+)\s*\{", re.MULTILINE)

# Field patterns for counting
_PYTHON_FIELD_RE = re.compile(
    r"^\s+(\w+)\s*[=:]\s*"
    r"(Column|Field|models\.\w+Field|mapped_column"
    r"|Mapped\[|Optional\[|str|int|float|bool|list\[)",
    re.MULTILINE,
)
_PRISMA_FIELD_RE = re.compile(r"^\s+(\w+)\s+\w+", re.MULTILINE)


def _count_fields_python(body: str) -> int:
    """Count field definitions in a Python class body."""
    return len(_PYTHON_FIELD_RE.findall(body))


def _count_fields_prisma(body: str) -> int:
    """Count field definitions in a Prisma model body."""
    count = 0
    for line in body.strip().splitlines():
        line = line.strip()
        # Skip empty lines, comments, decorators (@id, @@)
        if not line or line.startswith("//") or line.startswith("@@"):
            continue
        if _PRISMA_FIELD_RE.match(line):
            count += 1
    return count


def detect_schemas(root: Path) -> list[SchemaModel]:
    """Detect ORM model and schema definitions in the project."""
    root = root.resolve()
    schemas: list[SchemaModel] = []

    for dirpath, dirs, files in _walk_limited(root, max_depth=6):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for fname in files:
            fpath = Path(dirpath) / fname
            rel = str(fpath.relative_to(root))

            if _is_test_file(fname, rel):
                continue

            if fpath.suffix == ".prisma":
                try:
                    content = fpath.read_text(errors="replace")
                except OSError:
                    continue
                for match in _PRISMA_MODEL_RE.finditer(content):
                    name = match.group(1)
                    # Extract body between { and }
                    start = match.end()
                    brace_depth = 1
                    end = start
                    while end < len(content) and brace_depth > 0:
                        if content[end] == "{":
                            brace_depth += 1
                        elif content[end] == "}":
                            brace_depth -= 1
                        end += 1
                    body = content[start : end - 1]
                    schemas.append(
                        SchemaModel(
                            name=name,
                            file=rel,
                            field_count=_count_fields_prisma(body),
                            framework="Prisma",
                        )
                    )

            elif fpath.suffix in (".py", ".pyi"):
                try:
                    content = fpath.read_text(errors="replace")
                except OSError:
                    continue
                for match in _PYTHON_MODEL_RE.finditer(content):
                    name = match.group(1)
                    base = match.group(2)
                    framework = _PYTHON_MODEL_BASES.get(base, "Unknown")
                    # Extract class body: from match end to next class or EOF
                    start = match.end()
                    next_class = re.search(
                        r"\n(?=class\s)", content[start:]
                    )
                    if next_class:
                        body = content[start : start + next_class.start()]
                    else:
                        body = content[start:]
                    schemas.append(
                        SchemaModel(
                            name=name,
                            file=rel,
                            field_count=_count_fields_python(body),
                            framework=framework,
                        )
                    )

    schemas.sort(key=lambda s: s.name)
    return schemas
```

In `scan_directory()`, add schema detection after the middleware detection call
(only if not opted out -- but `scan_directory` doesn't know about CLI flags,
so always detect; the CLI handles opt-out in rendering). Add near the end of
`scan_directory`, before `return result`:

```python
    result.schemas = detect_schemas(root)
```

In `render_markdown`, add a schemas section after the middleware section:

```python
    # Schemas section
    if result.schemas:
        lines.append("## Models/Schemas")
        lines.append("")
        shown = result.schemas[:8]
        for s in shown:
            fields = f"({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  {s.name:<16} {s.file} {fields}")
        if len(result.schemas) > 8:
            lines.append(f"  ...{len(result.schemas) - 8} more")
        lines.append("")
```

In `render_json`, add schemas to the JSON output dict:

```python
        "schemas": [
            {
                "name": s.name,
                "file": s.file,
                "field_count": s.field_count,
                "framework": s.framework,
            }
            for s in result.schemas
        ],
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestSchemaDetection -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: 6 passed

- [ ] **Step 5: Run all tests for regression check**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py -v --override-ini="addopts=" 2>&1 | tail -10`
Expected: 103 passed

- [ ] **Step 6: Commit**

```bash
git add plugins/conserve/scripts/context_scanner.py plugins/conserve/tests/test_context_scanner.py
git commit -m "feat(conserve): add schema/model extraction for ORM detection"
```

---

## Task 5: Wiki Knowledge Articles

**Files:**
- Modify: `plugins/conserve/scripts/context_scanner.py` (topic classifier, wiki generator, CLI flags)
- Modify: `plugins/conserve/tests/test_context_scanner.py` (append)

- [ ] **Step 1: Write failing tests for wiki generation**

Append to `plugins/conserve/tests/test_context_scanner.py`:

```python
class TestWikiGeneration:
    """Tests for .codesight/ wiki article generation."""

    def test_generates_index(self, tmp_path):
        (tmp_path / "auth.py").write_text("import jwt\n")
        (tmp_path / "models.py").write_text(
            "class User(Base):\n    id = Column(Integer)\n"
        )
        result = context_scanner.scan_directory(tmp_path)
        context_scanner.generate_wiki(tmp_path, result)

        index = tmp_path / ".codesight" / "INDEX.md"
        assert index.exists()
        content = index.read_text()
        assert "auth" in content.lower() or "database" in content.lower()

    def test_generates_auth_article(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth.py").write_text(
            "import jwt\ndef login(): pass\n"
        )
        (src / "middleware.py").write_text(
            "def verify_token(): pass\n"
        )
        result = context_scanner.scan_directory(tmp_path)
        context_scanner.generate_wiki(tmp_path, result)

        auth_article = tmp_path / ".codesight" / "auth.md"
        assert auth_article.exists()
        content = auth_article.read_text()
        assert "auth.py" in content

    def test_generates_api_article_from_routes(self, tmp_path):
        (tmp_path / "routes.py").write_text(
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
            '@app.get("/users")\n'
            "def get_users(): pass\n"
        )
        result = context_scanner.scan_directory(tmp_path)
        context_scanner.generate_wiki(tmp_path, result)

        api_article = tmp_path / ".codesight" / "api.md"
        assert api_article.exists()
        content = api_article.read_text()
        assert "/users" in content

    def test_skips_empty_topics(self, tmp_path):
        (tmp_path / "utils.py").write_text("def helper(): pass\n")
        result = context_scanner.scan_directory(tmp_path)
        context_scanner.generate_wiki(tmp_path, result)

        wiki_dir = tmp_path / ".codesight"
        # Should have INDEX.md at minimum, but no topic files
        # if no patterns match
        if wiki_dir.exists():
            articles = [
                f.name for f in wiki_dir.iterdir()
                if f.name != "INDEX.md"
            ]
            # No topic articles for a plain utils file
            assert len(articles) == 0

    def test_no_wiki_flag(self, tmp_path, capsys):
        (tmp_path / "auth.py").write_text("import jwt\n")
        context_scanner.main(["--no-wiki", str(tmp_path)])

        wiki_dir = tmp_path / ".codesight"
        assert not wiki_dir.exists()

    def test_wiki_only_flag(self, tmp_path, capsys):
        (tmp_path / "auth.py").write_text("import jwt\n")
        exit_code = context_scanner.main(
            ["--wiki-only", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert (tmp_path / ".codesight").exists()
        # wiki-only should not print the full context map
        assert "## Structure" not in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestWikiGeneration -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: FAIL with `AttributeError: module 'context_scanner' has no attribute 'generate_wiki'`

- [ ] **Step 3: Implement topic classification and wiki generation**

Add a `WikiArticle` dataclass after `SchemaModel`:

```python
@dataclass
class WikiArticle:
    """A generated wiki knowledge article."""

    topic: str
    title: str
    files: list[str] = field(default_factory=list)
    content: str = ""
```

Insert the wiki generation functions after `detect_schemas`:

```python
# ---------------------------------------------------------------------------
# Wiki Knowledge Articles
# ---------------------------------------------------------------------------

# Topic patterns: (topic_name, title, path_patterns, import_patterns)
_TOPIC_PATTERNS: list[tuple[str, str, list[str], list[str]]] = [
    (
        "auth",
        "Authentication & Authorization",
        ["auth", "login", "session", "permission", "jwt", "oauth", "token"],
        ["jwt", "oauth", "passlib", "bcrypt", "flask_login", "authlib"],
    ),
    (
        "database",
        "Database & Models",
        ["model", "schema", "migration", "orm", "database", "db"],
        ["sqlalchemy", "django.db", "prisma", "sqlx", "diesel", "gorm",
         "drizzle", "mongoose", "sequelize", "typeorm"],
    ),
    (
        "api",
        "API Routes & Endpoints",
        ["route", "endpoint", "handler", "controller", "view", "api"],
        [],  # Populated from detected routes
    ),
    (
        "config",
        "Configuration & Environment",
        ["config", "setting", "env", ".env"],
        ["dotenv", "pydantic_settings", "decouple", "environ"],
    ),
    (
        "testing",
        "Testing",
        ["test", "spec", "fixture", "conftest", "factory"],
        ["pytest", "unittest", "jest", "vitest", "mocha"],
    ),
]


def classify_topics(
    result: ScanResult,
) -> dict[str, list[str]]:
    """Classify project files into topic clusters.

    Returns a dict of topic_name -> list of relevant file paths.
    """
    topics: dict[str, list[str]] = defaultdict(list)

    # Collect all source file paths from directory info
    all_files: list[str] = []
    for d in result.directories:
        all_files.append(d.path)

    # Classify files by route presence
    route_files = {r.file for r in result.routes}
    for rf in route_files:
        topics["api"].append(rf)

    # Classify files by env var presence
    env_files = {v.file for v in result.env_vars}
    for ef in env_files:
        if ef not in topics["config"]:
            topics["config"].append(ef)

    # Classify by middleware
    for mw in result.middleware:
        if mw.kind in ("auth", "session"):
            topics["auth"].append(mw.file)
        elif mw.kind == "logging":
            topics["config"].append(mw.file)

    # Classify schemas
    for s in getattr(result, "schemas", []):
        if s.file not in topics["database"]:
            topics["database"].append(s.file)

    # Classify hot files by path patterns
    for hf in result.hot_files:
        hf_lower = hf.lower()
        for topic, _title, path_pats, _imp_pats in _TOPIC_PATTERNS:
            if any(pat in hf_lower for pat in path_pats):
                if hf not in topics[topic]:
                    topics[topic].append(hf)

    # Deduplicate and sort
    for topic in topics:
        topics[topic] = sorted(set(topics[topic]))

    # Remove empty topics
    return {k: v for k, v in topics.items() if v}


def _render_wiki_article(
    topic: str, title: str, files: list[str], result: ScanResult
) -> str:
    """Render a single wiki article as markdown."""
    lines = [f"# {title}", ""]

    if topic == "api" and result.routes:
        # Group routes by file
        by_file: dict[str, list[RouteInfo]] = defaultdict(list)
        for r in result.routes:
            by_file[r.file].append(r)
        for rfile, routes in sorted(by_file.items()):
            lines.append(f"## {rfile}")
            for r in routes:
                lines.append(f"  {r.method:<7} {r.path}")
            lines.append("")
    elif topic == "database" and getattr(result, "schemas", []):
        for s in result.schemas:
            fields = f" ({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  - {s.name}: {s.file}{fields}")
        lines.append("")

    if topic == "config" and result.env_vars:
        lines.append("## Environment Variables")
        for v in result.env_vars[:20]:
            default = " (has default)" if v.has_default else " (required)"
            lines.append(f"  - {v.name}{default}")
        if len(result.env_vars) > 20:
            lines.append(f"  ...{len(result.env_vars) - 20} more")
        lines.append("")

    lines.append("## Related Files")
    lines.append("")
    for f in files[:20]:
        lines.append(f"  - {f}")
    if len(files) > 20:
        lines.append(f"  ...{len(files) - 20} more")
    lines.append("")

    return "\n".join(lines)


def generate_wiki(root: Path, result: ScanResult) -> None:
    """Generate .codesight/ wiki directory with per-topic articles."""
    root = root.resolve()
    topics = classify_topics(result)

    if not topics:
        return

    wiki_dir = root / ".codesight"
    wiki_dir.mkdir(exist_ok=True)

    # Generate per-topic articles
    generated: list[tuple[str, str]] = []
    for topic, files in sorted(topics.items()):
        title = topic
        for t_name, t_title, _pats, _imps in _TOPIC_PATTERNS:
            if t_name == topic:
                title = t_title
                break
        content = _render_wiki_article(topic, title, files, result)
        article_path = wiki_dir / f"{topic}.md"
        article_path.write_text(content)
        generated.append((topic, title))

    # Generate INDEX.md
    index_lines = [
        f"# Context Wiki: {result.project_name}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Topics",
        "",
    ]
    for topic, title in generated:
        count = len(topics[topic])
        index_lines.append(f"  - [{title}]({topic}.md) ({count} files)")
    index_lines.append("")

    (wiki_dir / "INDEX.md").write_text("\n".join(index_lines))
```

Add CLI flags in `main()`:

```python
    parser.add_argument(
        "--no-wiki",
        action="store_true",
        default=False,
        help="Skip wiki article generation",
    )
    parser.add_argument(
        "--wiki-only",
        action="store_true",
        default=False,
        help="Generate wiki articles only, no stdout output",
    )
```

In `main()`, add wiki generation after the scan (after the cache
save, before the render):

```python
    # Wiki generation
    if not args.no_wiki or args.wiki_only:
        generate_wiki(root, result)

    if args.wiki_only:
        return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestWikiGeneration -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: 6 passed

- [ ] **Step 5: Run all tests for regression check**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py -v --override-ini="addopts=" 2>&1 | tail -10`
Expected: 109 passed

- [ ] **Step 6: Commit**

```bash
git add plugins/conserve/scripts/context_scanner.py plugins/conserve/tests/test_context_scanner.py
git commit -m "feat(conserve): add wiki knowledge article generation"
```

---

## Task 6: Section Queries

**Files:**
- Modify: `plugins/conserve/scripts/context_scanner.py` (render_section, CLI flag)
- Modify: `plugins/conserve/tests/test_context_scanner.py` (append)

- [ ] **Step 1: Write failing tests for section queries**

Append to `plugins/conserve/tests/test_context_scanner.py`:

```python
class TestSectionQueries:
    """Tests for --section flag to output individual sections."""

    def test_section_routes(self, tmp_path, capsys):
        (tmp_path / "app.py").write_text(
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
            '@app.get("/users")\n'
            "def get_users(): pass\n"
        )
        exit_code = context_scanner.main(
            ["--section", "routes", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "/users" in captured.out
        # Should NOT have the full map sections
        assert "## Structure" not in captured.out

    def test_section_env(self, tmp_path, capsys):
        (tmp_path / "config.py").write_text(
            'DB_URL = os.environ.get("DATABASE_URL", "sqlite:///db")\n'
        )
        exit_code = context_scanner.main(
            ["--section", "env", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "DATABASE_URL" in captured.out

    def test_section_structure(self, tmp_path, capsys):
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1\n")

        exit_code = context_scanner.main(
            ["--section", "structure", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "src" in captured.out

    def test_section_hot_files(self, tmp_path, capsys):
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import core\n")
        (tmp_path / "c.py").write_text("import core\n")

        exit_code = context_scanner.main(
            ["--section", "hot-files", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "core.py" in captured.out

    def test_section_invalid_name(self, tmp_path, capsys):
        exit_code = context_scanner.main(
            ["--section", "bogus", str(tmp_path)]
        )

        assert exit_code == 1

    def test_section_deps(self, tmp_path, capsys):
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            "dependencies = [\n"
            '    "fastapi>=0.100.0",\n'
            "]\n"
        )
        exit_code = context_scanner.main(
            ["--section", "deps", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "fastapi" in captured.out

    def test_section_models(self, tmp_path, capsys):
        (tmp_path / "models.py").write_text(
            "class User(Base):\n"
            "    id = Column(Integer)\n"
            "    name = Column(String)\n"
        )
        exit_code = context_scanner.main(
            ["--section", "models", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "User" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestSectionQueries -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: FAIL (unrecognized argument --section)

- [ ] **Step 3: Implement render_section and CLI flag**

Insert after `render_blast_radius` in `context_scanner.py`:

```python
_VALID_SECTIONS = {
    "structure", "deps", "routes", "hot-files",
    "env", "middleware", "models", "frameworks",
}


def render_section(result: ScanResult, section: str) -> str | None:
    """Render a single section of the context map.

    Returns None if the section name is invalid.
    """
    if section not in _VALID_SECTIONS:
        return None

    lines: list[str] = []

    if section == "structure":
        for d in result.directories[:12]:
            lang = f" ({d.primary_language})" if d.primary_language else ""
            lines.append(f"  {d.path:<20} {d.file_count} files{lang}")
        if result.truncated_dirs:
            lines.append(f"  ...{result.truncated_dirs} more directories")

    elif section == "deps":
        for eco in result.ecosystems:
            pm = f" ({eco.package_manager})" if eco.package_manager else ""
            lines.append(f"## {eco.name}{pm}")
            for dep in eco.dependencies[:12]:
                ver = f" {dep.version}" if dep.version else ""
                lines.append(f"  - {dep.name}{ver}")
            remaining = len(eco.dependencies) - 12
            if remaining > 0:
                lines.append(f"  ...{remaining} more")
            lines.append("")

    elif section == "routes":
        for r in result.routes[:20]:
            lines.append(f"  {r.method:<7} {r.path:<30} ({r.file})")
        if len(result.routes) > 20:
            lines.append(f"  ...{len(result.routes) - 20} more")

    elif section == "hot-files":
        graph = result.import_graph
        for hf in result.hot_files[:15]:
            count = len(graph.imported_by.get(hf, set())) if graph else 0
            lines.append(f"  - {hf} ({count} importers)")
        if len(result.hot_files) > 15:
            lines.append(f"  ...{len(result.hot_files) - 15} more")

    elif section == "env":
        for v in result.env_vars[:20]:
            default = " (has default)" if v.has_default else " (required)"
            lines.append(f"  - {v.name}{default}")
        if len(result.env_vars) > 20:
            lines.append(f"  ...{len(result.env_vars) - 20} more")

    elif section == "middleware":
        for m in result.middleware:
            lines.append(f"  - {m.name} [{m.kind}] ({m.file})")

    elif section == "models":
        schemas = getattr(result, "schemas", [])
        for s in schemas[:12]:
            fields = f" ({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  {s.name:<16} {s.file}{fields}")
        if len(schemas) > 12:
            lines.append(f"  ...{len(schemas) - 12} more")

    elif section == "frameworks":
        for fw in result.all_frameworks:
            locs = ", ".join(fw.locations[:3])
            lines.append(f"  - {fw.name} ({locs})")

    return "\n".join(lines) if lines else "(empty)"
```

Add CLI flag in `main()`:

```python
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        metavar="NAME",
        help=(
            "Output a single section: "
            + ", ".join(sorted(_VALID_SECTIONS))
        ),
    )
```

In `main()`, add section handling after the blast radius check
and before the full scan render:

```python
    if args.section:
        output = render_section(result, args.section)
        if output is None:
            print(
                f"Error: unknown section '{args.section}'. "
                f"Valid: {', '.join(sorted(_VALID_SECTIONS))}",
                file=sys.stderr,
            )
            return 1
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
        return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py::TestSectionQueries -v --override-ini="addopts=" 2>&1 | tail -20`
Expected: 7 passed

- [ ] **Step 5: Run all tests for regression check**

Run: `cd plugins/conserve && python3 -m pytest tests/test_context_scanner.py -v --override-ini="addopts=" 2>&1 | tail -10`
Expected: 116 passed

- [ ] **Step 6: Commit**

```bash
git add plugins/conserve/scripts/context_scanner.py plugins/conserve/tests/test_context_scanner.py
git commit -m "feat(conserve): add --section flag for targeted context queries"
```

---

## Task 7: Update Skill Definition

**Files:**
- Modify: `plugins/conserve/skills/context-map/SKILL.md`

- [ ] **Step 1: Update SKILL.md with new CLI capabilities**

Update the `## Options` and `## What It Detects` sections in
`plugins/conserve/skills/context-map/SKILL.md` to reflect the new flags:

Add to the `## What It Detects` table:

```markdown
| **Models/Schemas** | SQLAlchemy, Django, Pydantic, Prisma definitions |
```

Replace the `## Options` section with:

```markdown
## Options

### Output
- `--format json` for structured output
- `--max-tokens N` to adjust output size (default: 5000)
- `--output FILE` to save to a file

### Modes
- `--blast FILE` to show blast radius for a specific file
- `--section NAME` to output a single section
  (routes, deps, env, hot-files, models, structure,
  middleware, frameworks)
- `--wiki-only` to generate wiki articles without stdout

### Opt-out
- `--no-cache` to force a fresh scan
- `--no-wiki` to skip wiki article generation
- `--no-schema` to skip schema/model extraction
```

Add a new section after `## Example Output`:

```markdown
## Wiki Articles

The scanner generates per-topic knowledge articles in
`.codesight/` for selective context loading:

```bash
python3 scanner.py .
# Creates .codesight/INDEX.md, auth.md, database.md, etc.
```

Load only what you need per session instead of the full map:

```bash
python3 scanner.py --section routes .
# ~200 tokens vs ~5,000 for the full map
```
```

- [ ] **Step 2: Commit**

```bash
git add plugins/conserve/skills/context-map/SKILL.md
git commit -m "docs(conserve): update context-map skill with v2 capabilities"
```

---

## Dependency Graph

```
T1 (Blast BFS)
  └── T2 (Blast CLI + renderer)

T3 (Caching) [independent]

T4 (Schema extraction) [independent]
  └── T5 (Wiki articles) [uses schemas from T4]
       └── T6 (Section queries) [uses all data]

T7 (Skill docs) [after all features]
```

### Parallelization

| Batch | Tasks | Notes |
|-------|-------|-------|
| 1 | T1, T3, T4 | All independent foundations |
| 2 | T2, T5 | T2 needs T1; T5 needs T4 |
| 3 | T6 | Needs all scan data available |
| 4 | T7 | Documentation after all features |
