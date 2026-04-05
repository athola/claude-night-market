# cartograph

Codebase visualization through architecture, data flow,
dependency, workflow, and class diagrams rendered via
Mermaid Chart MCP.

## Overview

Cartograph analyzes code structure and generates Mermaid
diagrams. A codebase explorer agent extracts modules,
imports, and relationships, then diagram-specific skills
convert the structural model into rendered visuals.

## Installation

```bash
/plugin install cartograph@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `architecture-diagram` | Component relationship diagrams | System structure, plugin architecture |
| `data-flow` | Data movement between components | Request paths, API flows |
| `dependency-graph` | Import and dependency relationships | Coupling analysis, circular deps |
| `workflow-diagram` | Process steps and state transitions | CI/CD pipelines, dev workflows |
| `class-diagram` | Classes, interfaces, inheritance | OOP structure, type hierarchies |

## Commands

| Command | Description |
|---------|-------------|
| `/visualize` | Generate a codebase diagram |

## Agents

| Agent | Description |
|-------|-------------|
| `codebase-explorer` | Analyzes modules, imports, and relationships |

## Usage Examples

### Architecture Diagram

```bash
/visualize architecture plugins/sanctum
```

Generates a flowchart showing component relationships
within the specified scope.

### Dependency Graph

```bash
/visualize dependency plugins/
```

Shows import relationships between modules. Useful for
spotting circular dependencies or tight coupling.

### Data Flow

```bash
/visualize data-flow plugins/conserve
```

Produces a sequence diagram tracing data movement through
the system.

### Workflow Diagram

```bash
/visualize workflow
```

Maps process steps, decision points, and state transitions
for development workflows or CI/CD pipelines.

### Class Diagram

```bash
/visualize class plugins/gauntlet
```

Shows classes, interfaces, inheritance, and composition
within a module.

## How It Works

1. The `/visualize` command routes to a diagram skill
2. The skill dispatches the `codebase-explorer` agent
3. The agent analyzes code structure and produces a JSON
   structural model
4. The skill generates Mermaid syntax from the model
5. The Mermaid Chart MCP server renders the diagram

## Requirements

- Mermaid Chart MCP server (included with Claude Code)

## Related Plugins

- **scry**: Terminal and browser recordings for demos
- **pensive**: Architecture review complements visual
  diagrams with written assessments
- **archetypes**: Architecture paradigm selection pairs
  with architectural visualization
