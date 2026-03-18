---
area_name: plugins/egregore
ownership_globs:
  - "plugins/egregore/**"
tags:
  - autonomous-agent
  - orchestration
  - pipeline
---

# plugins/egregore Area Guide

The autonomous orchestrator -- reads manifests, picks
work items, drives the full development lifecycle.

## Patterns

- Orchestrator agent runs autonomously without human
  input, processing work items from .egregore/manifest.json
- Pipeline has 4 stages: intake, build, quality, ship
- Sentinel agent monitors resource budget for graceful
  shutdown
- Continuation agents handle context overflow

## Pitfalls

- The orchestrator MUST NOT stop early or ask "should
  I continue?" -- it persists until dismissed
- Bounded mode stops at time limit, not item completion
- Mode detection (bounded vs indefinite) uses
  manifest.json config, not heuristics
- Output gate requires actual deliverables before
  marking items complete

## Testing

```bash
cd plugins/egregore && uv run python -m pytest tests/ -v --tb=short
```

## Review Focus

- Pipeline stage transitions and idempotency
- Budget monitoring and graceful shutdown
- Manifest parsing and work item lifecycle
- Anti-relabeling rules (items cannot regress)
