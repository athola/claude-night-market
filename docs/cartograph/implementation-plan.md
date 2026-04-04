# Cartograph Plugin - Implementation Plan v0.1.0

**Author**: Alex Thola
**Date**: 2026-04-03
**Target Completion**: Single session

## Architecture

### System Overview

```
User: /visualize architecture plugins/sanctum
  │
  ▼
Command (visualize.md)
  │  routes by diagram type
  ▼
Skill (architecture-diagram / data-flow / dependency-graph)
  │  dispatches explorer if needed
  ├─► Agent (codebase-explorer)
  │     reads code, builds structural model (JSON)
  │     returns model to skill
  │
  │  skill generates Mermaid syntax from model
  ▼
MCP (Mermaid Chart: validate_and_render_mermaid_diagram)
  │
  ▼
Rendered diagram displayed to user
```

### Components

**1. Visualize Command** (`commands/visualize.md`)
Entry point. Parses diagram type and scope, invokes
the matching skill.

**2. Diagram Skills** (`skills/`)
Each skill knows one diagram type. Accepts an optional
structural model or dispatches the explorer agent.
Generates Mermaid syntax and calls the MCP to render.

**3. Codebase Explorer Agent** (`agents/codebase-explorer.md`)
Explores a codebase scope using Glob/Grep/Read. Produces
a JSON structural model capturing modules, relationships,
and metadata. Reusable across all diagram skills.

**4. Structural Model** (runtime JSON, not persisted)
Intermediate representation between exploration and
rendering. Schema defined in skill documentation.

### Data Flow

1. Command receives user input (diagram type + scope)
2. Command invokes the matching skill
3. Skill dispatches explorer agent with scope
4. Agent returns structural model JSON
5. Skill transforms model into Mermaid syntax
6. Skill calls MCP to render
7. User sees diagram

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `plugins/cartograph/.claude-plugin/plugin.json` | Create | Plugin manifest |
| `plugins/cartograph/hooks/hooks.json` | Create | Empty hooks registry |
| `plugins/cartograph/commands/visualize.md` | Create | `/visualize` command |
| `plugins/cartograph/skills/architecture-diagram/SKILL.md` | Create | Architecture diagram generation |
| `plugins/cartograph/skills/data-flow/SKILL.md` | Create | Data flow diagram generation |
| `plugins/cartograph/skills/dependency-graph/SKILL.md` | Create | Dependency graph generation |
| `plugins/cartograph/agents/codebase-explorer.md` | Create | Codebase analysis agent |
| `plugins/cartograph/README.md` | Create | Plugin documentation |
| `plugins/cartograph/tests/unit/test_plugin_health.py` | Create | Plugin validation tests |

## Task Breakdown

### Phase 1: Plugin Scaffold (TASK-001 to TASK-003)

#### TASK-001: Create Plugin Structure

**Description**: Scaffold the cartograph plugin with
plugin.json, hooks.json, README, and directory structure.

**Type**: Infrastructure
**Priority**: P0
**Estimate**: 2 points
**Dependencies**: None
**Linked Requirements**: FR-001

**Acceptance Criteria**:

- [ ] `plugin.json` passes `validate_plugin.py`
- [ ] Directory structure follows night-market conventions
- [ ] README describes plugin purpose and usage

#### TASK-002: Create Visualize Command

**Description**: Create the `/visualize` slash command that
routes to diagram skills by type argument.

**Type**: Implementation
**Priority**: P0
**Estimate**: 2 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-006

**Acceptance Criteria**:

- [ ] `/visualize` with no args shows usage help
- [ ] `/visualize architecture` invokes architecture skill
- [ ] `/visualize data-flow` invokes data-flow skill
- [ ] `/visualize dependency` invokes dependency-graph skill
- [ ] Invalid type shows error with valid options

#### TASK-003: Create Codebase Explorer Agent

**Description**: Create the agent definition that explores
codebases and builds structural models.

**Type**: Implementation
**Priority**: P0
**Estimate**: 3 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-002

**Acceptance Criteria**:

