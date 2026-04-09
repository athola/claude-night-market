# Context Map Scanner - Implementation Plan v1.0

**Date**: 2026-04-07
**Spec**: docs/context-map-specification.md

## Architecture

### Component Diagram

```
plugins/conserve/
  scripts/
    context_scanner.py       # Core: scanner + detectors + renderer
  skills/
    context-map/
      SKILL.md               # Skill orchestration
  tests/
    test_context_scanner.py  # Unit + integration tests
```

Single-file architecture. All scanner logic lives in one
script (`context_scanner.py`) following the established
conserve pattern (see `detect_duplicates.py`). No package
structure, no imports beyond stdlib.

### Data Flow

```
Project Directory
      │
      ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  File Tree  │────▶│  Detectors   │────▶│ Summarizer  │
│  Walker     │     │  (per-eco)   │     │ (truncate)  │
└─────────────┘     └──────────────┘     └─────────────┘
                                               │
                                               ▼
                                         ┌─────────────┐
                                         │  Renderer   │
                                         │  (md/json)  │
                                         └─────────────┘
```

### Key Data Structures

```python
@dataclass
class DirectoryInfo:
    path: str
    file_count: int
    primary_language: str | None

@dataclass
class Dependency:
    name: str
    version: str | None
    category: str  # "runtime" | "dev"

@dataclass
class FrameworkMatch:
    name: str
    locations: list[str]
    confidence: float  # 0.0-1.0

@dataclass
class EntryPoint:
    path: str
    kind: str  # "main" | "cli" | "app" | "server"

@dataclass
class ScanResult:
    project_name: str
    total_files: int
    directories: list[DirectoryInfo]
    frameworks: list[FrameworkMatch]
    dependencies: list[Dependency]
    entry_points: list[EntryPoint]
    config_files: list[str]
```

## Task Breakdown

### Phase 1: Core Scanner (4 tasks)

#### T001: File Tree Walker

**Description**: Implement `scan_directory()` that walks
the project tree, respects gitignore-style exclusions,
and collects per-directory file counts by extension.

**Dependencies**: None
**Effort**: M
**Files**: `scripts/context_scanner.py`, `tests/test_context_scanner.py`

**Acceptance Criteria**:

- [ ] Walks directory tree using `os.scandir` recursively
- [ ] Skips default exclusions (.git, node_modules, .venv,
      __pycache__, .tox, .mypy_cache, .pytest_cache, dist,
      build, .eggs, *.egg-info)
- [ ] Collects file count and primary extension per
      top-level directory
- [ ] Returns list of `DirectoryInfo` sorted by file count
      descending

**Test Cases**:

- Empty directory returns empty list
- Single file directory returns correct count
- Nested directories aggregate correctly
- Excluded directories are skipped
- Symlinks are not followed

#### T002: Python Ecosystem Detector

**Description**: Detect Python projects from pyproject.toml,
setup.py, setup.cfg, requirements.txt. Extract dependencies
and identify frameworks (FastAPI, Django, Flask, pytest, etc).

**Dependencies**: T001
**Effort**: M
**Files**: `scripts/context_scanner.py`, `tests/test_context_scanner.py`

**Acceptance Criteria**:

- [ ] Detects pyproject.toml and extracts `[project]`
      dependencies and optional-dependencies
- [ ] Detects requirements.txt and extracts package names
      with versions
- [ ] Identifies package manager (uv from uv.lock, poetry
      from poetry.lock, pip from requirements.txt)
- [ ] Identifies frameworks from dependency names using
      a known-frameworks lookup table
- [ ] Returns `FrameworkMatch` list and `Dependency` list

**Test Cases**:

- pyproject.toml with [project.dependencies]
- pyproject.toml with [tool.poetry.dependencies]
- requirements.txt with pinned versions
- Project with uv.lock detected as uv-managed
- Unknown dependencies listed without framework match

#### T003: Multi-Ecosystem Detectors

**Description**: Add detectors for Node (package.json),
Rust (Cargo.toml), Go (go.mod), and Java (pom.xml /
build.gradle). Each follows the same interface as the
Python detector.

**Dependencies**: T002 (uses same pattern)
**Effort**: L
**Files**: `scripts/context_scanner.py`, `tests/test_context_scanner.py`

**Acceptance Criteria**:

- [ ] Node: parse package.json for dependencies and
      devDependencies, detect npm/yarn/pnpm from lockfiles
- [ ] Rust: parse Cargo.toml [dependencies] section, detect
      key crates (tokio, serde, actix, rocket)
- [ ] Go: parse go.mod require block, detect key modules
      (gin, echo, fiber, cobra)
- [ ] Java: detect pom.xml or build.gradle presence, parse
      basic dependency declarations
- [ ] All detectors return consistent FrameworkMatch and
      Dependency types

**Test Cases**:

- package.json with nested deps
- Cargo.toml with features
- go.mod with indirect deps
- Multi-language project triggers all relevant detectors

#### T004: Entry Point Detection

**Description**: Identify likely application entry points
from file naming conventions and config declarations.

**Dependencies**: T001, T002
**Effort**: S
**Files**: `scripts/context_scanner.py`, `tests/test_context_scanner.py`

