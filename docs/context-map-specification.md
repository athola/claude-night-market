# Context Map Scanner - Specification v0.1.0

**Author**: Alex Thola
**Date**: 2026-04-07
**Status**: Draft

## Overview

**Purpose**: Reduce token waste from codebase exploration by
pre-generating compressed context maps that give AI assistants
a project roadmap before they start reading files.

**Scope**:

- IN: Project structure scanning, framework detection,
  dependency summarization, entry point identification,
  strategic truncation, markdown output, CLI interface
- OUT: MCP server, HTML dashboards, ORM parsing, wiki
  system, watch mode, IDE-specific formats

**Stakeholders**:

- Claude Code users (primary: fewer tokens wasted on
  exploration)
- Plugin developers (secondary: understand project structure
  faster)

## Functional Requirements

### FR-001: Project Structure Scanning

**Description**: Walk a project's file tree and collect
metadata including file counts by extension, directory
depth, and top-level layout.

**Acceptance Criteria**:

- [ ] Given a project directory, when scanning, then
      produce a directory summary with file counts per
      top-level directory
- [ ] Given a project with .gitignore, when scanning, then
      respect .gitignore exclusions (skip node_modules,
      .venv, __pycache__, .git, etc.)
- [ ] Given a project with over 100 directories, when
      scanning, then truncate the listing to the top N
      directories by file count with "...M more" indicator
- [ ] Given an empty directory, when scanning, then omit
      it from the output

**Priority**: High
**Dependencies**: None
**Estimated Effort**: M

### FR-002: Framework Detection

**Description**: Identify frameworks and tooling from
configuration files and directory patterns. Each detector
is a pluggable function that receives a project root and
returns structured findings.

**Acceptance Criteria**:

- [ ] Given a project with pyproject.toml, when detecting,
      then identify Python ecosystem (uv, pip, poetry) and
      list key dependencies
- [ ] Given a project with package.json, when detecting,
      then identify Node ecosystem (npm, yarn, pnpm) and
      list key dependencies
- [ ] Given a project with Cargo.toml, when detecting,
      then identify Rust ecosystem and list key crates
- [ ] Given a project with go.mod, when detecting, then
      identify Go ecosystem and list key modules
- [ ] Given a project with pom.xml or build.gradle, when
      detecting, then identify Java/Kotlin ecosystem
- [ ] Given a multi-language project, when detecting, then
      report all detected ecosystems
- [ ] Given an unknown project type, when detecting, then
      produce a generic file-type summary without errors

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: L

### FR-003: Dependency Summarization

**Description**: Extract and summarize dependencies from
manifest files with strategic truncation. Show the most
important packages first, truncate the rest.

**Acceptance Criteria**:

- [ ] Given a pyproject.toml with 30 dependencies, when
      summarizing, then show the top 8 by relevance with
      versions, and indicate "...22 more"
- [ ] Given a package.json with devDependencies, when
      summarizing, then separate runtime from dev
      dependencies
- [ ] Given a Cargo.toml, when summarizing, then list
      crate names and versions with feature flags noted
- [ ] Given no manifest file, when summarizing, then omit
      the dependencies section entirely

**Priority**: High
**Dependencies**: FR-002
**Estimated Effort**: M

### FR-004: Entry Point Identification

**Description**: Detect likely entry points (main files,
CLI interfaces, app factories, route definitions) for
the project.

**Acceptance Criteria**:

- [ ] Given a Python project with `__main__.py` or
      `if __name__ == "__main__"`, when detecting, then
      list it as an entry point
- [ ] Given a project with `main.py`, `app.py`, `cli.py`,
      `server.py`, or `index.ts/js`, when detecting, then
      list them as entry points
- [ ] Given a pyproject.toml with `[project.scripts]`,
      when detecting, then list declared CLI entry points
- [ ] Given a package.json with `"main"` or `"bin"`, when
      detecting, then list those as entry points
- [ ] Given no identifiable entry points, when detecting,
      then omit the section

**Priority**: Medium
**Dependencies**: FR-001
**Estimated Effort**: S

### FR-005: Strategic Summarization

**Description**: Compress all findings into bounded markdown
output. Each section has a configurable maximum item count.
Excess items are summarized with "...N more" indicators.
Empty sections are omitted entirely.

