---
name: palace-diagram
description: Generates Mermaid and ASCII diagrams of palace structure, knowledge topology, and synapse connectivity. Use when inspecting or presenting a palace visually.
alwaysApply: false
category: visualization
tags:
- memory
- visualization
- mermaid
- diagram
- graph
dependencies:
- memory-palace-architect
usage_patterns:
- palace-visualization
- knowledge-topology
complexity: intermediate
model_hint: standard
estimated_tokens: 400
---

# Palace Diagram

Generate Mermaid and ASCII diagrams from the knowledge
graph, showing palace structure, entity relationships,
synapse connectivity, and tier assignments.

> **Status: wired**. Invoke via `/palace diagram <palace-id>
> [--type map|ascii|entity|heatmap]`, which calls
> `Skill(memory-palace:palace-diagram)`. The renderer lives in
> `memory_palace.palace_renderer.PalaceRenderer`; see the Usage
> section below for direct programmatic access.

## When To Use

- Inspecting palace structure after creation or migration
- Understanding knowledge topology and connections
- Identifying strong and weak synapses (heatmap)
- Reviewing entity relationships and triples
- Getting an ASCII overview for inline display

## When NOT To Use

- Creating palaces: use memory-palace-architect
- Searching knowledge: use knowledge-locator
- Code architecture diagrams: use cartograph

## Diagram Types

| Type | Format | Description |
|------|--------|-------------|
| Palace map | Mermaid flowchart | Rooms as subgraphs, entities as nodes, synapses as edges |
| Entity graph | Mermaid flowchart | Single entity's connections and triples |
| Synapse heatmap | Mermaid flowchart | Edge styling by strength (thick=strong, dotted=weak) |
| ASCII overview | Text | Box-drawing palace layout with entity counts |

## Workflow

1. **Identify palace** by ID or name
2. **Choose diagram type** based on what you want to see
3. **Generate diagram** using `PalaceRenderer`
4. **Render** via Mermaid Chart MCP (for Mermaid) or
   display inline (for ASCII)

## Usage

### Palace Map
```python
from memory_palace.knowledge_graph import KnowledgeGraph
from memory_palace.palace_renderer import PalaceRenderer

graph = KnowledgeGraph("path/to/knowledge_graph.db")
renderer = PalaceRenderer(graph)
mermaid = renderer.palace_map("palace_id")
```

Then call `mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`
with the generated Mermaid string.

### ASCII Overview
```python
ascii_art = renderer.ascii_overview("palace_id")
print(ascii_art)
```

### Entity Graph
```python
mermaid = renderer.entity_graph("entity_id")
```

### Synapse Heatmap
```python
mermaid = renderer.synapse_heatmap("palace_id")
```

## Edge Styling

| Strength | Style | Meaning |
|----------|-------|---------|
| >= 0.7 | `==>` (thick) | Strong connection |
| >= 0.4 | `-->` (normal) | Medium connection |
| < 0.4 | `-.->` (dotted) | Weak connection |

## Integration

Works with:

- `memory-palace-architect`: visualize after palace creation
- `knowledge-locator`: display search results as graph
- `graph-analyzer`: tier-informed node sizing

## Exit Criteria

- [ ] At least one of the four diagram types (palace map, entity graph,
      synapse heatmap, ASCII overview) is generated without a Python
      exception from `PalaceRenderer`
- [ ] Mermaid diagrams are passed to
      `mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram`
      and render successfully
- [ ] ASCII overview displays rooms with box-drawing characters and
      entity counts per room
- [ ] Synapse edge styling matches strength thresholds: `==>` for
      strength ≥ 0.7, `-->` for ≥ 0.4, `-.->` for < 0.4
- [ ] If the requested palace ID does not exist in the knowledge graph,
      an error is reported with the palace ID that was searched