- [ ] Agent frontmatter has valid fields
- [ ] Agent instructions cover Python module discovery
- [ ] Agent outputs JSON structural model
- [ ] Agent respects scope parameter

### Phase 2: Diagram Skills (TASK-004 to TASK-006)

#### TASK-004: Architecture Diagram Skill

**Description**: Skill that generates Mermaid flowchart or
architecture-beta diagrams showing component relationships.

**Type**: Implementation
**Priority**: P1
**Estimate**: 3 points
**Dependencies**: TASK-003
**Linked Requirements**: FR-003, FR-007

**Acceptance Criteria**:

- [ ] Generates valid Mermaid flowchart syntax
- [ ] Calls MCP `validate_and_render_mermaid_diagram`
- [ ] Works with or without pre-built structural model

#### TASK-005: Data Flow Diagram Skill

**Description**: Skill that generates Mermaid sequence
diagrams showing data movement through a system.

**Type**: Implementation
**Priority**: P1
**Estimate**: 3 points
**Dependencies**: TASK-003
**Linked Requirements**: FR-004, FR-007

**Acceptance Criteria**:

- [ ] Generates valid Mermaid sequence diagram syntax
- [ ] Traces data through function calls and boundaries
- [ ] Handles circular references gracefully

#### TASK-006: Dependency Graph Skill

**Description**: Skill that generates Mermaid flowcharts
showing import/dependency relationships between modules.

**Type**: Implementation
**Priority**: P1
**Estimate**: 2 points
**Dependencies**: TASK-003
**Linked Requirements**: FR-005, FR-007

**Acceptance Criteria**:

- [ ] Generates valid Mermaid flowchart with directed edges
- [ ] Supports depth limiting
- [ ] Highlights cross-plugin dependencies

### Phase 3: Validation (TASK-007 to TASK-008)

#### TASK-007: Plugin Health Tests

**Description**: Create test file that validates plugin
structure and registration.

**Type**: Testing
**Priority**: P2
**Estimate**: 2 points
**Dependencies**: TASK-001 through TASK-006
**Linked Requirements**: NFR-003

**Acceptance Criteria**:

- [ ] Tests pass `validate_plugin.py`
- [ ] Tests verify all skills registered in plugin.json
- [ ] Tests verify command registered

#### TASK-008: Exemplar Test - Night Market Visualization

**Description**: Generate all 3 diagram types for the
night-market repo itself to validate end-to-end.

**Type**: Testing
**Priority**: P2
**Estimate**: 3 points
**Dependencies**: TASK-004, TASK-005, TASK-006

**Acceptance Criteria**:

- [ ] Architecture diagram renders for night-market
- [ ] Data flow diagram renders for a specific plugin
- [ ] Dependency graph renders for plugin relationships

## Dependency Graph

```
TASK-001 (Plugin scaffold)
    ├─► TASK-002 (Visualize command)
    │       └─► TASK-007 (Health tests)
    └─► TASK-003 (Explorer agent)
            ├─► TASK-004 (Architecture skill)
            ├─► TASK-005 (Data flow skill)
            └─► TASK-006 (Dependency skill)
                    └─► TASK-008 (Exemplar test)
```

**Critical path**: TASK-001 → TASK-003 → TASK-004 → TASK-008
**Parallelizable**: TASK-002 || TASK-003 (after TASK-001)
**Parallelizable**: TASK-004 || TASK-005 || TASK-006 (after TASK-003)

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Mermaid syntax errors from generation | Medium | Medium | MCP validates; retry with fixes |
| Agent context overflow on large repos | High | Low | Scope parameter limits exploration |
| MCP server unavailable | High | Low | Skill still outputs Mermaid text |

## Success Metrics

- [ ] All 3 diagram types generate valid Mermaid
- [ ] MCP rendering succeeds for each type
- [ ] Plugin passes validation
- [ ] Night-market exemplar diagrams render

## Next Steps

1. Execute Phase 1 (scaffold + command + agent)
2. Execute Phase 2 (diagram skills, parallelizable)
3. Execute Phase 3 (validation and exemplar)