**Acceptance Criteria**:

- [ ] Given scan results, when rendering, then total output
      stays under 5,000 tokens (estimated at ~4 chars/token)
- [ ] Given a section with more items than the configured
      limit, when rendering, then show top items and append
      "...N more" line
- [ ] Given a section with zero items, when rendering, then
      omit the entire section including its heading
- [ ] Given all sections, when rendering, then include a
      header line with project name, timestamp, file count,
      and estimated token count

**Priority**: High
**Dependencies**: FR-001, FR-002, FR-003, FR-004
**Estimated Effort**: M

### FR-006: CLI Interface

**Description**: Standalone Python script invocable as
`python context_scanner.py [path] [options]` with no
external dependencies beyond the Python standard library.

**Acceptance Criteria**:

- [ ] Given a path argument, when running, then scan that
      directory and print markdown to stdout
- [ ] Given no path argument, when running, then scan the
      current working directory
- [ ] Given `--format json` flag, when running, then output
      structured JSON instead of markdown
- [ ] Given `--max-tokens N` flag, when running, then
      adjust truncation limits to target N tokens
- [ ] Given `--output FILE` flag, when running, then write
      output to FILE instead of stdout
- [ ] Given an invalid path, when running, then exit with
      error code 1 and a clear message

**Priority**: High
**Dependencies**: FR-005
**Estimated Effort**: M

### FR-007: Skill Integration

**Description**: A conserve skill (`context-map`) that
instructs Claude to invoke the scanner script and
incorporate the results into session context.

**Acceptance Criteria**:

- [ ] Given a user invoking the skill, when activated, then
      run the scanner script and present the context map
- [ ] Given the skill is used at session start, when
      loading, then the context map reduces subsequent
      Read calls by providing a project overview
- [ ] Given the skill frontmatter, when registered, then
      it appears in the conserve plugin's openpackage.yml

**Priority**: Medium
**Dependencies**: FR-006
**Estimated Effort**: S

## Non-Functional Requirements

### NFR-001: Performance

- Scan completes in under 10 seconds for repos with up
  to 10,000 files
- File tree walk uses os.scandir (not os.walk with stat)
  for speed
- No external API calls or network requests

### NFR-002: Zero External Dependencies

- Scanner uses only Python standard library (pathlib,
  argparse, json, re, collections, dataclasses)
- Must run with Python 3.9+ (matches project baseline)
- No pip install required

### NFR-003: Token Efficiency

- Output under 5,000 tokens for projects with 500-2000
  files
- Output under 2,000 tokens for small projects (under
  100 files)
- The context map must save more tokens than it costs
  to load

### NFR-004: Accuracy

- Framework detection should have over 90% precision
  (few false positives) on common project types
- Recall can be lower (missing a framework is acceptable;
  misidentifying one is not)

### NFR-005: Extensibility

- Adding a new framework detector requires adding one
  function, not modifying existing code
- Detector registry uses a simple list or decorator
  pattern

## Technical Constraints

**Language**: Python 3.9+, stdlib only
**Location**: `plugins/conserve/scripts/context_scanner.py`
**Testing**: pytest, matching conserve plugin test patterns
**Pattern**: Follow `detect_duplicates.py` structure (CLI
script, dataclasses, argparse, JSON/text output)

## Out of Scope (v1)

- AST parsing for any language
- MCP server integration
- ORM schema detection
- HTML or dashboard output
- Wiki knowledge base
- Watch mode or filesystem monitoring
- Incremental scanning (deferred to v2)
- IDE-specific output formats

## Dependency Graph

```
FR-001 (Structure Scan)
  ├── FR-002 (Framework Detection)
  │     └── FR-003 (Dependency Summary)
  ├── FR-004 (Entry Points)
  └── FR-005 (Strategic Summarization)
        └── FR-006 (CLI Interface)
              └── FR-007 (Skill Integration)
```

## Acceptance Testing Strategy

1. **Unit tests**: Each detector tested with fixture
   directories containing minimal config files
2. **Integration test**: Full scan of the night-market
   repo itself, verifying output structure and token count
3. **Regression test**: Snapshot-based test comparing
   output against a known-good baseline
