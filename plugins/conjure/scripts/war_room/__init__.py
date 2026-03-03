"""War Room package - multi-LLM deliberation orchestration.

Re-exports WarRoomOrchestrator and key types for backward compatibility.

Usage:
    from war_room import WarRoomOrchestrator

    orchestrator = WarRoomOrchestrator()
    session = await orchestrator.convene(
        problem="What architecture should we use?",
        context_files=["src/**/*.py"],
        mode="lightweight"
    )
"""

from __future__ import annotations

from scripts.war_room.experts import (
    EXPERT_CONFIGS,
    FULL_COUNCIL,
    LIGHTWEIGHT_PANEL,
    check_expert_availability,
    clear_availability_cache,
    get_expert_command,
    get_fallback_notice,
    get_glm_command,
    get_haiku_command,
)
from scripts.war_room.hooks import should_suggest_war_room
from scripts.war_room.models import (
    DeliberationNode,
    ExpertConfig,
    ExpertInfo,
    MerkleDAG,
    WarRoomSession,
)
from scripts.war_room.orchestrator import WarRoomOrchestrator

__all__ = [
    # Main class
    "WarRoomOrchestrator",
    # Data structures
    "DeliberationNode",
    "ExpertConfig",
    "ExpertInfo",
    "MerkleDAG",
    "WarRoomSession",
    # Expert configuration
    "EXPERT_CONFIGS",
    "FULL_COUNCIL",
    "LIGHTWEIGHT_PANEL",
    # Command resolution
    "get_expert_command",
    "get_glm_command",
    "get_haiku_command",
    # Availability
    "clear_availability_cache",
    "get_fallback_notice",
    "check_expert_availability",
    # Hooks
    "should_suggest_war_room",
]
