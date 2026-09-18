---
name: knowledge-locator
description: Searches and navigates stored knowledge in memory palaces. Use when looking for previously stored information or cross-referencing concepts across palaces.
alwaysApply: false
category: navigation
tags:
- retrieval
- search
- indexing
- recall
- spatial-memory
- pr-review
dependencies:
- memory-palace-architect
- review-chamber
scripts:
- memory_palace_cli.py
usage_patterns:
- search
- cross-reference
- discovery
- review-search
complexity: intermediate
model_hint: standard
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
python scripts/memory_palace_cli.py search "authentication" --type semantic
```
**Verification:** Run `python --version` to verify Python environment.

### List All Palaces
```bash
python scripts/memory_palace_cli.py list
```
**Verification:** Run `python --version` to verify Python environment.

## When To Use

- Finding specific concepts within one or more memory palaces
- Cross-referencing information across different palaces
- Discovering connections between stored information
- Finding information using partial or contextual queries
- Analyzing access patterns for palace optimization

## When NOT To Use

- Creating new
  palace structures - use memory-palace-architect
- Processing new
  external resources - use knowledge-intake
- Creating new
  palace structures - use memory-palace-architect
- Processing new
  external resources - use knowledge-intake

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
- **Cross-Reference Mapping**: See `modules/index-structure.md`

## PR Review Search

Search the review chamber within project palaces for past decisions and patterns.

### Quick Commands

The CLI has no room-scoped search: `search` runs across every
palace, and `--palace`, `--room`, `list-reviews` and `search-reviews`
do not exist (this file cited them until 2026-09-18). Filter by the
palace name in the output, or use `Skill(memory-palace:review-chamber)`,
which owns the chamber's own retrieval.

```bash
python scripts/memory_palace_cli.py search "authentication"
```

### Review Chamber Rooms

| Room | Content | Example Query |
|------|---------|---------------|
| `decisions/` | Architectural choices | "JWT vs sessions" |
| `patterns/` | Recurring solutions | "error handling pattern" |
| `standards/` | Quality conventions | "API error format" |
| `lessons/` | Post-mortems | "outage learnings" |

### Context-Aware Surfacing

When starting work in a code area, surface relevant review knowledge:

There is no `context-search` command. Search for the area's own
words instead:

```bash
python scripts/memory_palace_cli.py search "auth"
```

## Integration

Works with:
- `memory-palace-architect` - Indexes palaces created by architect
- `session-palace-builder` - Searches session-specific palaces
- `digital-garden-cultivator` - Finds garden content and links
- `review-chamber` - Searches PR review knowledge in project palaces

## Exit Criteria

- [ ] `scripts/memory_palace_cli.py search "<query>"` returns results,
      and says "No palaces indexed" rather than "No matches" when there
      is nothing to search
      within 500ms for a cold query against an indexed palace
- [ ] At least one of the five search modalities (spatial, semantic,
      sensory, associative, temporal) returns ranked results for a
      valid query against an existing palace
- [ ] Top-3 accuracy target of ≥ 90% is met for semantic queries when
      the queried concept is present in the indexed palace
- [ ] Incomplete or partial queries return results rather than errors,
      satisfying the ≥ 80% robustness target
- [ ] If no palace exists to search, user is directed to
      `memory-palace-architect` rather than returning an empty result
      silently
