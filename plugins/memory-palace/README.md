# Memory Palace Plugin

Spatial knowledge organization using memory palace techniques for Claude Code.

## Overview

Memory Palace organizes information using spatial memory techniques for easier
retrieval. It builds "palaces" (knowledge repositories with spatial
metaphors), "gardens" (organic knowledge bases with bidirectional links),
and a "review chamber" for capturing PR review knowledge.

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
Palace holds domain knowledge in navigable
hierarchies that persist as a permanent corpus.
The three layers work together.

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

- **Palace Architect**: Design spatial knowledge structures using mnemonic
  techniques
- **Knowledge Locator**: Multi-modal search (keyword, semantic,
  spatial) across palaces
- **Session Palaces**: Temporary structures for extended conversations
- **Digital Gardens**: Evolving knowledge bases with bidirectional linking
- **PR Review Chamber**: Capture architectural decisions, patterns,
  and lessons from PR reviews
- **Skill Execution Memory**:
  Automatic logging of skill invocations for continual learning
- **Semantic Deduplication**:
  FAISS cosine similarity (with Jaccard fallback) prevents near-duplicate
  storage
- **Research Interceptor**:
  Checks local knowledge cache before making web requests

## Skills

| Skill | Description |
|-------|-------------|
| `memory-palace-architect` | Design and construct virtual memory palaces. |
| `knowledge-locator` | Find information using multi-modal search. |
| `session-palace-builder` | Create temporary session-specific palaces. |
| `digital-garden-cultivator` | Manage evolving knowledge bases. |
| `knowledge-intake` | Process and evaluate external knowledge. |
| `review-chamber` | Capture PR review knowledge in project palaces. |
| `palace-diagram` | Draw palace structure and topology as Mermaid or ASCII. |
| `palace-index-curator` | Curate the web-capture index: rebuild, promote, archive. |
| `memory-clarity-probe` | Check session state clarity before handoff or compression. |

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
| `user_prompt.py` | UserPromptSubmit | One process for URL detection (`_url_detector.py`) and `+recall` (`_recall.py`). |
| `web_research_handler.py` | PostToolUse | Processes web content for knowledge extraction. |
| `skill_tracker_pre.py` | PreToolUse | Records start time when Skill tool is invoked. |
| `skill_tracker_post.py` | PostToolUse | Logs completion, calculates metrics, stores memory. |
| `research_queue.py` | SessionEnd | Queues the session's web research for corpus evaluation ([details](hooks/research-queue-integration.md)). |

Setup hook (`claude --init-only`,
`claude -p --maintenance "<prompt>"`) handles one-time initialization
and periodic garden maintenance. See `hooks/hooks.json` for configuration.

## Architecture

```
memory-palace/
├── .claude-plugin/
│   └── plugin.json
├── skills/              # 9 skills (see Skills table above)
├── commands/            # 5 commands (palace, garden, navigate, review-room, skill-logs)
├── agents/              # 4 agents (architect, navigator, librarian, curator)
├── hooks/               # 6 runtime hooks + setup hook
├── src/memory_palace/
│   ├── palace_manager.py
│   ├── project_palace/  # rooms.py, entry.py, manager.py, capture.py
│   ├── corpus/          # Indexing, caching, deduplication, lineage
│   └── lifecycle/       # Autonomy state, decay model
├── scripts/             # CLI tools and metrics
└── tests/
```

### Why the capture index is local state

`hooks/memory-palace-index.yaml` is gitignored. A session hook rewrites
it on every web capture, and a tracked copy went stale on every branch.
Two branches that both captured URLs conflicted on merge. Issue #620
kept it tracked to make the drain queue and the corpus it feeds move
together. Issue #1067 reversed that and classed the index as state.

The drain still works the same way. `web_research_handler` appends a
capture as `pending`. `scripts/precommit_palace_maintenance.sh` runs the
`index_promoter` drain on every commit. The drain promotes an entry
into `docs/knowledge-corpus/`, which is committed, or archives it, or
holds it. pre-commit leaves an ignored file in place, and the drain
reads every local capture. A promoted entry records its source URLs in
its `sources` frontmatter, which carries its provenance into the
commit. A
fresh clone has no index, and the first capture creates it.

Three gates hold the drain, and they run in `make test`:

- `test_capture_index_drain_gate.py` blocks a commit while the local
  index holds an entry still `pending`. The drain cannot quietly fall
  behind.
- `test_capture_index_artifact.py` applies the dedup invariants to the
  local index when one exists. A hook that corrupts it fails a gate.
- `test_index_prune_cli_guard.py` covers the prune path that once left
  dangling hash references behind.

## Requirements

- Python 3.9+
- Claude Code

## Documentation

- [Book: Memory Palace Plugin](../../book/src/plugins/memory-palace.md) for
  detailed usage, cache modes, palace architecture, and curation workflows
- [PR Review Chamber](skills/review-chamber/SKILL.md) for review knowledge
  capture
- [Skill Execution Memory](commands/skill-logs.md) for execution history
  and metrics

## Stewardship

Ways to leave this plugin better than you found it:

- Palace architecture examples could include a walkthrough
  showing how spatial metaphors map to real knowledge
- The semantic deduplication threshold (FAISS cosine
  similarity) is an opportunity to document how to tune
  it for different content densities
- Hook descriptions would benefit from latency
  expectations so users understand the per-operation cost
- The research interceptor cache hit/miss ratio could be
  surfaced as a quick health metric in `/palace` output
- Garden maintenance workflows could include a short
  guide on pruning stale nodes

See [STEWARDSHIP.md](../../STEWARDSHIP.md) for the full
stewardship principles guiding this project.

## License

MIT
