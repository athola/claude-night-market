---
name: hook-integration
description: Memory-palace hooks that signal knowledge-intake candidates, with their deduplication index and safety checks
category: integration
tags: [hooks, url-detection, deduplication, safety]
dependencies: [knowledge-intake]
complexity: intermediate
estimated_tokens: 550
---

## Hook Integration

Memory-palace hooks automatically detect content that may need knowledge intake processing:

### Automatic Triggers

| Hook | Event | When Triggered |
|------|-------|----------------|
| `url_detector` | UserPromptSubmit | User message contains URLs |
| `web_content_processor` | PostToolUse (WebFetch/WebSearch) | After fetching web content |
| `local_doc_processor` | PostToolUse (Read) | Reading files in knowledge paths |
| `research_queue_integration` | SessionEnd | Research sessions with 3+ WebSearch calls |

### Hook Signals

When hooks detect potential knowledge content, they add context messages:

```
**Verification:** Run `pytest -v` to verify tests pass.
Memory Palace: New web content fetched from {url}.
Consider running knowledge-intake to evaluate and store if valuable.
```
**Verification:** Run the command with `--help` flag to verify availability.

```
**Verification:** Run the command with `--help` flag to verify availability.
Memory Palace: Reading local knowledge doc '{path}'.
This path is configured for knowledge tracking.
Consider running knowledge-intake if this contains valuable reference material.
```
**Verification:** Run the command with `--help` flag to verify availability.

### Deduplication

Hooks check the `memory-palace-index.yaml` to avoid redundant processing:
- **Known URLs**: "Content already indexed" - skip re-evaluation
- **Changed content**: "Content has changed" - suggest update
- **New content**: Full evaluation recommended

### Safety Checks

Before signaling intake, hooks validate content:
- Size limits (default 500KB)
- Secret detection (API keys, credentials)
- Data bomb prevention (repetition, unicode bombs)
- Prompt injection sanitization

### Index Schema Alignment

The deduplication index stores fields aligned with this skill's evaluation:

```yaml
entries:
  "https://example.com/article":
    content_hash: "xxh:abc123..."
    stored_at: "docs/knowledge-corpus/article.md"
    importance_score: 82           # From evaluation framework, in [0, 100]
    maturity: "growing"            # seedling, growing, evergreen
    routing_type: "both"           # local, meta, both
    last_updated: "2025-12-06T..."
```
**Verification:** Run the command with `--help` flag to verify availability.
