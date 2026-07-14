---
name: architecture-diagram
description: Generates a Mermaid architecture diagram showing high-level component relationships. Use when visualizing how plugins or modules fit together.
---

# Architecture Diagram

Generate a Mermaid flowchart showing high-level component
relationships in a codebase.

## When To Use

- Visualizing how plugins/modules relate to each other
- Onboarding to understand system structure
- Documenting architecture for PR reviews
- Answering "how does this system fit together?"

## When NOT To Use

- Import-level coupling (use `cartograph:dependency-graph`)
- Runtime call paths (use `cartograph:call-chain`)

## Workflow

### Step 1: Explore the Codebase

Dispatch the codebase explorer agent to analyze the scope:

```
Agent(cartograph:codebase-explorer)
Prompt: Explore [scope] and return a structural model.
Focus on packages, modules, and their relationships
for an architecture diagram.
```

If no scope is provided, use the project root.

### Step 2: Generate Mermaid Syntax

Transform the structural model into a Mermaid flowchart.

**Rules for architecture diagrams**:

- Use `flowchart TD` (top-down) for hierarchical systems
- Use `flowchart LR` (left-right) for pipeline/flow systems
- Group related modules into subgraphs by package
- Use descriptive edge labels for relationships
- Limit to 15-20 nodes maximum (aggregate small modules)
- Use shapes to distinguish component types:
  - `[Rectangle]` for modules/packages
  - `([Stadium])` for entry points/commands
  - `[(Database)]` for data stores
  - `{Diamond}` for decision points

**Example output**:

```mermaid
flowchart TD
    subgraph sanctum[Sanctum Plugin]
        commit[Commit Messages]
        pr[PR Preparation]
        workspace[Workspace Review]
    end

    subgraph leyline[Leyline Plugin]
        git[Git Platform]
        patterns[Error Patterns]
    end

    commit --> git
    pr --> workspace
    pr --> git
    workspace --> patterns
```

### Step 3: Render via MCP

Call the Mermaid Chart MCP to render:

```
mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram
  prompt: "Architecture diagram of [scope]"
  mermaidCode: [generated syntax]
  diagramType: "flowchart"
  clientName: "claude-code"
```

If rendering fails, fix the Mermaid syntax based on the
error message and retry (max 2 retries).

### Step 4: Present Results

Show the rendered diagram to the user with a brief summary
of what it depicts (2-3 sentences).

## Exit Criteria

- [ ] Mermaid `flowchart` syntax generated containing at least
      one `subgraph` block grouping related modules
- [ ] `mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`
      called and returns without error (or retry attempted on first
      failure and result reported)
- [ ] Diagram node count is between 3 and 20 (per skill rules)
- [ ] A 2-3 sentence description of what the diagram depicts is shown
      alongside the rendered output
- [ ] If the MCP render fails after 2 retries, the Mermaid syntax is
      still presented as a code block with the error surfaced
