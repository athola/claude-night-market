"""ERC-8004 SDK wrapper for on-chain behavioral contract verification.

Provides identity registration and assertion publishing for the
night-market plugin ecosystem, targeting Base L2 (Ethereum rollup).

Usage:
    from leyline.erc8004 import ERC8004Client

    client = ERC8004Client.from_env()
    token_id = client.identity.register_plugin("my-plugin", "ipfs://...")
    client.reputation.publish_assertions(token_id, commit_hash, results)

Note:
    Requires web3 for blockchain operations. Install with:
        pip install web3
"""

from __future__ import annotations

from leyline.erc8004.client import ERC8004Client
from leyline.erc8004.config import ERC8004Config
from leyline.erc8004.identity import IdentityRegistry
from leyline.erc8004.reputation import (
    AssertionRecord,
    AssertionResult,
    ReputationRegistry,
    TrustScore,
)

__all__ = [
    "AssertionRecord",
    "AssertionResult",
    "ERC8004Client",
    "ERC8004Config",
    "IdentityRegistry",
    "ReputationRegistry",
    "TrustScore",
]
