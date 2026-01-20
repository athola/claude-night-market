#!/usr/bin/env python3
"""War Room Orchestrator.

Orchestrates multi-LLM deliberation sessions for strategic decision making.
Composes delegation calls to manage expert panels, anonymization, and synthesis.

Note: Uses asyncio.create_subprocess_exec (safe, no shell injection).

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

import asyncio
import json
import shutil
import subprocess  # nosec B404 - Used safely with create_subprocess_exec (no shell)
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class DeliberationNode:
    """A single contribution in the deliberation graph."""

    node_id: str
    parent_id: str | None
    round_number: int
    phase: str
    anonymous_label: str
    content: str
    expert_role: str
    expert_model: str
    content_hash: str
    metadata_hash: str
    combined_hash: str
    timestamp: str


@dataclass
class MerkleDAG:
    """Directed Acyclic Graph tracking deliberation history."""

    session_id: str
    sealed: bool = True
    root_hash: str | None = None
    nodes: dict[str, DeliberationNode] = field(default_factory=dict)
    label_counter: dict[str, int] = field(default_factory=dict)

    def add_contribution(  # noqa: PLR0913
        self,
        content: str,
        phase: str,
        round_number: int,
        expert_role: str,
        expert_model: str,
        parent_id: str | None = None,
    ) -> DeliberationNode:
        """Add a contribution and compute hashes."""
        content_hash = sha256(content.encode()).hexdigest()
        metadata_hash = sha256(f"{expert_role}:{expert_model}".encode()).hexdigest()
        combined_hash = sha256(f"{content_hash}:{metadata_hash}".encode()).hexdigest()

        label = self._generate_label(phase)

        node = DeliberationNode(
            node_id=combined_hash[:16],
            parent_id=parent_id,
            round_number=round_number,
            phase=phase,
            anonymous_label=label,
            content=content,
            expert_role=expert_role,
            expert_model=expert_model,
            content_hash=content_hash,
            metadata_hash=metadata_hash,
            combined_hash=combined_hash,
            timestamp=datetime.now().isoformat(),
        )

        self.nodes[node.node_id] = node
        self._update_root_hash()
        return node

    def _generate_label(self, phase: str) -> str:
        """Generate anonymous label for phase."""
        if phase not in self.label_counter:
            self.label_counter[phase] = 0
        self.label_counter[phase] += 1
        count = self.label_counter[phase]

        if phase == "coa":
            return f"Response {chr(64 + count)}"  # A, B, C...
        return f"Expert {count}"

    def _update_root_hash(self) -> None:
        """Update root hash from all leaf nodes."""
        if not self.nodes:
            self.root_hash = None
            return
        combined = ":".join(sorted(n.combined_hash for n in self.nodes.values()))
        self.root_hash = sha256(combined.encode()).hexdigest()

    def get_anonymized_view(self, phase: str | None = None) -> list[dict[str, Any]]:
        """Return contributions with attribution masked."""
        nodes_iter = list(self.nodes.values())
        if phase:
            nodes_iter = [n for n in nodes_iter if n.phase == phase]
        return [
            {
                "label": node.anonymous_label,
                "content": node.content,
                "phase": node.phase,
                "round": node.round_number,
                "hash": node.node_id,
            }
            for node in nodes_iter
        ]

    def unseal(self) -> list[dict[str, Any]]:
        """Reveal full attribution after decision is made."""
        self.sealed = False
        return [
            {
                "label": node.anonymous_label,
                "content": node.content,
                "phase": node.phase,
                "round": node.round_number,
                "expert_role": node.expert_role,
                "expert_model": node.expert_model,
                "hash": node.node_id,
            }
            for node in self.nodes.values()
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize for persistence."""
        return {
            "session_id": self.session_id,
            "sealed": self.sealed,
            "root_hash": self.root_hash,
            "label_counter": self.label_counter,
            "nodes": {
                nid: {
                    "node_id": n.node_id,
                    "parent_id": n.parent_id,
                    "round_number": n.round_number,
                    "phase": n.phase,
                    "anonymous_label": n.anonymous_label,
                    "content": n.content,
                    "expert_role": n.expert_role if not self.sealed else "[SEALED]",
                    "expert_model": n.expert_model if not self.sealed else "[SEALED]",
                    "content_hash": n.content_hash,
                    "metadata_hash": n.metadata_hash,
                    "combined_hash": n.combined_hash,
                    "timestamp": n.timestamp,
                }
                for nid, n in self.nodes.items()
            },
        }


