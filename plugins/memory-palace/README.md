# Memory Palace Plugin

Spatial knowledge organization using memory palace techniques for Claude Code.

## Overview

Memory Palace organizes complex information using spatial memory techniques for easier retrieval.

## Features

The Memory Palace Architect allows users to design spatial knowledge structures using mnemonic techniques, while the Knowledge Locator facilitates multi-modal search across these palaces. Temporary structures for extended conversations are handled by the Session Palace Builder, and the Digital Garden Cultivator manages evolving knowledge bases with bidirectional linking. Additionally, a dedicated PR Review Chamber captures knowledge from PR reviews, and Skill Execution Memory automatically logs skill invocation history to support continual learning.

## PR Review Room

Projects function as palaces with a dedicated chamber for capturing knowledge from PR reviews.

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

Knowledge capture triggers after PR reviews:

1. Review posted to GitHub.
2. Findings captured to review-chamber.

See `skills/review-chamber/SKILL.md` for details.

## Skill Execution Memory

Memory-palace automatically stores skill execution history via hooks, enabling continual learning and performance analysis.

### Automatic Storage

Every skill invocation is automatically stored with:
- **Timestamp**: When the skill was invoked
- **Duration**: Execution time
- **Outcome**: Success, failure, or partial
- **Continual metrics**: Stability gap, accuracy trends

### Storage Structure

```
~/.claude/skills/logs/
├── .history.json              # Aggregated continual metrics
├── abstract/
│   ├── skill-auditor/
│   │   └── 2025-01-08.jsonl   # Daily JSONL files
│   └── plugin-validator/
├── sanctum/
│   └── pr-review/
└── <your-plugin>/
    └── <your-skill>/
```

### Quick Start

```bash
# View recent skill executions
/skill-logs --last 1h

# View failures only
/skill-logs --failures-only

# Filter by plugin
/skill-logs --plugin abstract

# Cleanup old logs
/skill-logs cleanup --older-than 90d
```

### Integration with pensive

Use `/pensive:skill-review` to analyze metrics and identify unstable skills:

```bash
# Check skill health
/pensive:skill-review --unstable-only

# Deep-dive specific skill
/pensive:skill-review --skill abstract:skill-auditor
```

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
| `memory-palace-architect` | Design and construct virtual memory palaces. |
| `knowledge-locator` | Find information using multi-modal search. |
| `session-palace-builder` | Create temporary session-specific palaces. |
| `digital-garden-cultivator` | Manage evolving knowledge bases. |
| `knowledge-intake` | Process and evaluate external knowledge. |
| `review-chamber` | Capture PR review knowledge in project palaces. |

## Commands

| Command | Description |
|---------|-------------|
| `/palace` | Create and manage memory palaces. |
| `/garden` | Manage digital gardens and metrics. |
| `/navigate` | Search and navigate across palaces. |
| `/review-room` | Manage PR review knowledge in project palaces. |
| `/skill-logs` | View and manage skill execution memories. |

## Agents

| Agent | Description |
|-------|-------------|
| `palace-architect` | Design palace architectures. |
| `knowledge-navigator` | Search and retrieve information. |
| `garden-curator` | Maintain digital gardens. |

## Hooks

Hooks integrate Memory Palace with Claude Code events:

| Hook | Event | Description |
|------|-------|-------------|
| `research_interceptor.py` | PreToolUse | Checks local knowledge cache before web requests. |
| `local_doc_processor.py` | PostToolUse | Monitors Read operations for indexing suggestions. |
| `url_detector.py` | UserPromptSubmit | Detects URLs for potential knowledge intake. |
| `web_content_processor.py` | PostToolUse | Processes web content for knowledge extraction. |
| `skill_tracker_pre.py` | PreToolUse | Records start time when Skill tool is invoked. |
| `skill_tracker_post.py` | PostToolUse | Logs completion, calculates metrics, stores memory. |

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

Session forking allows testing knowledge organization strategies without committing to a single structure:

```bash
# Fork for hierarchical organization
claude --fork-session --session-id "hierarchical-tags" --resume
> "Organize using hierarchical tags"

# Fork for concept-map approach
claude --fork-session --session-id "concept-map" --resume
> "Organize using semantic relationships"
```

**Best Practices**: Test with representative content, extract successful designs as templates.

See `plugins/abstract/docs/claude-code-compatibility.md` for detailed patterns.

## License

MIT
