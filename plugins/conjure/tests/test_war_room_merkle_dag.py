"""Tests for War Room Merkle-DAG anonymization system.

Tests core Merkle-DAG functionality:
- Hash generation and determinism
- Anonymized view hiding attribution
- Unsealing to reveal attribution
- Phase-specific labeling
"""

from __future__ import annotations

from scripts.war_room_orchestrator import MerkleDAG


class TestMerkleDAG:
    """Test Merkle-DAG anonymization system."""

    def test_add_contribution_generates_hash(self) -> None:
        """Adding a contribution generates deterministic hashes."""
        dag = MerkleDAG(session_id="test-session")
        node = dag.add_contribution(
            content="Test COA content",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )

        assert node.content_hash is not None
        assert len(node.content_hash) == 64  # SHA256 hex
        assert node.anonymous_label == "Response A"
        assert node.expert_role == "Chief Strategist"

    def test_anonymized_view_hides_attribution(self) -> None:
        """Anonymized view does not reveal expert identity."""
        dag = MerkleDAG(session_id="test-session")
        dag.add_contribution(
            content="COA 1",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )
        dag.add_contribution(
            content="COA 2",
            phase="coa",
            round_number=1,
            expert_role="Field Tactician",
            expert_model="glm-4.7",
        )

        anon_view = dag.get_anonymized_view(phase="coa")

        assert len(anon_view) == 2
        assert anon_view[0]["label"] == "Response A"
        assert anon_view[1]["label"] == "Response B"
        # Attribution NOT in anonymized view
        assert "expert_role" not in anon_view[0]
        assert "expert_model" not in anon_view[0]

    def test_unseal_reveals_attribution(self) -> None:
        """Unsealing reveals full expert attribution."""
        dag = MerkleDAG(session_id="test-session")
        dag.add_contribution(
            content="COA content",
            phase="coa",
            round_number=1,
            expert_role="Chief Strategist",
            expert_model="claude-sonnet-4",
        )

        assert dag.sealed is True
        unsealed = dag.unseal()
        assert dag.sealed is False

        assert len(unsealed) == 1
        assert unsealed[0]["expert_role"] == "Chief Strategist"
        assert unsealed[0]["expert_model"] == "claude-sonnet-4"

    def test_to_dict_respects_seal_state(self) -> None:
        """Serialization masks attribution when sealed."""
        dag = MerkleDAG(session_id="test-session")
        dag.add_contribution(
            content="Test",
            phase="coa",
            round_number=1,
            expert_role="Tactician",
            expert_model="glm-4.7",
        )

        # Sealed - should mask
        sealed_dict = dag.to_dict()
        node_data = list(sealed_dict["nodes"].values())[0]
        assert node_data["expert_role"] == "[SEALED]"

        # Unseal and check again
        dag.unseal()
        unsealed_dict = dag.to_dict()
        node_data = list(unsealed_dict["nodes"].values())[0]
        assert node_data["expert_role"] == "Tactician"


class TestMerkleDAGEdgeCases:
    """Test MerkleDAG edge cases and additional scenarios."""

    def test_empty_dag_root_hash(self) -> None:
        """Empty DAG has no root hash."""
        dag = MerkleDAG(session_id="empty-test")
        assert dag.root_hash is None
        assert len(dag.nodes) == 0

    def test_multiple_phases_generate_distinct_labels(self) -> None:
        """Different phases have independent label counters."""
        dag = MerkleDAG(session_id="multi-phase")

        # Add COA contributions
        dag.add_contribution(
            content="COA 1",
            phase="coa",
            round_number=1,
            expert_role="Strategist",
            expert_model="model-a",
        )
        dag.add_contribution(
            content="COA 2",
            phase="coa",
            round_number=1,
            expert_role="Tactician",
            expert_model="model-b",
        )

        # Add voting contributions
        dag.add_contribution(
            content="Vote 1",
            phase="voting",
            round_number=2,
            expert_role="Strategist",
            expert_model="model-a",
        )

        anon_coa = dag.get_anonymized_view(phase="coa")
        anon_voting = dag.get_anonymized_view(phase="voting")

        assert len(anon_coa) == 2
        assert len(anon_voting) == 1
        assert anon_coa[0]["label"] == "Response A"
        assert anon_coa[1]["label"] == "Response B"
        assert anon_voting[0]["label"] == "Expert 1"

    def test_get_anonymized_view_all_phases(self) -> None:
        """Anonymized view without phase filter returns all contributions."""
        dag = MerkleDAG(session_id="all-phases")

        dag.add_contribution(
            content="Intel",
            phase="intel",
            round_number=1,
            expert_role="Scout",
            expert_model="model-a",
        )
        dag.add_contribution(
            content="COA",
            phase="coa",
            round_number=2,
            expert_role="Strategist",
            expert_model="model-b",
        )

        all_anon = dag.get_anonymized_view()
        assert len(all_anon) == 2

    def test_content_hash_deterministic(self) -> None:
        """Same content produces same hash."""
        dag1 = MerkleDAG(session_id="hash-test-1")
        dag2 = MerkleDAG(session_id="hash-test-2")

        node1 = dag1.add_contribution(
            content="Same content",
            phase="coa",
            round_number=1,
            expert_role="Role",
            expert_model="Model",
        )
        node2 = dag2.add_contribution(
            content="Same content",
            phase="coa",
            round_number=1,
            expert_role="Role",
            expert_model="Model",
        )

        assert node1.content_hash == node2.content_hash
