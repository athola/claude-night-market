"""Unified ERC-8004 client combining Identity and Reputation registries.

Provides a single entry point for all ERC-8004 operations.

Usage:
    client = ERC8004Client.from_env()
    client.identity.register_plugin("my-plugin", "ipfs://metadata")
    client.reputation.publish_assertions(token_id, commit, results)
"""

from __future__ import annotations

from leyline.erc8004.config import ERC8004Config
from leyline.erc8004.identity import IdentityRegistry
from leyline.erc8004.reputation import ReputationRegistry


class ERC8004Client:
    """Unified client for ERC-8004 Identity and Reputation operations.

    Combines both registries under a single configuration, providing
    a convenient entry point for plugin verification workflows.

    Args:
        config: ERC-8004 connection configuration.

    Attributes:
        identity: IdentityRegistry for plugin/skill registration.
        reputation: ReputationRegistry for assertion publishing.

    """

    def __init__(self, config: ERC8004Config) -> None:
        self.config = config
        self.identity = IdentityRegistry(config)
        self.reputation = ReputationRegistry(config)

    @classmethod
    def from_env(cls) -> ERC8004Client:
        """Create client from environment variables.

        Reads ERC8004_* environment variables to configure the
        connection. See ERC8004Config.from_env() for details.

        Returns:
            Configured ERC8004Client instance.

        """
        return cls(ERC8004Config.from_env())
