"""Tests for ERC-8004 configuration loading.

Feature: ERC-8004 Configuration

As a plugin developer
I want to configure chain connections via environment variables
So that I can connect to the ERC-8004 registries without hardcoding secrets
"""

from __future__ import annotations

import pytest

from leyline.erc8004.config import ERC8004Config

# Expected defaults
BASE_SEPOLIA_CHAIN_ID = 84532
BASE_MAINNET_CHAIN_ID = 8453
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
IDENTITY_ADDR = "0x1111111111111111111111111111111111111111"
REPUTATION_ADDR = "0x2222222222222222222222222222222222222222"


@pytest.mark.unit
class TestERC8004ConfigDefaults:
    """Feature: ERC-8004 config provides sensible defaults."""

    @pytest.mark.bdd
    def test_default_config_targets_base_sepolia(self) -> None:
        """Scenario: Default config uses Base Sepolia testnet.

        Given no configuration is provided
        When creating a default ERC8004Config
        Then the RPC URL should point to Base Sepolia
        And the chain ID should be 84532.
        """
        config = ERC8004Config()

        assert config.rpc_url == "https://sepolia.base.org"
        assert config.chain_id == BASE_SEPOLIA_CHAIN_ID

    @pytest.mark.bdd
    def test_default_config_has_no_private_key(self) -> None:
        """Scenario: Default config is read-only.

        Given no configuration is provided
        When creating a default ERC8004Config
        Then the private key should be empty
        And is_read_only should be True.
        """
        config = ERC8004Config()

        assert config.private_key == ""
        assert config.is_read_only is True

    @pytest.mark.bdd
    def test_default_config_uses_zero_address_for_registries(self) -> None:
        """Scenario: Default registry addresses are zero-address placeholders.

        Given no configuration is provided
        When creating a default ERC8004Config
        Then both registry addresses should be the zero address.
        """
        config = ERC8004Config()

        assert config.identity_registry == ZERO_ADDRESS
        assert config.reputation_registry == ZERO_ADDRESS


@pytest.mark.unit
class TestERC8004ConfigFromEnv:
    """Feature: ERC-8004 config loads from environment variables."""

    @pytest.mark.bdd
    def test_from_env_reads_all_variables(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: All environment variables are read.

        Given ERC8004_* environment variables are set
        When creating config via from_env()
        Then all values should be populated from the environment.
        """
        monkeypatch.setenv("ERC8004_RPC_URL", "https://custom-rpc.example.com")
        monkeypatch.setenv("ERC8004_PRIVATE_KEY", "0xdeadbeef")
        monkeypatch.setenv("ERC8004_IDENTITY_REGISTRY", IDENTITY_ADDR)
        monkeypatch.setenv("ERC8004_REPUTATION_REGISTRY", REPUTATION_ADDR)
        monkeypatch.setenv("ERC8004_CHAIN_ID", "8453")

        config = ERC8004Config.from_env()

        assert config.rpc_url == "https://custom-rpc.example.com"
        assert config.private_key == "0xdeadbeef"
        assert config.identity_registry == IDENTITY_ADDR
        assert config.reputation_registry == REPUTATION_ADDR
        assert config.chain_id == BASE_MAINNET_CHAIN_ID

    @pytest.mark.bdd
    def test_from_env_uses_defaults_when_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Missing environment variables fall back to defaults.

        Given no ERC8004_* environment variables are set
        When creating config via from_env()
        Then defaults should be used.
        """
        env_vars = (
            "ERC8004_RPC_URL",
            "ERC8004_PRIVATE_KEY",
            "ERC8004_IDENTITY_REGISTRY",
            "ERC8004_REPUTATION_REGISTRY",
            "ERC8004_CHAIN_ID",
        )
        for var in env_vars:
            monkeypatch.delenv(var, raising=False)

        config = ERC8004Config.from_env()

        assert config.rpc_url == "https://sepolia.base.org"
        assert config.private_key == ""
        assert config.chain_id == BASE_SEPOLIA_CHAIN_ID


@pytest.mark.unit
class TestERC8004ConfigReadOnly:
    """Feature: ERC-8004 config distinguishes read-only from write mode."""

    @pytest.mark.bdd
    def test_config_with_private_key_is_not_read_only(self) -> None:
        """Scenario: Config with private key enables write operations.

        Given a config with a private key set
        When checking is_read_only
        Then it should return False.
        """
        config = ERC8004Config(private_key="0xsomekey")

        assert config.is_read_only is False

    @pytest.mark.bdd
    def test_config_without_private_key_is_read_only(self) -> None:
        """Scenario: Config without private key is read-only.

        Given a config with no private key
        When checking is_read_only
        Then it should return True.
        """
        config = ERC8004Config(private_key="")

        assert config.is_read_only is True
