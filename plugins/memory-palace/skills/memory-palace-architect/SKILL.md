---
name: memory-palace-architect
description: Designs memory palace structures with spatial layouts and domain organization. Use when creating a new palace or planning knowledge architecture by hand.
alwaysApply: false
category: architecture
tags:
- memory
- organization
- spatial
- knowledge
- architecture
- mnemonic
dependencies:
- leyline:progressive-loading
scripts:
- memory_palace_cli.py
usage_patterns:
- palace-design
- domain-analysis
- layout-creation
complexity: intermediate
estimated_tokens: 600
---
> **Status: wired**. The `palace-architect` agent loads this skill
> for its design method (#618). `/palace create` still creates the
> palace record directly. This skill decides what goes in it.

# Memory Palace Architect

Design and construct virtual memory palaces for spatial knowledge organization. This skill guides you through creating memorable spatial structures that enhance recall and organize complex information.

## What It Is

A memory palace is a mnemonic technique that uses spatial visualization to organize and recall information. This skill provides a systematic approach for:
- Analyzing knowledge domains for optimal spatial mapping
- Designing architectural layouts that reflect conceptual relationships
- Creating multi-sensory associations for enhanced recall
- Building navigable structures for knowledge retrieval

## Quick Start

### Create a New Palace
```bash
python scripts/memory_palace_cli.py create "My Palace" "programming" --metaphor workshop
```

### List Existing Palaces
```bash
python scripts/memory_palace_cli.py list
```

### View Palace Status
```bash
python scripts/memory_palace_cli.py status
```

## When To Use

- Creating knowledge structures for complex topics
- Organizing large amounts of related information
- Building persistent, project-specific memory systems
- Designing learning pathways for skill acquisition
- Structuring documentation or reference material

## When NOT To Use

- Quick knowledge search
  - use knowledge-locator instead
- Session-specific context - use
  session-palace-builder
- Quick knowledge search
  - use knowledge-locator instead
- Session-specific context - use
  session-palace-builder

## Metaphor Choices

`--metaphor` is a free-form label stored on the palace as given, and it
defaults to `building`. Nothing validates it or loads a template from
it. These five are suggested starting points for the design:

| Metaphor | Best For | Key Features |
|----------|----------|--------------|
| **Fortress** | Security, defense, production-grade systems | Strong boundaries, layered access |
| **Library** | Knowledge, research, documentation | Organized shelves, categorized sections |
| **Workshop** | Practical skills, tools, techniques | Workbenches, tool areas, project spaces |
| **Garden** | Organic growth, evolving knowledge | Plots, seasons, interconnected paths |
| **Observatory** | Exploration, discovery, patterns | Viewing platforms, star maps, instruments |

## Core Workflow

1. **Analyze Domain** - Identify concepts, relationships, and hierarchy
2. **Design Layout** - Choose metaphor and spatial organization
3. **Map Associations** - Create memorable imagery and connections
4. **Encode Details** - Add sensory attributes and ambient atmosphere
5. **Validate Palace** - Test recall efficiency and navigation

## Detailed Resources

- **Domain Analysis Guide**: See `modules/domain-analysis.md`
- **Layout Patterns**: See `modules/layout-patterns.md`
- **Sensory Encoding**: See `modules/sensory-encoding.md`
- **Validation Metrics**: See `modules/validation.md`
- **Franklin Protocol**: See `modules/franklin-protocol.md` - Apply the original learning algorithm to palace design

## Integration

Works with:
- `knowledge-locator` - For searching across palaces
- `session-palace-builder` - For temporary session palaces
- `digital-garden-cultivator` - For evolving knowledge bases

## Expected Outputs

- Complete palace schema with spatial coordinates
- Sensory encoding profile for each location
- Navigation guide and connection map
- Recall testing results and optimization recommendations
## Troubleshooting

### Common Issues

If palace creation fails, ensure your Python environment meets the requirements listed in `pyproject.toml`. The `metaphor` value cannot cause a failure, because any string is accepted.

## Exit Criteria

- [ ] `scripts/memory_palace_cli.py create "<name>" "<domain>" --metaphor
      <metaphor>` completes without error and adds the palace to the
      index
- [ ] `scripts/memory_palace_cli.py list` shows the newly created palace
      by the name supplied during creation
- [ ] The created palace JSON has a `layout` (districts, buildings,
      rooms, connections) and a `sensory_encoding` block, and both are
      filled in from the design
- [ ] The palace's `metaphor` field records the metaphor the design
      chose
- [ ] Recall testing results or optimization recommendations are
      produced as part of the Expected Outputs section