@dataclass
class ExpertConfig:
    """Configuration for a War Room expert."""

    role: str
    service: str
    model: str
    description: str
    phases: list[str]
    dangerous: bool = True
    command: list[str] | None = None
    command_resolver: str | None = None


@dataclass
class WarRoomSession:
    """Active War Room deliberation session."""

    session_id: str
    problem_statement: str
    mode: str = "lightweight"
    status: str = "initialized"
    merkle_dag: MerkleDAG = field(default_factory=lambda: MerkleDAG(""))
    phases_completed: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    escalated: bool = False
    escalation_reason: str | None = None

    def __post_init__(self) -> None:
        """Initialize session with session_id on merkle_dag if not set."""
        if not self.merkle_dag.session_id:
            self.merkle_dag.session_id = self.session_id


# ---------------------------------------------------------------------------
# Expert Configuration
# ---------------------------------------------------------------------------

EXPERT_CONFIGS: dict[str, ExpertConfig] = {
    "supreme_commander": ExpertConfig(
        role="Supreme Commander",
        service="native",
        model="claude-opus-4",
        description="Final decision authority and synthesis",
        phases=["synthesis"],
        dangerous=False,
    ),
    "chief_strategist": ExpertConfig(
        role="Chief Strategist",
        service="native",
        model="claude-sonnet-4",
        description="Approach generation and trade-off analysis",
        phases=["assessment", "coa"],
        dangerous=False,
    ),
    "intelligence_officer": ExpertConfig(
        role="Intelligence Officer",
        service="gemini",
        model="gemini-2.5-pro-exp",
        description="Deep context analysis with 1M+ token window",
        phases=["intel"],
        command=["gemini", "--model", "gemini-2.5-pro-exp", "-p"],
    ),
    "field_tactician": ExpertConfig(
        role="Field Tactician",
        service="glm",
        model="glm-4.7",
        description="Implementation feasibility assessment",
        phases=["coa"],
        command_resolver="get_glm_command",
    ),
    "scout": ExpertConfig(
        role="Scout",
        service="qwen",
        model="qwen-turbo",
        description="Rapid reconnaissance and data gathering",
        phases=["intel"],
        command=["qwen", "--model", "qwen-turbo", "-p"],
    ),
    "red_team": ExpertConfig(
        role="Red Team Commander",
        service="gemini",
        model="gemini-2.0-flash-exp",
        description="Adversarial challenge and failure mode identification",
        phases=["red_team", "premortem"],
        command=["gemini", "--model", "gemini-2.0-flash-exp", "-p"],
    ),
    "logistics_officer": ExpertConfig(
        role="Logistics Officer",
        service="qwen",
        model="qwen-max",
        description="Resource estimation and dependency analysis",
        phases=["coa"],
        command=["qwen", "--model", "qwen-max", "-p"],
    ),
}

LIGHTWEIGHT_PANEL = ["supreme_commander", "chief_strategist", "red_team"]
FULL_COUNCIL = list(EXPERT_CONFIGS.keys())


# ---------------------------------------------------------------------------
# Command Resolution
# ---------------------------------------------------------------------------


def get_glm_command() -> list[str]:
    """Resolve GLM-4.7 invocation command with fallback.

    Priority:
    1. ccgd (alias) - if available in PATH
    2. claude-glm --dangerously-skip-permissions - explicit fallback
    3. ~/.local/bin/claude-glm - direct path fallback
    """
    if shutil.which("ccgd"):
        return ["ccgd", "-p"]

    if shutil.which("claude-glm"):
        return ["claude-glm", "--dangerously-skip-permissions", "-p"]

    local_bin = Path.home() / ".local" / "bin" / "claude-glm"
    if local_bin.exists():
        return [str(local_bin), "--dangerously-skip-permissions", "-p"]

    raise RuntimeError(
        "GLM-4.7 not available. Install claude-glm or configure ccgd alias.\n"
        "Add to ~/.bashrc: alias ccgd='claude-glm --dangerously-skip-permissions'"
    )


