# Memory Palace Plugin

Spatial knowledge organization using memory palace techniques for Claude Code.

## Overview

The Memory Palace plugin provides tools for building, navigating, and maintaining virtual memory structures. These techniques leverage spatial memory to enhance recall and organize complex information.

## Features

- **Memory Palace Architect**: Design spatial knowledge structures using mnemonic techniques
- **Knowledge Locator**: Multi-modal search across palaces (semantic, spatial, sensory)
- **Session Palace Builder**: Temporary palaces for extended conversations
- **Digital Garden Cultivator**: Evolving knowledge bases with bidirectional linking

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

## Commands

| Command | Description |
|---------|-------------|
| `/palace` | Create and manage memory palaces |
| `/garden` | Manage digital gardens and metrics |
| `/navigate` | Search and navigate across palaces |

## Agents

| Agent | Description |
|-------|-------------|
| `palace-architect` | Designs palace architectures |
| `knowledge-navigator` | Searches and retrieves information |
| `garden-curator` | Maintains digital gardens |

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
│   └── garden_metrics.py
└── scripts/
    └── memory_palace_cli.py
```

## Requirements

- Python 3.12+
- Claude Code

## License

MIT
