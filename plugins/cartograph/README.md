# cartograph

Codebase visualization plugin for Claude Code.
Generates architecture, data flow, dependency, call chain,
and community detection diagrams rendered via the Mermaid
Chart MCP server.

## Usage

```
/visualize architecture [scope]
/visualize data-flow [scope]
/visualize dependency [scope]
/visualize workflow [scope]
/visualize class [scope]
```

**scope** is optional. Defaults to current project root.
Pass a directory path to limit analysis
(e.g., `plugins/sanctum`).

## How It Works

1. The `/visualize` command routes to a diagram skill
2. The skill dispatches the codebase explorer agent
3. The agent analyzes code structure (modules, imports,
   relationships)
4. The skill generates Mermaid syntax from the analysis
5. The Mermaid Chart MCP renders the diagram

## Diagram Types

| Type | Mermaid Type | Shows |
|------|-------------|-------|
| `architecture` | flowchart | Component relationships |
| `data-flow` | sequenceDiagram | Data movement between components |
| `dependency` | flowchart | Import/dependency graph |
| `workflow` | flowchart | Process steps, pipelines, state machines |
| `class` | classDiagram | Classes, inheritance, composition |
| `call-chain` | flowchart | Execution paths from entry points |
| `communities` | flowchart | Architectural clusters via community detection |

## Requirements

- Mermaid Chart MCP server (included with Claude Code)
