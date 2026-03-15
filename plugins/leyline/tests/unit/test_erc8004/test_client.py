"""Tests for ERC-8004 unified client.

Feature: Unified ERC-8004 client

As a developer
I want a single entry point for ERC-8004 operations
So that I don't need to configure Identity and Reputation separately
"""

from __future__ import annotations

import pytest

from leyline.erc8004.client import ERC8004Client
from leyline.erc8004.config import ERC8004Config
from leyline.erc8004.identity import IdentityRegistry
from leyline.erc8004.reputation import ReputationRegistry

# Expected chain IDs
BASE_SEPOLIA_CHAIN_ID = 84532
BASE_MAINNET_CHAIN_ID = 8453

# Env vars to clear for clean tests
ERC8004_ENV_VARS = (
    "ERC8004_RPC_URL",
    "ERC8004_PRIVATE_KEY",
    "ERC8004_IDENTITY_REGISTRY",
    "ERC8004_REPUTATION_REGISTRY",
    "ERC8004_CHAIN_ID",
)


@pytest.mark.unit
class TestERC8004Client:
    """Feature: Unified client combining Identity and Reputation registries."""

    @pytest.mark.bdd
    def test_client_initializes_both_registries(self) -> None:
        """Scenario: Client creates both registry wrappers.

        Given a valid ERC8004Config
        When creating an ERC8004Client
        Then it should have identity and reputation attributes
        And both should be properly configured.
        """
        config = ERC8004Config(
            rpc_url="https://test.example.com",
            chain_id=BASE_SEPOLIA_CHAIN_ID,
        )

        client = ERC8004Client(config)

        assert isinstance(client.identity, IdentityRegistry)
        assert isinstance(client.reputation, ReputationRegistry)
        assert client.config is config

    @pytest.mark.bdd
    def test_client_from_env_reads_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Client created from environment variables.

        Given ERC8004_* environment variables are set
        When creating a client via from_env()
        Then it should configure from the environment.
        """
        monkeypatch.setenv("ERC8004_RPC_URL", "https://env-rpc.example.com")
        monkeypatch.setenv("ERC8004_CHAIN_ID", "8453")
        monkeypatch.delenv("ERC8004_PRIVATE_KEY", raising=False)

        client = ERC8004Client.from_env()

        assert client.config.rpc_url == "https://env-rpc.example.com"
        assert client.config.chain_id == BASE_MAINNET_CHAIN_ID
        assert client.config.is_read_only is True

    @pytest.mark.bdd
    def test_client_from_env_uses_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Client from_env uses defaults when env vars absent.

        Given no ERC8004_* environment variables are set
        When creating a client via from_env()
        Then it should use Base Sepolia defaults.
        """
        for var in ERC8004_ENV_VARS:
            monkeypatch.delenv(var, raising=False)

        client = ERC8004Client.from_env()

        assert client.config.rpc_url == "https://sepolia.base.org"
        assert client.config.chain_id == BASE_SEPOLIA_CHAIN_ID
