---
name: knowledge-locator
description: |
  Spatial indexing and retrieval system for finding information within memory
  palaces using multi-modal search.

  Triggers: knowledge search, find information, locate concept, recall, spatial
  query, cross-reference, discovery, memory retrieval

  Use when: searching for stored knowledge, cross-referencing concepts,
  discovering connections, retrieving from palaces

  DO NOT use when: creating new palace structures - use memory-palace-architect.
  DO NOT use when: processing new external resources - use knowledge-intake.

  Consult this skill when searching or navigating stored knowledge.
category: navigation
tags: [retrieval, search, indexing, recall, spatial-memory]
dependencies: [memory-palace-architect]
scripts: [palace_manager.py]
usage_patterns: [search, cross-reference, discovery]
complexity: intermediate
estimated_tokens: 500
---

# Knowledge Locator

A spatial indexing and retrieval system for finding information within and across memory palaces. Enables multi-modal search using spatial, semantic, sensory, and associative queries.

## What It Is

The Knowledge Locator provides efficient information retrieval across your memory palace network by:
- Building and maintaining spatial indices for fast lookup
- Supporting multiple search modalities (spatial, semantic, sensory)
- Mapping cross-references between palaces
- Tracking access patterns for optimization

## Quick Start

### Search Palaces
```bash
python scripts/palace_manager.py search "authentication" --type semantic
```

### List All Palaces
```bash
python scripts/palace_manager.py list
```

## When to Use

- Finding specific concepts within one or more memory palaces
- Cross-referencing information across different palaces
- Discovering connections between stored information
- Finding information using partial or contextual queries
- Analyzing access patterns for palace optimization

## Search Modalities

| Mode | Description | Best For |
|------|-------------|----------|
| **Spatial** | Query by location path | "Find concepts in the Workshop" |
| **Semantic** | Search by meaning/keywords | "Find authentication-related items" |
| **Sensory** | Locate by sensory attributes | "Blue-colored concepts" |
| **Associative** | Follow connection chains | "Related to OAuth" |
| **Temporal** | Find by creation/access date | "Recently accessed" |

## Core Workflow

1. **Build Index** - Create spatial index of all palaces
2. **Optimize Search** - Configure search strategies and heuristics
3. **Map Cross-References** - Identify inter-palace connections
4. **Test Retrieval** - Validate search accuracy and speed
5. **Analyze Patterns** - Track and optimize based on usage

## Target Metrics

- **Retrieval latency**: ≤ 150ms cached, ≤ 500ms cold
- **Top-3 accuracy**: ≥ 90% for semantic queries
- **Robustness**: ≥ 80% success with incomplete queries

## Detailed Resources

- **Index Structure**: See `modules/index-structure.md`
- **Search Strategies**: See `modules/search-strategies.md`
- **Cross-Reference Mapping**: See `modules/cross-references.md`

## Integration

Works with:
- `memory-palace-architect` - Indexes palaces created by architect
- `session-palace-builder` - Searches session-specific palaces
- `digital-garden-cultivator` - Finds garden content and links
