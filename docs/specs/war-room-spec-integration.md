# War Room Specification: Integration

**Part of**: [War Room Specification](war-room-spec-overview.md)

---

## Conjure Integration

### New Module: war_room_orchestrator.py

```python
#!/usr/bin/env python3
"""
War Room Orchestrator

Composes delegation_executor calls to orchestrate multi-LLM deliberation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import asyncio

from delegation_executor import Delegator, ExecutionResult


class WarRoomOrchestrator:
    """
    Orchestrates multi-LLM deliberation sessions.

    Responsibilities:
    - Expert panel management
    - Phase sequencing
    - Parallel dispatch via delegation_executor
    - Response aggregation
    - Merkle-DAG maintenance
    - Strategeion persistence
    """

    async def convene_war_room(
        self,
        problem_statement: str,
        context_files: list[str] = None,
        mode: str = "lightweight"
    ) -> WarRoomSession:
        """
        Convene a new War Room session.
        """
        session = self._initialize_session(problem_statement, mode)

        # Phase 1-7 execution
        await self._phase_intel(session, context_files)
        await self._phase_assessment(session)
        await self._phase_coa_development(session)

        if await self._should_escalate(session):
            session.mode = "full_council"
            await self._escalate_to_full_council(session)

        await self._phase_red_team(session)
        await self._phase_voting(session)
        await self._phase_premortem(session)
        await self._phase_synthesis(session)

        self._persist_to_strategeion(session)
        return session
```

### Service Configuration Extension

```json
{
  "services": {
    "gemini": { ... },
    "qwen": { ... },
    "claude-glm": {
      "command": "claude",
      "args": ["--model", "glm-4.7", "-p"],
      "auth_method": "anthropic_api"
    }
  },
  "war_room": {
    "default_mode": "lightweight",
    "escalation_threshold": 0.7,
    "delphi_convergence_threshold": 0.85,
    "max_delphi_rounds": 5
  }
}
```

---

## Command: /attune:war-room

```yaml
name: war-room
description: Convene a multi-LLM War Room for strategic decision making
```

### Usage

```bash
# Basic invocation
/attune:war-room "Problem statement here"

# With context files
/attune:war-room "Problem" --files src/**/*.py

# Force full council
/attune:war-room "Problem" --full-council

# High-stakes (Delphi mode)
/attune:war-room "Problem" --delphi

# Resume session
/attune:war-room --resume {session-id}
```

### Arguments

- `--files <globs...>` - Context files for analysis
- `--full-council` - Skip lightweight, use full expert panel
- `--delphi` - Use iterative Delphi convergence
- `--resume <session-id>` - Resume interrupted session
- `--archive <name>` - Name for campaign archive

---

## Skill: attune:war-room

```yaml
name: war-room
description: Multi-LLM deliberation framework for strategic decisions
triggers: war room, strategic decision, multi-expert, deliberation, council
use_when: complex decisions requiring multiple perspectives
do_not_use_when: simple questions, routine tasks
category: strategic-planning
tags: [deliberation, multi-llm, strategy, decision-making]
dependencies:
  - conjure:delegation-core
  - memory-palace:strategeion
tools: [war-room-orchestrator]
complexity: advanced
estimated_tokens: 2000
progressive_loading: true
modules:
  - modules/expert-roles.md
  - modules/deliberation-protocol.md
  - modules/red-team-patterns.md
  - modules/synthesis-framework.md
  - modules/merkle-dag.md
```

### When to Use

- Architectural decisions with major trade-offs
- Multi-stakeholder problems requiring diverse perspectives
- High-stakes choices with significant consequences
- Novel problems without clear precedent

---

## Hook Auto-Trigger Configuration

```json
{
  "war_room_auto_trigger": {
    "enabled": true,
    "require_user_opt_in": true,

    "complexity_threshold": {
      "enabled": true,
      "threshold": 0.7
    },

    "keyword_detection": {
      "enabled": true,
      "trigger_keywords": [
        "war room", "council", "deliberation",
        "strategic decision", "major trade-off",
        "architectural decision", "high stakes"
      ]
    },

    "user_settings": {
      "enabled": true,
      "setting_key": "war_room.auto_trigger",
      "default": false
    }
  }
}
```

### User Settings

```json
// ~/.claude/settings.json
{
  "war_room": {
    "auto_trigger": true,
    "complexity_threshold": 0.7,
    "always_suggest": false
  }
}
```

---

**Next**: See [Implementation](war-room-spec-implementation.md) for phases and success criteria.
