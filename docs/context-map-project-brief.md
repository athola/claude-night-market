# Context Map Scanner - Project Brief

## Problem Statement

AI assistants waste significant tokens exploring codebases.
A typical feature implementation triggers 20-60 Read calls
before writing any code, consuming 30-50K tokens on discovery
alone. The conserve plugin manages context pressure during
sessions (MECW, clear-context, token budgets) but nothing
pre-generates a compressed project overview to prevent
exploration waste in the first place.

CodeSight (github.com/Houseofmvps/codesight) demonstrates
that pre-scanned context maps reduce token usage by 7-12x
by giving AI assistants a roadmap before they start reading.

## Goals

1. Generate compressed context maps (under 5K tokens) that
   capture project structure, dependencies, frameworks,
   and key entry points
2. Detect common frameworks and patterns automatically
   (Python/uv, Node/npm, Rust/Cargo, Go modules, etc.)
3. Produce strategic summaries with truncation indicators
   ("...N more") to keep output bounded
4. Integrate as a conserve plugin skill with a Python
   backend for reliable scanning
5. Support incremental updates (re-scan only changed areas)

## Success Criteria

- [ ] Context map generates in under 10 seconds for repos
      up to 10K files
- [ ] Output stays under 5,000 tokens for medium projects
      (500-2000 files)
- [ ] Framework detection covers Python, Node, Rust, Go,
      and Java ecosystems
- [ ] Measured reduction in exploratory Read calls per session
      (target: 40% fewer reads)
- [ ] Skill integrates cleanly with existing conserve
      token-conservation workflow

## Constraints

- **Technical**: Must work as a Python module within the
  conserve plugin structure (pyproject.toml, uv, pytest).
  Must use existing plugin patterns (openpackage.yml
  registration).
- **Performance**: Scanning must be fast enough for
  session-start use. No external API calls.
- **Token budget**: The context map itself must be small
  enough that loading it saves more tokens than it costs.
- **Compatibility**: Must not conflict with existing
  conserve skills (context-optimization, smart-sourcing,
  token-conservation).

## Selected Approach: Python-backed Scanner

A Python module (`context_scanner.py`) in the conserve
plugin's `src/` directory, orchestrated by a new skill
(`context-map`). The scanner uses file-system analysis,
regex-based detection, and strategic summarization to
produce compressed markdown output.

### Architecture

```
plugins/conserve/
  skills/context-map/
    SKILL.md              # Skill definition
    modules/
      scanner-config.md   # Configuration options
      output-format.md    # Output format spec
  src/conserve/
    context_scanner.py    # Core scanner logic
    detectors/
      __init__.py
      base.py             # Base detector interface
      python.py           # Python/uv/pip detection
      node.py             # Node/npm/yarn detection
      rust.py             # Rust/Cargo detection
      go.py               # Go modules detection
  tests/
    test_context_scanner.py
    test_detectors.py
```

### Key Components

1. **Project Scanner**: Walks file tree, collects metadata
   (file counts by extension, directory structure, config
   files present).
2. **Framework Detectors**: Pluggable modules that identify
   frameworks from config files and import patterns.
   Each detector returns structured findings.
3. **Strategic Summarizer**: Compresses findings into
   bounded output. Truncates lists with "...N more"
   indicators. Omits empty sections.
4. **Context Map Renderer**: Produces the final markdown
   document with sections for structure, dependencies,
   frameworks, entry points, and patterns.

### Output Format

```markdown
# Context Map: <project-name>
Generated: <timestamp> | Files: <count> | Est. tokens: <N>

## Structure
src/           42 files (Python)
tests/         18 files
docs/           5 files
...3 more directories

## Dependencies
- fastapi 0.104.1 (web framework)
- pydantic 2.5.0 (validation)
- sqlalchemy 2.0.23 (ORM)
...12 more in pyproject.toml

## Frameworks Detected
- FastAPI (src/main.py, src/routes/)
- SQLAlchemy (src/models/)
- Pytest (tests/)

## Entry Points
- src/main.py (application entry)
- src/cli.py (CLI interface)

## Key Patterns
- Functional core, imperative shell
- Repository pattern (src/repos/)
- Dependency injection (src/deps.py)
```

## Trade-offs Accepted

- **No AST parsing**: Regex-based detection is less precise
  than AST but works across languages without heavy
  dependencies. Acceptable for summary-level accuracy.
- **No MCP server**: CodeSight offers an MCP server for
  focused queries. Deferred to future iteration since the
  skill-based approach covers the primary use case.
- **No wiki system**: CodeSight's wiki stores reusable
  docs. Deferred since memory-palace plugin already handles
  knowledge storage.
- **No watch mode**: Incremental updates via file mtime
  comparison are simpler than filesystem watchers.

## Out of Scope

- MCP server for context queries (future iteration)
- HTML dashboard output
- ORM schema parsing (8 parsers in CodeSight)
- Wiki knowledge base (covered by memory-palace plugin)
- Blast radius analysis (covered by pensive:blast-radius)
- IDE-specific output formats (.cursorrules, etc.)

## Next Steps

1. `/attune:specify` - Define detailed requirements
2. `/attune:blueprint` - Plan implementation phases
3. `/attune:execute` - Implement with TDD
