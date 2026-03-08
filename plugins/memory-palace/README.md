# Memory Palace Plugin

Spatial knowledge organization using memory palace techniques for Claude Code.

## Overview

Memory Palace organizes information using spatial memory techniques for easier retrieval. It builds "palaces" (structured knowledge repositories with spatial metaphors), "gardens" (organic knowledge bases with bidirectional links), and a "review chamber" for capturing PR review knowledge.

### How This Differs from Native Claude Memory

| Layer | Scope | Control |
|-------|-------|---------|
| **Auto-Memory** (2.1.59+) | Conversation context | Implicit, managed via `/memory` |
| **Agent `memory` Frontmatter** (2.1.33+) | Agent-scoped recall | Opt-in per agent |
| **Memory Palace** | Domain knowledge with spatial hierarchies | Explicit, user-designed |

Auto-memory (2.1.59+) saves useful conversation context
to `~/.claude/projects/*/memory/MEMORY.md` and is
managed via the `/memory` command. Agent memory
frontmatter gives agents persistent recall. Memory
Palace provides structured, navigable knowledge
architectures that persist as a permanent corpus.
These systems are complementary, not conflicting.

## Installation

```bash
claude plugins add memory-palace@claude-night-market
```

## Quick Start

```bash
# Create a palace
/palace create "K8s Concepts"

# Add knowledge from an external source
Skill(memory-palace:knowledge-intake)

# Search across palaces
/navigate "authentication"

# Check garden health
/garden status
```

## Features

- **Palace Architect**: Design spatial knowledge structures using mnemonic techniques
- **Knowledge Locator**: Multi-modal search (keyword, semantic, spatial) across palaces
- **Session Palaces**: Temporary structures for extended conversations
- **Digital Gardens**: Evolving knowledge bases with bidirectional linking
- **PR Review Chamber**: Capture architectural decisions, patterns, and lessons from PR reviews
- **Skill Execution Memory**: Automatic logging of skill invocations for continual learning
- **Semantic Deduplication**: FAISS cosine similarity (with Jaccard fallback) prevents near-duplicate storage
- **Research Interceptor**: Checks local knowledge cache before making web requests

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
| `knowledge-librarian` | Evaluate and route knowledge. |
| `garden-curator` | Maintain digital gardens. |

## Hooks

| Hook | Event | Description |
|------|-------|-------------|
| `research_interceptor.py` | PreToolUse | Checks local knowledge cache before web requests. |
| `local_doc_processor.py` | PostToolUse | Monitors Read operations for indexing suggestions. |
| `url_detector.py` | UserPromptSubmit | Detects URLs for potential knowledge intake. |
| `web_content_processor.py` | PostToolUse | Processes web content for knowledge extraction. |
| `skill_tracker_pre.py` | PreToolUse | Records start time when Skill tool is invoked. |
| `skill_tracker_post.py` | PostToolUse | Logs completion, calculates metrics, stores memory. |

Setup hook (`claude --init`, `claude --maintenance`) handles one-time initialization and periodic garden maintenance. See `hooks/hooks.json` for configuration.

## Optional Dependencies

| Package | Purpose | Fallback |
|---------|---------|----------|
| tiktoken | Accurate token estimation | Heuristic (~4 chars/token) |

```bash
pip install tiktoken
```

## Architecture

```
memory-palace/
├── .claude-plugin/
│   └── plugin.json
├── skills/              # 6 skills (architect, locator, garden, session, intake, review)
├── commands/            # 5 commands (palace, garden, navigate, review-room, skill-logs)
├── agents/              # 4 agents (architect, navigator, librarian, curator)
├── hooks/               # 6 runtime hooks + setup hook
├── src/memory_palace/
│   ├── palace_manager.py
│   ├── project_palace.py
│   ├── corpus/          # Indexing, caching, deduplication, lineage
│   └── lifecycle/       # Autonomy state, decay model
├── scripts/             # CLI tools, metrics, embedding builder
└── tests/
```

## Requirements

- Python 3.12+
- Claude Code

## Documentation

- [Book: Memory Palace Plugin](../../book/src/plugins/memory-palace.md) for detailed usage, cache modes, palace architecture, and curation workflows
- [PR Review Chamber](skills/review-chamber/SKILL.md) for review knowledge capture
- [Skill Execution Memory](commands/skill-logs.md) for execution history and metrics

## License

MIT
