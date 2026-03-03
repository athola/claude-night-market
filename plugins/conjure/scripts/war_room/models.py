"""Data structures for War Room deliberation sessions.

Contains DeliberationNode, MerkleDAG, WarRoomSession, and ExpertConfig.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Any


@dataclass
class ExpertInfo:
    """Identity of the expert providing a contribution."""

    role: str
    model: str


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

    def add_contribution(
        self,
        content: str,
        phase: str,
        round_number: int,
        expert: ExpertInfo,
        parent_id: str | None = None,
    ) -> DeliberationNode:
        """Add a contribution and compute hashes."""
        content_hash = sha256(content.encode()).hexdigest()
        metadata_hash = sha256(f"{expert.role}:{expert.model}".encode()).hexdigest()
        combined_hash = sha256(f"{content_hash}:{metadata_hash}".encode()).hexdigest()

        label = self._generate_label(phase)

        node = DeliberationNode(
            node_id=combined_hash[:16],
            parent_id=parent_id,
            round_number=round_number,
            phase=phase,
            anonymous_label=label,
            content=content,
            expert_role=expert.role,
            expert_model=expert.model,
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
