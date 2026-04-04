# Cartograph Plugin - Specification v0.1.0

**Author**: Alex Thola
**Date**: 2026-04-03
**Status**: Draft

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-04-03 | Alex | Initial draft |

## Overview

**Purpose**: A Claude Code plugin that analyzes codebases and
generates visual diagrams (architecture, data flow, workflow,
dependency) rendered via the Mermaid Chart MCP server.

**Scope**:

- **IN**: Code analysis, structural model extraction, Mermaid
  diagram generation, MCP rendering for 5 diagram types
  (architecture, data-flow, dependency, workflow, class)
- **OUT**: Interactive editing, screenshot annotation, desktop
  app, custom rendering engines

**Stakeholders**:

- Developers: understand unfamiliar codebases visually
- Reviewers: see architecture at a glance during PR review
- Maintainers: document system structure with generated diagrams

## Functional Requirements

### FR-001: Plugin Structure

**Description**: Create a new `cartograph` plugin following
the night-market plugin conventions with plugin.json, skills,
agents, and commands directories.

**Acceptance Criteria**:

- [ ] Given the plugins directory, when cartograph is installed,
  then `plugins/cartograph/.claude-plugin/plugin.json` exists
  and passes `validate_plugin.py`
- [ ] Given the plugin, when listed, then it registers at least
  1 command, 5 skills, and 1 agent

**Priority**: High
**Dependencies**: None
**Estimated Effort**: S

### FR-002: Codebase Explorer Agent

**Description**: An agent that explores a codebase (or scoped
subset) and produces a structural model as JSON. The model
captures modules, imports, exports, function signatures, and
relationships between components.

**Acceptance Criteria**:

- [ ] Given a Python codebase path, when the explorer agent
  runs, then it produces a JSON model with `modules`,
  `imports`, `exports`, and `relationships` keys
- [ ] Given a scope filter (e.g., "plugins/sanctum"), when
  exploring, then only that subtree is analyzed
- [ ] Given a codebase with no Python files in scope, when
  exploring, then it returns an empty model with a warning

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: M

### FR-003: Architecture Diagram Skill

**Description**: A skill that generates a Mermaid flowchart
or architecture-beta diagram showing high-level component
relationships from a structural model or codebase analysis.

**Acceptance Criteria**:

- [ ] Given a structural model, when generating an architecture
  diagram, then valid Mermaid syntax is produced
- [ ] Given valid Mermaid syntax, when rendering via MCP, then
  `validate_and_render_mermaid_diagram` returns a diagram image
- [ ] Given no structural model, when invoked directly, then
  the skill dispatches the explorer agent first

**Priority**: High
**Dependencies**: FR-002
**Estimated Effort**: M

### FR-004: Data Flow Diagram Skill

**Description**: A skill that generates Mermaid sequence or
flowchart diagrams showing how data moves through a system
(function calls, API boundaries, data transformations).

**Acceptance Criteria**:

- [ ] Given a structural model with function call chains, when
  generating a data flow diagram, then it produces a Mermaid
  sequence diagram or flowchart
- [ ] Given a specific entry point (e.g., "main()"), when
  tracing data flow, then only reachable paths are included
- [ ] Given circular dependencies, when generating, then
  cycles are detected and labeled rather than causing infinite
  recursion

**Priority**: High
**Dependencies**: FR-002
**Estimated Effort**: M

### FR-005: Dependency Graph Skill

**Description**: A skill that generates Mermaid flowcharts
showing import/dependency relationships between modules,
packages, or plugins.

**Acceptance Criteria**:

- [ ] Given a Python project, when generating a dependency
  graph, then it shows import relationships as directed edges
- [ ] Given a night-market plugin, when generating, then
  cross-plugin dependencies are highlighted
- [ ] Given a depth limit parameter, when generating, then
  only N levels of dependencies are shown

**Priority**: Medium
**Dependencies**: FR-002
**Estimated Effort**: S

### FR-006: Visualize Command

**Description**: A user-facing slash command `/visualize`
that serves as the entry point for all diagram generation.
Accepts a diagram type and optional scope.

**Acceptance Criteria**:

- [ ] Given `/visualize architecture`, when invoked, then
  it generates and renders an architecture diagram of the
  current project
