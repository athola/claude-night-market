# Memory Palace Plugin

Spatial knowledge organization using memory palace techniques for Claude Code.

## Overview

The Memory Palace plugin provides tools for building, navigating, and maintaining virtual memory structures. These techniques leverage spatial memory to enhance recall and organize complex information.

## Features

- **Memory Palace Architect**: Design spatial knowledge structures using mnemonic techniques
- **Knowledge Locator**: Multi-modal search across palaces (semantic, spatial, sensory)
- **Session Palace Builder**: Temporary palaces for extended conversations
- **Digital Garden Cultivator**: Evolving knowledge bases with bidirectional linking
- **PR Review Chamber**: Capture PR review knowledge in project memory palaces

## PR Review Room (New in v1.2.0)

Treat entire projects as palaces with a dedicated review chamber for capturing knowledge from PR reviews.

### Project Palace Structure

```
project-palace/
├── entrance/           # README, getting started
├── library/            # Documentation, ADRs
├── workshop/           # Development patterns, tooling
├── review-chamber/     # PR Reviews
│   ├── decisions/      # Architectural choices
│   ├── patterns/       # Recurring issues/solutions
│   ├── standards/      # Quality bar examples
│   └── lessons/        # Post-mortems, learnings
└── garden/             # Evolving knowledge
```

### Quick Start

```bash
# Capture knowledge from a PR review
/review-room capture 42

# Search past decisions
/review-room search "authentication" --room decisions

# List recent patterns
/review-room list --room patterns --limit 5
```

### Integration with sanctum:pr-review

Knowledge capture triggers automatically after PR reviews:

```bash
/pr-review 42
# → Review posted to GitHub
# → Significant findings captured to review-chamber
```

See `skills/review-chamber/SKILL.md` for full documentation.

## Installation

```bash
# Clone the repository
git clone https://github.com/superpowers-marketplace/memory-palace.git

# Install as Claude Code plugin
claude-code plugins add ./memory-palace
```

## Quick Start

### Create a Palace
```bash
python scripts/palace_manager.py create "K8s Concepts" "kubernetes" --metaphor workshop
```

### List Palaces
```bash
python scripts/palace_manager.py list
```

### Search
```bash
python scripts/palace_manager.py search "authentication" --type semantic
```

### Garden Metrics
```bash
python scripts/garden_metrics.py path/to/garden.json --format brief
```

## Skills

| Skill | Description |
|-------|-------------|
| `memory-palace-architect` | Design and construct virtual memory palaces |
| `knowledge-locator` | Find information using multi-modal search |
| `session-palace-builder` | Create temporary session-specific palaces |
| `digital-garden-cultivator` | Manage evolving knowledge bases |
| `knowledge-intake` | Process and evaluate external knowledge |
| `review-chamber` | Capture PR review knowledge in project palaces |

## Commands

| Command | Description |
|---------|-------------|
| `/palace` | Create and manage memory palaces |
| `/garden` | Manage digital gardens and metrics |
| `/navigate` | Search and navigate across palaces |
| `/review-room` | Manage PR review knowledge in project palaces |

## Agents

| Agent | Description |
|-------|-------------|
| `palace-architect` | Designs palace architectures |
| `knowledge-navigator` | Searches and retrieves information |
| `garden-curator` | Maintains digital gardens |

## Hooks

The plugin registers several hooks to integrate with Claude Code tool events:

| Hook | Event | Description |
|------|-------|-------------|
| `research_interceptor.py` | PreToolUse | Intercepts WebSearch/WebFetch to check local knowledge cache before web requests |
| `local_doc_processor.py` | PostToolUse | Monitors Read operations on configured knowledge paths for indexing suggestions |
| `url_detector.py` | PostToolUse | Detects URLs in tool responses for potential knowledge intake |
| `web_content_processor.py` | PostToolUse | Processes web content for knowledge extraction |

Hooks are configured via `hooks/hooks.json` and `hooks/memory-palace-config.yaml`.

## Architecture

```
memory-palace/
├── .claude-plugin/
│   ├── plugin.json      # Plugin manifest
│   └── metadata.json    # Extended metadata
├── skills/
│   ├── memory-palace-architect/
│   │   ├── SKILL.md
│   │   └── modules/
│   ├── knowledge-locator/
│   ├── session-palace-builder/
│   └── digital-garden-cultivator/
├── commands/
│   ├── palace.md
│   ├── garden.md
│   └── navigate.md
├── agents/
│   ├── palace-architect.md
│   ├── knowledge-navigator.md
│   └── garden-curator.md
├── src/memory_palace/
│   ├── palace_manager.py
│   ├── project_palace.py    # NEW: Project palace with review chamber
│   └── garden_metrics.py
└── scripts/
    └── memory_palace_cli.py
```

## Requirements

- Python 3.12+
- Claude Code

## Session Forking Workflows (Claude Code 2.0.73+)

Session forking enables exploratory knowledge organization - test different categorization strategies without commitment.

### Use Cases

**Test Knowledge Organization Strategies**
```bash
# Main session: New content to organize
claude "/knowledge-intake article.md"

# Fork for hierarchical categorization
claude --fork-session --session-id "hierarchical-tags" --resume
> "Organize using hierarchical tags (category/subcategory/topic)"

# Fork for flat categorization
claude --fork-session --session-id "flat-tags" --resume
> "Organize using flat, single-level tags"

# Fork for concept-map approach
claude --fork-session --session-id "concept-map" --resume
> "Organize using concept map with semantic relationships"

# Compare effectiveness and choose best approach
```

**Parallel Palace Design Exploration**
```bash
# Main session: Need to create memory palace
claude "Design memory palace for learning Rust"

# Fork A: Workshop metaphor
claude --fork-session --session-id "rust-workshop" --resume
> "Design as workshop with tools, benches, and materials"

# Fork B: Library metaphor
claude --fork-session --session-id "rust-library" --resume
> "Design as library with sections, shelves, and reading rooms"

# Fork C: City metaphor
claude --fork-session --session-id "rust-city" --resume
> "Design as city with districts, streets, and landmarks"

# Choose metaphor that best matches your learning style
```

**Alternative Review Chamber Structures**
```bash
# Main session: Setting up project palace
claude "Initialize project palace for this repository"

# Fork to try topic-based chambers
claude --fork-session --session-id "topic-chambers" --resume
> "Organize review chamber by topic (auth, database, API)"

# Fork to try chronological chambers
claude --fork-session --session-id "chronological-chambers" --resume
> "Organize review chamber chronologically by sprint/milestone"

# Fork to try pattern-based chambers
claude --fork-session --session-id "pattern-chambers" --resume
> "Organize review chamber by recurring patterns/anti-patterns"

# Evaluate and select most useful structure
```

### Benefits

- **Risk-free experimentation**: Try organization strategies without committing
- **Comparative evaluation**: See which approach works best for your content
- **Learning optimization**: Find the knowledge structure that matches your mental model
- **Iterative refinement**: Test refinements without losing proven approaches

### Best Practices

- **Test with representative content**: Use actual knowledge to evaluate organization
- **Document decision rationale**: Record why you chose one approach over others
- **Extract palace designs**: Save successful palace structures to templates
- **Iterate gradually**: Start with one fork, then add more if needed

See `plugins/abstract/docs/claude-code-compatibility.md` for comprehensive session forking patterns.

## License

MIT
