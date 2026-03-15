"""Tests for ERC-8004 Reputation Registry wrapper.

Feature: On-chain assertion publishing and trust scoring

As a plugin ecosystem
I want to publish assertion results and compute trust scores
So that consumers can verify plugin quality before installation
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from leyline.erc8004.config import ERC8004Config
from leyline.erc8004.reputation import (
    AssertionRecord,
    AssertionResult,
    ReputationRegistry,
    TrustScore,
    _calculate_pass_rate,
    _deserialize_assertions,
    _require_web3,
    _serialize_assertions,
)

# Test constants
EXPECTED_BATCH_SIZE = 2
EXPECTED_ASSERTION_COUNT = 7
EXPECTED_VERSIONS = 2
EXPECTED_PUBLISH_TOKEN_ID = 42
RATE_TOLERANCE = 0.01
IDENTITY_ADDR = "0x1111111111111111111111111111111111111111"
REPUTATION_ADDR = "0x2222222222222222222222222222222222222222"
SAMPLE_TIMESTAMP = 1700000000


def _make_config(*, read_only: bool = False) -> ERC8004Config:
    """Create an ERC8004Config for testing."""
    return ERC8004Config(
        rpc_url="https://test-rpc.example.com",
        private_key="" if read_only else "0xfakekey",
        identity_registry=IDENTITY_ADDR,
        reputation_registry=REPUTATION_ADDR,
        chain_id=84532,
    )


@pytest.mark.unit
class TestAssertionDataclasses:
    """Feature: Assertion data structures for test results."""

    @pytest.mark.bdd
    def test_assertion_result_holds_test_outcome(self) -> None:
        """Scenario: Creating an assertion result.

        Given test outcome data
        When constructing an AssertionResult
        Then all fields should be accessible.
        """
        result = AssertionResult(
            test_name="test_readme_exists",
            level="L1",
            status="pass",
            timestamp=SAMPLE_TIMESTAMP,
        )

        assert result.test_name == "test_readme_exists"
        assert result.level == "L1"
        assert result.status == "pass"
        assert result.timestamp == SAMPLE_TIMESTAMP

    @pytest.mark.bdd
    def test_assertion_record_holds_batch(self) -> None:
        """Scenario: Creating an assertion record for a commit.

        Given a batch of assertion results
        When constructing an AssertionRecord
        Then it should store the commit hash and results.
        """
        results = [
            AssertionResult("test_a", "L1", "pass", SAMPLE_TIMESTAMP),
            AssertionResult("test_b", "L2", "fail", SAMPLE_TIMESTAMP + 1),
        ]
        record = AssertionRecord(
            commit_hash="abc1234",
            assertions=results,
            published_at=SAMPLE_TIMESTAMP + 10,
            tx_hash="0xtxhash",
        )

        assert record.commit_hash == "abc1234"
        assert len(record.assertions) == EXPECTED_BATCH_SIZE
        assert record.tx_hash == "0xtxhash"

    @pytest.mark.bdd
    def test_trust_score_defaults_to_zero(self) -> None:
        """Scenario: Default trust score has zero values.

        Given no assertion history
        When creating a default TrustScore
        Then all rates should be 0.0 and counts should be 0.
        """
        score = TrustScore()

        assert score.l1_pass_rate == 0.0
        assert score.l2_pass_rate == 0.0
        assert score.l3_pass_rate == 0.0
        assert score.total_assertions == 0
        assert score.versions_verified == 0


@pytest.mark.unit
class TestReputationRegistryPublish:
    """Feature: Publish assertion results on-chain."""

    @pytest.mark.bdd
    def test_publish_assertions_sends_transaction(self) -> None:
        """Scenario: Publishing assertions sends a blockchain tx.

        Given a configured ReputationRegistry with a private key
        When publishing a batch of assertion results
        Then it should serialize, sign, and send a transaction
        And return the transaction hash.
        """
        config = _make_config()
        registry = ReputationRegistry(config)

        mock_web3 = MagicMock(name="Web3")
        mock_contract = MagicMock(name="contract")
        mock_fn = MagicMock(name="publishAssertions_fn")
        mock_contract.functions.publishAssertions.return_value = mock_fn

        mock_account = MagicMock(name="account")
        mock_account.address = "0xTestAddress"
        mock_web3.eth.account.from_key.return_value = mock_account
        mock_web3.eth.get_transaction_count.return_value = 0

        mock_receipt = MagicMock(name="receipt")
        mock_receipt.transactionHash.hex.return_value = "0xpublish_tx"
        mock_web3.eth.wait_for_transaction_receipt.return_value = mock_receipt

        registry._web3 = mock_web3
        registry._contract = mock_contract

        assertions = [
            AssertionResult("test_a", "L1", "pass", SAMPLE_TIMESTAMP),
            AssertionResult("test_b", "L2", "fail", SAMPLE_TIMESTAMP + 1),
        ]

        tx_hash = registry.publish_assertions("42", "abc1234", assertions)

        assert tx_hash == "0xpublish_tx"
        call_args = mock_contract.functions.publishAssertions.call_args
        assert call_args[0][0] == EXPECTED_PUBLISH_TOKEN_ID
        assert call_args[0][1] == "abc1234"
        deserialized = json.loads(call_args[0][2])
        assert len(deserialized) == EXPECTED_BATCH_SIZE
        assert deserialized[0]["test_name"] == "test_a"

    @pytest.mark.bdd
    def test_publish_assertions_raises_in_read_only_mode(self) -> None:
        """Scenario: Publishing fails without a private key.

        Given a read-only ReputationRegistry (no private key)
        When attempting to publish assertions
        Then it should raise a PermissionError.
        """
        config = _make_config(read_only=True)
        registry = ReputationRegistry(config)

        assertions = [AssertionResult("test_a", "L1", "pass", SAMPLE_TIMESTAMP)]

        with pytest.raises(PermissionError, match="read-only"):
            registry.publish_assertions("42", "abc1234", assertions)


@pytest.mark.unit
class TestReputationRegistryQuery:
    """Feature: Query assertion history and trust scores."""

    @pytest.mark.bdd
    def test_get_assertion_history_returns_records(self) -> None:
        """Scenario: Querying assertion history for a plugin.

        Given a plugin has published assertions
        When querying assertion history
        Then it should return deserialized AssertionRecord objects.
        """
        config = _make_config(read_only=True)
        registry = ReputationRegistry(config)

        serialized = json.dumps(
            [
                {
                    "test_name": "test_a",
                    "level": "L1",
                    "status": "pass",
                    "timestamp": SAMPLE_TIMESTAMP,
                },
            ]
        )
        mock_contract = MagicMock(name="contract")
        published_at = SAMPLE_TIMESTAMP + 10
        call_rv = [("abc1234", serialized, published_at)]
        hist_fn = mock_contract.functions.getAssertionHistory
        hist_fn.return_value.call.return_value = call_rv

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        records = registry.get_assertion_history("42", limit=5)

        assert len(records) == 1
        assert records[0].commit_hash == "abc1234"
        assert len(records[0].assertions) == 1
        assert records[0].assertions[0].test_name == "test_a"
        assert records[0].published_at == published_at

    @pytest.mark.bdd
    def test_get_assertion_history_returns_empty_on_error(
        self,
    ) -> None:
        """Scenario: History query fails gracefully.

        Given the contract call raises an exception
        When querying history
        Then it should return an empty list.
        """
        config = _make_config(read_only=True)
        registry = ReputationRegistry(config)

        mock_contract = MagicMock(name="contract")
        call_mock = mock_contract.functions.getAssertionHistory.return_value.call
        call_mock.side_effect = Exception("RPC error")

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        records = registry.get_assertion_history("42")

        assert records == []

    @pytest.mark.bdd
    def test_get_trust_score_calculates_pass_rates(self) -> None:
        """Scenario: Trust score computed from assertion history.

        Given a plugin has L1, L2, and L3 assertion results
        When computing the trust score
        Then pass rates should reflect the assertion outcomes.
        """
        config = _make_config(read_only=True)
        registry = ReputationRegistry(config)

        batch1 = json.dumps(
            [
                {"test_name": "t1", "level": "L1", "status": "pass", "timestamp": 100},
                {"test_name": "t2", "level": "L1", "status": "pass", "timestamp": 100},
                {"test_name": "t3", "level": "L2", "status": "fail", "timestamp": 100},
                {"test_name": "t4", "level": "L3", "status": "pass", "timestamp": 100},
            ]
        )
        batch2 = json.dumps(
            [
                {"test_name": "t1", "level": "L1", "status": "fail", "timestamp": 200},
                {"test_name": "t3", "level": "L2", "status": "pass", "timestamp": 200},
                {"test_name": "t4", "level": "L3", "status": "pass", "timestamp": 200},
            ]
        )

        mock_contract = MagicMock(name="contract")
        call_rv = [
            ("commit1", batch1, 1000),
            ("commit2", batch2, 2000),
        ]
        hist_fn = mock_contract.functions.getAssertionHistory
        hist_fn.return_value.call.return_value = call_rv

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        score = registry.get_trust_score("42")

        # L1: 2 pass + 1 fail = 2/3
        assert abs(score.l1_pass_rate - 2.0 / 3.0) < RATE_TOLERANCE
        # L2: 1 fail + 1 pass = 1/2
        assert abs(score.l2_pass_rate - 0.5) < RATE_TOLERANCE
        # L3: 2 pass = 2/2
        assert score.l3_pass_rate == 1.0
        assert score.total_assertions == EXPECTED_ASSERTION_COUNT
        assert score.versions_verified == EXPECTED_VERSIONS

    @pytest.mark.bdd
    def test_get_trust_score_returns_zero_with_no_history(
        self,
    ) -> None:
        """Scenario: Trust score is zero when no history exists.

        Given a plugin has no assertion history
        When computing the trust score
        Then all rates should be 0.0.
        """
        config = _make_config(read_only=True)
        registry = ReputationRegistry(config)

        mock_contract = MagicMock(name="contract")
        call_rv: list[tuple[str, str, int]] = []
        hist_fn = mock_contract.functions.getAssertionHistory
        hist_fn.return_value.call.return_value = call_rv

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        score = registry.get_trust_score("42")

        assert score.l1_pass_rate == 0.0
        assert score.total_assertions == 0
        assert score.versions_verified == 0


@pytest.mark.unit
class TestReputationSerialization:
    """Feature: Assertion serialization and deserialization."""

    @pytest.mark.bdd
    def test_serialize_deserialize_roundtrip(self) -> None:
        """Scenario: Assertions survive JSON serialization roundtrip.

        Given a list of assertion results
        When serializing and then deserializing
        Then the original data should be preserved.
        """
        original = [
            AssertionResult("test_a", "L1", "pass", SAMPLE_TIMESTAMP),
            AssertionResult("test_b", "L2", "fail", SAMPLE_TIMESTAMP + 1),
        ]

        serialized = _serialize_assertions(original)
        restored = _deserialize_assertions(serialized)

        assert len(restored) == EXPECTED_BATCH_SIZE
        assert restored[0].test_name == "test_a"
        assert restored[1].status == "fail"

    @pytest.mark.bdd
    def test_deserialize_handles_invalid_json(self) -> None:
        """Scenario: Deserialization handles corrupt data gracefully.

        Given invalid JSON data
        When deserializing
        Then it should return an empty list.
        """
        result = _deserialize_assertions("not valid json {{{")

        assert result == []

    @pytest.mark.bdd
    def test_calculate_pass_rate_for_level(self) -> None:
        """Scenario: Pass rate calculation filters by level.

        Given mixed L1 and L2 assertions
        When calculating pass rate for L1
        Then only L1 assertions should be considered.
        """
        assertions = [
            AssertionResult("t1", "L1", "pass", 100),
            AssertionResult("t2", "L1", "fail", 100),
            AssertionResult("t3", "L2", "pass", 100),
        ]

        l1_rate = _calculate_pass_rate(assertions, "L1")
        l2_rate = _calculate_pass_rate(assertions, "L2")
        l3_rate = _calculate_pass_rate(assertions, "L3")

        expected_l1_rate = 0.5
        assert l1_rate == expected_l1_rate
        assert l2_rate == 1.0
        assert l3_rate == 0.0  # No L3 assertions

    @pytest.mark.bdd
    def test_web3_import_error_raises_clear_message(self) -> None:
        """Scenario: Missing web3 package gives a helpful error.

        Given web3 is not installed
        When attempting to use the registry
        Then it should raise ImportError with install instructions.
        """
        with patch.dict("sys.modules", {"web3": None}):
            with pytest.raises(ImportError, match="pip install web3"):
                _require_web3()
