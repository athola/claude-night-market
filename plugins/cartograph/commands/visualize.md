# Visualize Codebase

Generate visual diagrams of codebase structure using
Mermaid Chart MCP rendering.

## Arguments

- `type` - Diagram type: `architecture`, `data-flow`,
  `dependency`, `workflow`, or `class` (required)
- `scope` - Directory path to limit analysis (optional,
  defaults to project root)

## Usage

```
/visualize architecture
/visualize data-flow plugins/sanctum
/visualize dependency --depth 2
/visualize workflow .github/workflows
/visualize class plugins/sanctum/scripts
```

## Diagram Types

| Type | Skill | Mermaid Format |
|------|-------|----------------|
| `architecture` | `cartograph:architecture-diagram` | flowchart TD |
| `data-flow` | `cartograph:data-flow` | sequenceDiagram |
| `dependency` | `cartograph:dependency-graph` | flowchart LR |
| `workflow` | `cartograph:workflow-diagram` | flowchart TD/LR |
| `class` | `cartograph:class-diagram` | classDiagram |

## Workflow

1. Parse the diagram type from arguments
2. Invoke the matching skill:
   - `architecture` invokes
     `Skill(cartograph:architecture-diagram)`
   - `data-flow` invokes `Skill(cartograph:data-flow)`
   - `dependency` invokes
     `Skill(cartograph:dependency-graph)`
   - `workflow` invokes
     `Skill(cartograph:workflow-diagram)`
   - `class` invokes `Skill(cartograph:class-diagram)`
3. Pass scope argument to the skill
4. Skill handles exploration, Mermaid generation, and
   MCP rendering

## Error Handling

If no type argument is provided, display this help text.
If an invalid type is provided, show the valid options
table above.
