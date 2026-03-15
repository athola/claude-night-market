"""Tests for ERC-8004 Identity Registry wrapper.

Feature: On-chain plugin/skill identity registration

As a plugin maintainer
I want to register plugin identities on-chain
So that consumers can verify plugin provenance and trust
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from leyline.erc8004.config import ERC8004Config
from leyline.erc8004.identity import IdentityRegistry, _require_web3

# Test constants
EXPECTED_SKILL_COUNT = 2
IDENTITY_ADDR = "0x1111111111111111111111111111111111111111"
REPUTATION_ADDR = "0x2222222222222222222222222222222222222222"


def _make_config(*, read_only: bool = False) -> ERC8004Config:
    """Create an ERC8004Config for testing."""
    return ERC8004Config(
        rpc_url="https://test-rpc.example.com",
        private_key="" if read_only else "0xfakekey",
        identity_registry=IDENTITY_ADDR,
        reputation_registry=REPUTATION_ADDR,
        chain_id=84532,
    )


def _make_web3_mocks(
    tx_hash: str = "0xabcdef1234567890",
) -> tuple[MagicMock, MagicMock]:
    """Create mock web3 and receipt objects for transaction tests."""
    mock_web3 = MagicMock(name="Web3")
    mock_account = MagicMock(name="account")
    mock_account.address = "0xTestAddress"
    mock_web3.eth.account.from_key.return_value = mock_account
    mock_web3.eth.get_transaction_count.return_value = 0

    mock_receipt = MagicMock(name="receipt")
    mock_receipt.transactionHash.hex.return_value = tx_hash
    mock_web3.eth.wait_for_transaction_receipt.return_value = mock_receipt

    return mock_web3, mock_receipt


@pytest.mark.unit
class TestIdentityRegistryRegistration:
    """Feature: Register plugins and skills as on-chain identities."""

    @pytest.mark.bdd
    def test_register_plugin_sends_transaction(self) -> None:
        """Scenario: Registering a plugin sends a blockchain transaction.

        Given a configured IdentityRegistry with a private key
        When registering a plugin with name and metadata URI
        Then it should build, sign, and send a transaction
        And return the transaction hash.
        """
        config = _make_config()
        registry = IdentityRegistry(config)

        mock_web3, _ = _make_web3_mocks("0xabcdef1234567890")
        mock_contract = MagicMock(name="contract")
        mock_fn = MagicMock(name="registerIdentity_fn")
        mock_contract.functions.registerIdentity.return_value = mock_fn

        registry._web3 = mock_web3
        registry._contract = mock_contract

        tx_hash = registry.register_plugin("my-plugin", "ipfs://metadata")

        assert tx_hash == "0xabcdef1234567890"
        mock_contract.functions.registerIdentity.assert_called_once_with(
            "my-plugin", "ipfs://metadata"
        )

    @pytest.mark.bdd
    def test_register_plugin_raises_in_read_only_mode(self) -> None:
        """Scenario: Registering a plugin fails without a private key.

        Given a read-only IdentityRegistry (no private key)
        When attempting to register a plugin
        Then it should raise a PermissionError.
        """
        config = _make_config(read_only=True)
        registry = IdentityRegistry(config)

        mock_contract = MagicMock(name="contract")
        mock_fn = MagicMock(name="registerIdentity_fn")
        mock_contract.functions.registerIdentity.return_value = mock_fn
        registry._contract = mock_contract
        registry._web3 = MagicMock(name="Web3")

        with pytest.raises(PermissionError, match="read-only"):
            registry.register_plugin("my-plugin", "ipfs://metadata")

    @pytest.mark.bdd
    def test_register_skill_under_plugin(self) -> None:
        """Scenario: Registering a skill under a parent plugin.

        Given a configured IdentityRegistry
        When registering a skill with a parent plugin token ID
        Then it should call registerSubIdentity with the correct args.
        """
        config = _make_config()
        registry = IdentityRegistry(config)

        mock_web3, _ = _make_web3_mocks("0xskill_tx_hash")
        mock_contract = MagicMock(name="contract")
        mock_fn = MagicMock(name="registerSubIdentity_fn")
        mock_contract.functions.registerSubIdentity.return_value = mock_fn

        registry._web3 = mock_web3
        registry._contract = mock_contract

        tx_hash = registry.register_skill("42", "do-issue", "ipfs://skill-meta")

        assert tx_hash == "0xskill_tx_hash"
        expected_parent_id = 42
        mock_contract.functions.registerSubIdentity.assert_called_once_with(
            expected_parent_id, "do-issue", "ipfs://skill-meta"
        )


@pytest.mark.unit
class TestIdentityRegistryQueries:
    """Feature: Query plugin and skill identities."""

    @pytest.mark.bdd
    def test_get_plugin_identity_returns_dict(self) -> None:
        """Scenario: Querying an existing plugin identity.

        Given a plugin is registered on-chain
        When querying by plugin name
        Then it should return a dict with identity fields.
        """
        config = _make_config(read_only=True)
        registry = IdentityRegistry(config)

        mock_contract = MagicMock(name="contract")
        call_rv = (1, "my-plugin", "ipfs://metadata", "0xOwner")
        get_fn = mock_contract.functions.getIdentityByName
        get_fn.return_value.call.return_value = call_rv

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        result = registry.get_plugin_identity("my-plugin")

        assert result is not None
        assert result["token_id"] == "1"  # noqa: S105
        assert result["name"] == "my-plugin"
        assert result["metadata_uri"] == "ipfs://metadata"
        assert result["owner"] == "0xOwner"

    @pytest.mark.bdd
    def test_get_plugin_identity_returns_none_when_not_found(
        self,
    ) -> None:
        """Scenario: Querying a non-existent plugin identity.

        Given no plugin is registered with the given name
        When querying by name
        Then it should return None.
        """
        config = _make_config(read_only=True)
        registry = IdentityRegistry(config)

        mock_contract = MagicMock(name="contract")
        # Token ID 0 means not found
        call_rv = (0, "", "", "0x" + "0" * 40)
        get_fn = mock_contract.functions.getIdentityByName
        get_fn.return_value.call.return_value = call_rv

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        result = registry.get_plugin_identity("nonexistent")

        assert result is None

    @pytest.mark.bdd
    def test_get_plugin_identity_returns_none_on_exception(
        self,
    ) -> None:
        """Scenario: Contract call fails gracefully.

        Given the contract call raises an exception
        When querying by name
        Then it should return None instead of propagating.
        """
        config = _make_config(read_only=True)
        registry = IdentityRegistry(config)

        mock_contract = MagicMock(name="contract")
        call_mock = mock_contract.functions.getIdentityByName.return_value.call
        call_mock.side_effect = Exception("RPC error")

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        result = registry.get_plugin_identity("broken")

        assert result is None

    @pytest.mark.bdd
    def test_get_skills_for_plugin_returns_list(self) -> None:
        """Scenario: Querying skills registered under a plugin.

        Given a plugin has registered skills
        When querying skills by plugin token ID
        Then it should return a list of skill dicts.
        """
        config = _make_config(read_only=True)
        registry = IdentityRegistry(config)

        mock_contract = MagicMock(name="contract")
        call_rv = [
            (10, "do-issue", "ipfs://skill1"),
            (11, "fix-pr", "ipfs://skill2"),
        ]
        sub_fn = mock_contract.functions.getSubIdentities
        sub_fn.return_value.call.return_value = call_rv

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        skills = registry.get_skills_for_plugin("1")

        assert len(skills) == EXPECTED_SKILL_COUNT
        assert skills[0]["token_id"] == "10"  # noqa: S105
        assert skills[0]["name"] == "do-issue"
        assert skills[1]["name"] == "fix-pr"

    @pytest.mark.bdd
    def test_get_skills_for_plugin_returns_empty_on_error(
        self,
    ) -> None:
        """Scenario: Skills query fails gracefully.

        Given the contract call raises an exception
        When querying skills
        Then it should return an empty list.
        """
        config = _make_config(read_only=True)
        registry = IdentityRegistry(config)

        mock_contract = MagicMock(name="contract")
        call_mock = mock_contract.functions.getSubIdentities.return_value.call
        call_mock.side_effect = Exception("RPC error")

        registry._web3 = MagicMock(name="Web3")
        registry._contract = mock_contract

        skills = registry.get_skills_for_plugin("1")

        assert skills == []


@pytest.mark.unit
class TestIdentityRegistryWeb3Lazy:
    """Feature: Web3 is lazily imported and initialized."""

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
