#!/usr/bin/env python3
"""War Room Orchestrator - backward compatibility wrapper.

This module has been refactored into the war_room package.
All imports are re-exported here for backward compatibility.

Usage:
    from war_room_orchestrator import WarRoomOrchestrator

    orchestrator = WarRoomOrchestrator()
    session = await orchestrator.convene(
        problem="What architecture should we use?",
        context_files=["src/**/*.py"],
        mode="lightweight"
    )
"""

from __future__ import annotations

# Backward compatibility - import everything from package
from scripts.war_room import (  # noqa: F401
    EXPERT_CONFIGS,
    FULL_COUNCIL,
    LIGHTWEIGHT_PANEL,
    DeliberationNode,
    ExpertConfig,
    MerkleDAG,
    WarRoomOrchestrator,
    WarRoomSession,
    check_expert_availability,
    clear_availability_cache,
    get_expert_command,
    get_fallback_notice,
    get_glm_command,
    get_haiku_command,
)

# Module-level state re-exports for test patching compatibility
from scripts.war_room.experts import (  # noqa: F401
    _expert_availability,
    _haiku_fallback_notices,
)

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    import sys

    async def main() -> None:
        """CLI entry point for War Room orchestrator."""
        if len(sys.argv) < 2:
            print("Usage: war_room_orchestrator.py <problem_statement>")
            sys.exit(1)

        problem = " ".join(sys.argv[1:])
        orchestrator = WarRoomOrchestrator()
        session = await orchestrator.convene(problem=problem, mode="lightweight")
        print(f"Session completed: {session.session_id}")
        print(f"Status: {session.status}")
        print(f"Phases: {session.phases_completed}")

    asyncio.run(main())
