---
name: session-routing
description: |
  Route multi-area work to subagents or dedicated
  sessions based on complexity. Prevents quality
  degradation from parallel subagent overload.
category: coordination
---

# Session Routing

Decide whether work should use subagents or dedicated
sessions based on the number of areas involved.

## Routing Rules

| Condition | Route | Reason |
|-----------|-------|--------|
| 1-3 areas, focused scope | Subagent | Low coordination overhead, parent context can handle results |
| 4+ areas | Dedicated sessions | Each area needs full context window, parallel subagents degrade |
| Codebase-wide | Sequential sessions | One area at a time, results accumulate in files |

## Decision Logic

```python
from scripts.agent_memory import decide_session_routing

decision = decide_session_routing(
    files=["plugins/imbue/a.py", "plugins/conserve/b.py"],
    areas=["plugins/imbue", "plugins/conserve"],
)
# Returns RoutingDecision.SUBAGENT (2 areas < 4 threshold)
```

## Subagent Route

- Standard Task tool dispatch
- Each agent gets a tight scope prompt
- Results return through parent context
- Works well for 1-3 focused areas

## Dedicated Session Route

- Use Agent Teams or separate tmux panes
- Each session gets a full clean context window
- Coordinate via `.coordination/` files (see
  findings-format module)
- Parent reads only summaries for synthesis

## Sequential Route

- For codebase-wide operations
- Process one area at a time
- Each session completes before the next begins
- Results accumulate in `.coordination/agents/`
- Final synthesis session reads all findings

## Integration

- `decide_session_routing()` in `scripts/agent_memory.py`
  implements the decision logic
- Integrates with `plan-before-large-dispatch` rule
  (4+ areas trigger plan mode)
- Area-agent configs (`.claude/area-agents/`) provide
  area-specific context for each session