def get_expert_command(expert: ExpertConfig) -> list[str]:
    """Get the command to invoke an expert."""
    if expert.command_resolver:
        resolver = globals().get(expert.command_resolver)
        if resolver and callable(resolver):
            cmd = resolver()
            if isinstance(cmd, list):
                return cmd
            raise RuntimeError(
                f"Resolver {expert.command_resolver} did not return list"
            )
        raise RuntimeError(f"Unknown command resolver: {expert.command_resolver}")
    if expert.command:
        return expert.command.copy()
    raise RuntimeError(f"No command configured for {expert.role}")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class WarRoomOrchestrator:
    """Orchestrates multi-LLM deliberation sessions.

    Responsibilities:
    - Expert panel management
    - Phase sequencing
    - Parallel dispatch
    - Response aggregation
    - Merkle-DAG maintenance
    - Strategeion persistence
    """

    def __init__(self, strategeion_path: Path | None = None) -> None:
        """Initialize orchestrator with Strategeion storage path."""
        self.strategeion = strategeion_path or (
            Path.home() / ".claude" / "memory-palace" / "strategeion"
        )
        self.strategeion.mkdir(parents=True, exist_ok=True)

    async def convene(
        self,
        problem: str,
        context_files: list[str] | None = None,
        mode: str = "lightweight",
    ) -> WarRoomSession:
        """Convene a new War Room session.

        Args:
            problem: The problem/decision to deliberate
            context_files: Optional file globs for context
            mode: "lightweight" or "full_council"

        Returns:
            Completed WarRoomSession with decision

        """
        session = self._initialize_session(problem, mode)
        session.metrics["start_time"] = datetime.now().isoformat()

        try:
            # Phase 1: Intelligence
            await self._phase_intel(session, context_files)

            # Phase 2: Assessment
            await self._phase_assessment(session)

            # Phase 3: COA Development
            await self._phase_coa_development(session)

            # Escalation check
            if mode == "lightweight" and await self._should_escalate(session):
                session.escalated = True
                session.mode = "full_council"
                await self._escalate(session, context_files)

            # Phase 4: Red Team
            await self._phase_red_team(session)

            # Phase 5: Voting
            await self._phase_voting(session)

            # Phase 6: Premortem
            await self._phase_premortem(session)

            # Phase 7: Synthesis
            await self._phase_synthesis(session)

            session.status = "completed"

        except Exception as e:
            session.status = f"failed: {e}"
            raise

        finally:
            session.metrics["end_time"] = datetime.now().isoformat()
            self._persist_session(session)

        return session

    def _initialize_session(self, problem: str, mode: str) -> WarRoomSession:
        """Create new session with unique ID."""
        session_id = f"war-room-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return WarRoomSession(
            session_id=session_id,
            problem_statement=problem,
            mode=mode,
            merkle_dag=MerkleDAG(session_id),
        )

    async def _invoke_expert(
        self,
        expert_key: str,
        prompt: str,
        session: WarRoomSession,
        phase: str,
    ) -> str:
        """Invoke a single expert and record contribution."""
        expert = EXPERT_CONFIGS[expert_key]

        if expert.service == "native":
            # Native experts (Opus, Sonnet) handled by orchestrating Claude
            result = f"[Native expert {expert.role} response placeholder]"
        else:
            result = await self._invoke_external(expert, prompt)

        # Record in Merkle-DAG
        session.merkle_dag.add_contribution(
            content=result,
            phase=phase,
            round_number=len(session.phases_completed) + 1,
            expert_role=expert.role,
            expert_model=expert.model,
        )

        return result

    async def _invoke_external(self, expert: ExpertConfig, prompt: str) -> str:
        """Invoke external expert via CLI.

        Uses asyncio.create_subprocess_exec (safe, no shell injection).
        Arguments passed as list, not through shell.
        """
        cmd = get_expert_command(expert)
        cmd.append(prompt)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=120.0,
            )

            if proc.returncode != 0:
                return f"[{expert.role} failed: {stderr.decode()[:500]}]"

            return stdout.decode()

        except TimeoutError:
            return f"[{expert.role} timed out after 120s]"
        except FileNotFoundError:
            return f"[{expert.role} command not found: {cmd[0]}]"
        except Exception as e:
            return f"[{expert.role} error: {e}]"

    async def _invoke_parallel(
        self,
        expert_keys: list[str],
        prompts: dict[str, str],
        session: WarRoomSession,
        phase: str,
    ) -> dict[str, str]:
        """Invoke multiple experts in parallel."""
        tasks = {
            key: self._invoke_expert(
                key, prompts.get(key, prompts.get("default", "")), session, phase
            )
            for key in expert_keys
            if key in EXPERT_CONFIGS
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        output: dict[str, str] = {}
        for key, result in zip(tasks.keys(), results, strict=False):
            if isinstance(result, BaseException):
                output[key] = f"[Error: {result}]"
            elif isinstance(result, str):
                output[key] = result
            else:
                output[key] = str(result)
        return output

    # ---------------------------------------------------------------------------
    # Phase Implementations (Stubs for Phase 1)
    # ---------------------------------------------------------------------------

    async def _phase_intel(
        self, session: WarRoomSession, context_files: list[str] | None
    ) -> None:
        """Phase 1: Intelligence Gathering."""
        session.phases_completed.append("intel")
        # TODO: Implement full phase in Phase 2
        session.artifacts["intel"] = {"status": "stub", "context_files": context_files}

    async def _phase_assessment(self, session: WarRoomSession) -> None:
        """Phase 2: Situation Assessment."""
        session.phases_completed.append("assessment")
        # TODO: Implement full phase in Phase 2
        session.artifacts["assessment"] = {"status": "stub"}

    async def _phase_coa_development(self, session: WarRoomSession) -> None:
        """Phase 3: COA Development."""
        session.phases_completed.append("coa")
        # TODO: Implement full phase in Phase 2
        session.artifacts["coa"] = {"status": "stub"}

    async def _should_escalate(self, _session: WarRoomSession) -> bool:
        """Check if Supreme Commander should escalate to full council."""
        # TODO: Implement escalation logic in Phase 4
        _ = _session  # Will be used in implementation
        return False

    async def _escalate(
        self, session: WarRoomSession, _context_files: list[str] | None
    ) -> None:
        """Escalate to full council."""
        _ = _context_files  # Will be used in implementation
        session.escalation_reason = "Manual escalation or complexity threshold"
        # TODO: Invoke additional experts

    async def _phase_red_team(self, session: WarRoomSession) -> None:
        """Phase 4: Red Team Challenge."""
        session.phases_completed.append("red_team")
        # TODO: Implement full phase in Phase 2
        session.artifacts["red_team"] = {"status": "stub"}

    async def _phase_voting(self, session: WarRoomSession) -> None:
        """Phase 5: Voting and Narrowing."""
        session.phases_completed.append("voting")
        # TODO: Implement full phase in Phase 2
        session.artifacts["voting"] = {"status": "stub"}

    async def _phase_premortem(self, session: WarRoomSession) -> None:
        """Phase 6: Premortem Analysis."""
        session.phases_completed.append("premortem")
        # TODO: Implement full phase in Phase 2
        session.artifacts["premortem"] = {"status": "stub"}

    async def _phase_synthesis(self, session: WarRoomSession) -> None:
        """Phase 7: Supreme Commander Synthesis."""
        session.phases_completed.append("synthesis")
        # TODO: Implement full phase in Phase 2
        session.artifacts["synthesis"] = {"status": "stub"}

    # ---------------------------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------------------------

    def _persist_session(self, session: WarRoomSession) -> None:
        """Save session to Strategeion."""
        session_dir = self.strategeion / "war-table" / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save main session file
        session_data = {
            "session_id": session.session_id,
            "problem_statement": session.problem_statement,
            "mode": session.mode,
            "status": session.status,
            "escalated": session.escalated,
            "escalation_reason": session.escalation_reason,
            "phases_completed": session.phases_completed,
            "artifacts": session.artifacts,
            "metrics": session.metrics,
            "merkle_dag": session.merkle_dag.to_dict(),
        }

        with open(session_dir / "session.json", "w") as f:
            json.dump(session_data, f, indent=2)

    def load_session(self, session_id: str) -> WarRoomSession | None:
        """Load session from Strategeion."""
        session_file = self.strategeion / "war-table" / session_id / "session.json"
        if not session_file.exists():
            return None

        with open(session_file) as f:
            data = json.load(f)

        # Reconstruct session
        session = WarRoomSession(
            session_id=data["session_id"],
            problem_statement=data["problem_statement"],
            mode=data["mode"],
            status=data["status"],
            escalated=data.get("escalated", False),
            escalation_reason=data.get("escalation_reason"),
            phases_completed=data["phases_completed"],
            artifacts=data["artifacts"],
            metrics=data["metrics"],
        )
        # TODO: Reconstruct MerkleDAG from data["merkle_dag"]
        return session


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
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