**Acceptance Criteria**:

- [ ] Detect `__main__.py`, `main.py`, `app.py`, `cli.py`,
      `server.py`, `manage.py` as Python entry points
- [ ] Detect `index.ts`, `index.js`, `main.ts`, `server.ts`,
      `app.ts` as Node entry points
- [ ] Detect `main.go`, `main.rs` as Go/Rust entry points
- [ ] Parse `[project.scripts]` from pyproject.toml
- [ ] Parse `"bin"` and `"main"` from package.json
- [ ] Return `EntryPoint` list with path and kind

**Test Cases**:

- Python project with cli.py and __main__.py
- Node project with bin in package.json
- No entry points returns empty list

### Phase 2: Output and CLI (3 tasks)

#### T005: Strategic Summarizer

**Description**: Implement `summarize()` that takes a
`ScanResult` and produces bounded output. Each section
has a configurable max-items limit. Excess items get
"...N more" indicators. Empty sections are omitted.

**Dependencies**: T001, T002, T003, T004
**Effort**: M
**Files**: `scripts/context_scanner.py`, `tests/test_context_scanner.py`

**Acceptance Criteria**:

- [ ] Default limits: 8 directories, 8 dependencies,
      6 frameworks, 5 entry points
- [ ] Items beyond limit shown as "...N more" line
- [ ] Sections with zero items omitted entirely
- [ ] Token estimation: count output characters / 4
- [ ] Total output stays under `--max-tokens` target
      (default 5000)

**Test Cases**:

- 20 directories truncated to 8 + "...12 more"
- Empty frameworks section omitted
- Token count within target for large project
- All sections empty produces minimal output

#### T006: Markdown and JSON Renderers

**Description**: Render `ScanResult` to markdown (default)
or JSON output format.

**Dependencies**: T005
**Effort**: S
**Files**: `scripts/context_scanner.py`, `tests/test_context_scanner.py`

**Acceptance Criteria**:

- [ ] Markdown output matches the format specified in
      the project brief (header, structure, dependencies,
      frameworks, entry points sections)
- [ ] JSON output produces a serializable dict matching
      the ScanResult structure
- [ ] Header includes project name, timestamp, file count,
      estimated token count
- [ ] Output is deterministic (same input = same output,
      ignoring timestamp)

**Test Cases**:

- Markdown output matches expected snapshot
- JSON output round-trips through json.loads
- Deterministic output (minus timestamp)

#### T007: CLI Interface

**Description**: Add argparse-based CLI with path, format,
max-tokens, and output arguments.

**Dependencies**: T006
**Effort**: S
**Files**: `scripts/context_scanner.py`, `tests/test_context_scanner.py`

**Acceptance Criteria**:

- [ ] `python context_scanner.py .` scans current directory
- [ ] `python context_scanner.py /path` scans given path
- [ ] `--format json` switches to JSON output
- [ ] `--max-tokens 3000` adjusts truncation limits
- [ ] `--output FILE` writes to file instead of stdout
- [ ] Invalid path exits with code 1 and error message
- [ ] `--help` shows usage

**Test Cases**:

- Default args scan cwd
- JSON format produces valid JSON
- Invalid path returns exit code 1
- Output file is written correctly

### Phase 3: Skill Integration (1 task)

#### T008: Context Map Skill

**Description**: Create the conserve skill that orchestrates
the scanner and registers it in openpackage.yml.

**Dependencies**: T007
**Effort**: S
**Files**: `skills/context-map/SKILL.md`, `openpackage.yml`

**Acceptance Criteria**:

- [ ] SKILL.md instructs Claude to run the scanner script
      and present the results
- [ ] Skill registered in openpackage.yml under skills
- [ ] Skill frontmatter includes name, description, version,
      tags, estimated_tokens
- [ ] Skill works when invoked as
      `Skill(conserve:context-map)`

## Dependency Graph

```
T001 (File Walker)
  ├── T002 (Python Detector)
  │     ├── T003 (Multi-Eco Detectors)
  │     └── T004 (Entry Points)
  │           └── T005 (Summarizer)
  │                 └── T006 (Renderers)
  │                       └── T007 (CLI)
  │                             └── T008 (Skill)
  └── T004 (Entry Points) [also depends on T001]
```

### Parallelization Opportunities

- T002 and T004 can start in parallel after T001
- T003 can start after T002 (uses same pattern)
- T005 requires all of T001-T004

### Execution Sequence

| Batch | Tasks | Parallel? |
|-------|-------|-----------|
| 1 | T001 | No (foundation) |
| 2 | T002, T004 | Yes (independent) |
| 3 | T003 | No (extends T002 pattern) |
| 4 | T005 | No (needs all scan results) |
| 5 | T006, T007 | Sequential (T007 needs T006) |
| 6 | T008 | No (skill definition) |

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex parsing unreliable for TOML | Medium | Use line-by-line parsing for simple cases; complex TOML falls back to key detection |
| Large monorepos timeout | Low | os.scandir is fast; cap directory depth at 6 levels |
| Token estimate inaccurate | Low | Use conservative 4-chars-per-token; allow --max-tokens override |
