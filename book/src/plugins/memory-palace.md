# memory-palace

Knowledge organization using spatial memory techniques.

## Overview

Memory Palace applies the ancient method of loci to digital knowledge management. It helps you build "palaces" - structured knowledge repositories that use spatial metaphors for organization and retrieval.

## Installation

```bash
/plugin install memory-palace@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `memory-palace-architect` | Building virtual palaces | Organizing complex concepts |
| `knowledge-locator` | Spatial search | Finding stored information |
| `knowledge-intake` | Intake and curation | Processing new information |
| `digital-garden-cultivator` | Digital garden maintenance | Long-term knowledge base care |
| `session-palace-builder` | Session-specific palaces | Temporary working knowledge |

## Commands

| Command | Description |
|---------|-------------|
| `/palace` | Manage memory palaces |
| `/garden` | Manage digital gardens |
| `/navigate` | Search and traverse palaces |

## Agents

| Agent | Description |
|-------|-------------|
| `palace-architect` | Designs memory palace architectures |
| `knowledge-navigator` | Searches and retrieves from palaces |
| `knowledge-librarian` | Evaluates and routes knowledge |
| `garden-curator` | Maintains digital gardens |

## Hooks

| Hook | Type | Description |
|------|------|-------------|
| `research_interceptor.py` | PreToolUse | Checks local knowledge before web searches |
| `url_detector.py` | UserPromptSubmit | Detects URLs for intake |
| `local_doc_processor.py` | PostToolUse | Processes local docs after reads |
| `web_content_processor.py` | PostToolUse | Processes web content for storage |

## Usage Examples

### Create a Palace

```bash
/palace create "Python Async Patterns"

# Creates:
# - Palace structure
# - Entry rooms
# - Navigation paths
```

### Add Knowledge

```bash
Skill(memory-palace:knowledge-intake)

# Processes:
# - New information
# - Categorization
# - Spatial placement
# - Cross-references
```

### Navigate Knowledge

```bash
/navigate "async context managers"

# Returns:
# - Matching rooms
# - Related concepts
# - Cross-references
# - Source citations
```

### Maintain Garden

```bash
/garden cultivate

# Performs:
# - Pruning outdated content
# - Strengthening connections
# - Identifying gaps
# - Suggesting additions
```

## Cache Modes

The research interceptor supports four modes:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `cache_only` | Deny web when no cache match | Offline work, audits |
| `cache_first` | Check cache, fall back to web | Default research |
| `augment` | Blend cache with live results | When freshness matters |
| `web_only` | Bypass Memory Palace | Incident response |

Set mode in `hooks/memory-palace-config.yaml`:

```yaml
research_mode: cache_first
```

## Palace Architecture

Palaces use spatial metaphors:

```
Palace: "Python Async"
├── Entry Hall
│   └── Overview concepts
├── Library Wing
│   ├── asyncio basics
│   ├── coroutines
│   └── event loops
├── Practice Room
│   ├── code examples
│   └── exercises
└── Reference Archive
    ├── official docs
    └── external sources
```

## Knowledge Intake Flow

```
New Information
      |
      v
[Novelty Check] --> Duplicate? --> Skip
      |
      No
      v
[Domain Alignment] --> Matches interests? --> Flag for intake
      |
      Yes
      v
[Palace Placement] --> Store in appropriate room
      |
      v
[Cross-Reference] --> Link to related concepts
```

## Embedding Support

Optional semantic search via embeddings:

```bash
# Build embeddings
cd plugins/memory-palace
uv run python scripts/build_embeddings.py --provider local

# Toggle at runtime
export MEMORY_PALACE_EMBEDDINGS_PROVIDER=local
```

## Telemetry

Track research decisions:

```csv
# data/telemetry/memory-palace.csv
timestamp,query,decision,novelty_score,domains,duplicates
2025-01-15,async patterns,cache_hit,0.2,python,entry-123
```

## Curation Workflow

Regular maintenance keeps palaces useful:

1. **Review intake queue**: `data/intake_queue.jsonl`
2. **Approve/reject items**: Based on value and fit
3. **Update vitality scores**: Mark evergreen vs. probationary
4. **Prune stale content**: Archive outdated information
5. **Document in curation log**: `docs/curation-log.md`

## Digital Gardens

Unlike palaces (structured), gardens are organic:

```bash
/garden status

# Shows:
# - Growth rate
# - Connection density
# - Orphan nodes
# - Suggested links
```

## Knowledge Promotion to Discussions

Evergreen corpus entries can be promoted to a GitHub Discussion in the "Knowledge" (Q&A) category. The `discussion-promotion` module in `knowledge-intake` checks entry maturity — only entries at the `evergreen` lifecycle stage are eligible. Promotion creates a structured Discussion with title, summary, key findings, and source references. Entries that already have a `discussion_url` field are updated rather than duplicated.

## Related Plugins

- **conservation**: Memory Palace helps reduce redundant web fetches
- **imbue**: Evidence logging integrates with knowledge intake
