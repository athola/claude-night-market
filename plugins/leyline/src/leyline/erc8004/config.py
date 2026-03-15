"""Configuration for ERC-8004 chain connection.

Environment-driven configuration for connecting to the ERC-8004
Identity and Reputation registries on Base L2.

Environment variables:
    ERC8004_RPC_URL: Base Sepolia RPC endpoint
    ERC8004_PRIVATE_KEY: Wallet private key (for publishing)
    ERC8004_IDENTITY_REGISTRY: Identity registry contract address
    ERC8004_REPUTATION_REGISTRY: Reputation registry contract address
    ERC8004_CHAIN_ID: Chain ID (84532 for Base Sepolia)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Base Sepolia defaults
DEFAULT_RPC_URL = "https://sepolia.base.org"
DEFAULT_CHAIN_ID = 84532

# Zero-address placeholders for undeployed contracts
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@dataclass
class ERC8004Config:
    """Configuration for ERC-8004 registry connections.

    Attributes:
        rpc_url: RPC endpoint for the target chain.
        private_key: Wallet private key for signing transactions.
            Empty string means read-only mode (queries only).
        identity_registry: Contract address for the Identity Registry.
        reputation_registry: Contract address for the Reputation Registry.
        chain_id: Target chain ID.

    """

    rpc_url: str = DEFAULT_RPC_URL
    private_key: str = ""
    identity_registry: str = ZERO_ADDRESS
    reputation_registry: str = ZERO_ADDRESS
    chain_id: int = DEFAULT_CHAIN_ID

    @classmethod
    def from_env(cls) -> ERC8004Config:
        """Create configuration from environment variables.

        Returns:
            ERC8004Config populated from environment, with defaults
            for Base Sepolia testnet.

        """
        return cls(
            rpc_url=os.environ.get("ERC8004_RPC_URL", DEFAULT_RPC_URL),
            private_key=os.environ.get("ERC8004_PRIVATE_KEY", ""),
            identity_registry=os.environ.get("ERC8004_IDENTITY_REGISTRY", ZERO_ADDRESS),
            reputation_registry=os.environ.get(
                "ERC8004_REPUTATION_REGISTRY", ZERO_ADDRESS
            ),
            chain_id=int(os.environ.get("ERC8004_CHAIN_ID", str(DEFAULT_CHAIN_ID))),
        )

    @property
    def is_read_only(self) -> bool:
        """Check if config supports write operations.

        Returns:
            True if no private key is configured.

        """
        return not self.private_key