- [ ] Given `/visualize data-flow plugins/sanctum`, when
  invoked, then it scopes analysis to that directory
- [ ] Given `/visualize` with no arguments, when invoked,
  then it shows available diagram types and usage help
- [ ] Given an invalid diagram type, when invoked, then it
  shows an error with valid options

**Priority**: High
**Dependencies**: FR-003, FR-004, FR-005
**Estimated Effort**: S

### FR-007: Mermaid Rendering Integration

**Description**: All diagram skills call the Mermaid Chart
MCP server to render generated Mermaid syntax into visual
diagrams.

**Acceptance Criteria**:

- [ ] Given valid Mermaid syntax, when rendering, then
  `mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`
  is called with correct `mermaidCode`, `diagramType`,
  `prompt`, and `clientName` parameters
- [ ] Given invalid Mermaid syntax from generation, when
  MCP returns an error, then the skill fixes the syntax and
  retries (max 2 retries)
- [ ] Given a rendered diagram, when displayed, then the
  user sees the image inline in their terminal/IDE

**Priority**: High
**Dependencies**: FR-003, FR-004, FR-005
**Estimated Effort**: S

## Non-Functional Requirements

### NFR-001: Performance - Agent Exploration Time

**Requirement**: The explorer agent should complete analysis
of a 50-plugin codebase (like night-market) within a single
agent dispatch, without exceeding context limits.

**Measurement**:

- Metric: Files read per diagram type
- Target: Under 30 file reads for a scoped analysis
- Tool: Agent dispatch logs

**Priority**: High

### NFR-002: Quality - Mermaid Syntax Validity

**Requirement**: Generated Mermaid syntax should pass MCP
validation on first attempt at least 80% of the time.

**Measurement**:

- Metric: First-attempt render success rate
- Target: 80%+
- Tool: MCP error response tracking

**Priority**: Medium

### NFR-003: Maintainability - Plugin Standards

**Requirement**: Plugin must follow night-market conventions
including BDD tests, skill frontmatter, and plugin.json
schema compliance.

**Measurement**:

- Metric: `validate_plugin.py` pass/fail
- Target: Pass with 0 errors
- Tool: `python3 plugins/abstract/scripts/validate_plugin.py`

**Priority**: High

## Technical Constraints

- **Rendering**: Mermaid Chart MCP server only (no local
  mermaid-cli or custom renderers)
- **Language**: Python for any analyzer scripts; Markdown for
  skills and commands
- **Diagram types**: flowchart, sequenceDiagram,
  architecture-beta, classDiagram (Mermaid built-in types)
- **Model format**: JSON structural model as intermediate
  representation between agent analysis and skill rendering

## Out of Scope (v1.0)

- Interactive diagram editing or annotation
- SVG/PNG file export (MCP returns images inline)
- Real-time diagram updates on code changes
- Git history visualization (timeline/gitgraph)
- Custom Mermaid themes or styling

## Dependencies

- Mermaid Chart MCP server (already available)
- Claude Code plugin SDK (hooks, skills, agents, commands)
- Python 3.9+ for analyzer scripts
- Night-market plugin infrastructure (validate_plugin.py)

## Acceptance Testing Strategy

1. **Unit tests**: Python analyzers tested with fixture
   codebases (small synthetic projects)
2. **Integration tests**: Skill invocation produces valid
   Mermaid syntax (validated by MCP or regex)
3. **Exemplar test**: Generate all 3 diagram types for the
   night-market repo itself and verify they render

## Success Criteria

- [x] All 5 diagram types generate valid Mermaid syntax
- [ ] MCP rendering succeeds for each diagram type
- [ ] Plugin passes `validate_plugin.py` with 0 errors
- [ ] Agent explores night-market and produces a model
- [ ] `/visualize architecture` works end-to-end on this repo

## Glossary

- **Structural model**: JSON representation of a codebase's
  modules, imports, and relationships
- **Mermaid**: Text-based diagramming language (mermaid.js)
- **MCP**: Model Context Protocol, used to call external
  tools from Claude Code

## References

- [Snip (reference implementation)](https://github.com/rixinhahaha/snip)
- [Mermaid.js documentation](https://mermaid.js.org/)
- [Mermaid Chart MCP](https://github.com/mermaidchart/mcp)
- `docs/cartograph/project-brief.md` (project brief)
