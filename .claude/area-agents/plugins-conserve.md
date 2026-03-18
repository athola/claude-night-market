---
area_name: plugins/conserve
ownership_globs:
  - "plugins/conserve/**"
tags:
  - context-optimization
  - token-conservation
  - bloat-detection
  - coordination
---

# plugins/conserve Area Guide

Context optimization and resource management -- keeps
agent context lean and coordinates subagent workflows.

## Patterns

- MECW (Minimum Effective Context Window) principle:
  load only what's needed for the current task
- Three-tier alert system: OK (<40%), WARNING (40-50%),
  CRITICAL (50-80%), EMERGENCY (80%+)
- Bloat detection runs in progressive tiers (1-3)
- Continuation agents handle context overflow with
  session state checkpointing
- Coordination workspace manages .coordination/ for
  file-based inter-agent communication

## Pitfalls

- Never use verbose commands that dump large outputs
- Subagent conversations auto-compact at ~160k tokens
- Background agents prompt for permissions upfront
  (since 2.1.20+)
- Growth analyzer tracks file-level token changes over
  time -- check before adding large files

## Testing

```bash
cd plugins/conserve && uv run python -m pytest tests/ -v --tb=short
```

## Review Focus

- Token efficiency of any new skills or modules
- Context overhead of coordination mechanisms
- Conservation mode compliance (quick/deep/normal)
