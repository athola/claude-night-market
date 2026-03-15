"""ERC-8004 Reputation Registry wrapper.

Publish and query content assertion results on the ERC-8004
Reputation Registry contract.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from leyline.erc8004.config import ERC8004Config

logger = logging.getLogger(__name__)

# Minimal ABI for Reputation Registry interactions
REPUTATION_REGISTRY_ABI: list[dict[str, Any]] = [
    {
        "name": "publishAssertions",
        "type": "function",
        "inputs": [
            {"name": "tokenId", "type": "uint256"},
            {"name": "commitHash", "type": "string"},
            {"name": "data", "type": "string"},
        ],
        "outputs": [],
    },
    {
        "name": "getAssertionHistory",
        "type": "function",
        "inputs": [
            {"name": "tokenId", "type": "uint256"},
            {"name": "limit", "type": "uint256"},
        ],
        "outputs": [
            {
                "name": "records",
                "type": "tuple[]",
                "components": [
                    {"name": "commitHash", "type": "string"},
                    {"name": "data", "type": "string"},
                    {"name": "publishedAt", "type": "uint256"},
                ],
            },
        ],
    },
]


@dataclass
class AssertionResult:
    """A single assertion outcome from a test run.

    Attributes:
        test_name: Fully qualified test name.
        level: Assertion tier ("L1", "L2", or "L3").
        status: Outcome ("pass", "fail", or "skip").
        timestamp: Unix timestamp when the test ran.

    """

    test_name: str
    level: str
    status: str
    timestamp: int


@dataclass
class AssertionRecord:
    """A batch of assertion results published on-chain.

    Attributes:
        commit_hash: Git commit hash the assertions apply to.
        assertions: Individual assertion outcomes in the batch.
        published_at: Unix timestamp of on-chain publication.
        tx_hash: Transaction hash of the publish operation.

    """

    commit_hash: str
    assertions: list[AssertionResult] = field(default_factory=list)
    published_at: int = 0
    tx_hash: str = ""


@dataclass
class TrustScore:
    """Aggregate trust metrics derived from assertion history.

    Attributes:
        l1_pass_rate: Pass rate for L1 (structural) assertions.
        l2_pass_rate: Pass rate for L2 (semantic) assertions.
        l3_pass_rate: Pass rate for L3 (behavioral) assertions.
        total_assertions: Total number of assertions evaluated.
        versions_verified: Number of distinct commits with assertions.

    """

    l1_pass_rate: float = 0.0
    l2_pass_rate: float = 0.0
    l3_pass_rate: float = 0.0
    total_assertions: int = 0
    versions_verified: int = 0


def _require_web3() -> Any:
    """Import web3 or raise a clear error."""
    try:
        from web3 import Web3  # type: ignore[import-not-found]  # noqa: PLC0415

        return Web3
    except ImportError:
        msg = "Install web3 for ERC-8004 support: pip install web3"
        raise ImportError(msg) from None


def _serialize_assertions(assertions: list[AssertionResult]) -> str:
    """Serialize assertion results to JSON for on-chain storage.

    Args:
        assertions: List of assertion results to serialize.

    Returns:
        JSON string representation.

    """
    return json.dumps(
        [
            {
                "test_name": a.test_name,
                "level": a.level,
                "status": a.status,
                "timestamp": a.timestamp,
            }
            for a in assertions
        ],
    )


def _deserialize_assertions(data: str) -> list[AssertionResult]:
    """Deserialize assertion results from on-chain JSON.

    Args:
        data: JSON string from the contract.

    Returns:
        List of AssertionResult objects.

    """
    try:
        items = json.loads(data)
        return [
            AssertionResult(
                test_name=item["test_name"],
                level=item["level"],
                status=item["status"],
                timestamp=item["timestamp"],
            )
            for item in items
        ]
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("Failed to deserialize assertion data: %s", data[:100])
        return []


def _calculate_pass_rate(assertions: list[AssertionResult], level: str) -> float:
    """Calculate pass rate for a specific assertion level.

    Args:
        assertions: All assertions to evaluate.
        level: The tier to filter by ("L1", "L2", "L3").

    Returns:
        Pass rate as a float between 0.0 and 1.0.
        Returns 0.0 if no assertions exist for the level.

    """
    level_assertions = [a for a in assertions if a.level == level]
    if not level_assertions:
        return 0.0
    passed = sum(1 for a in level_assertions if a.status == "pass")
    return passed / len(level_assertions)


class ReputationRegistry:
    """Publish and query assertion results on ERC-8004.

    Each publish operation batches assertion results for a specific
    commit hash and stores them on-chain under the plugin's token ID.

    Args:
        config: ERC-8004 connection configuration.

    """

    def __init__(self, config: ERC8004Config) -> None:
        self._config = config
        self._web3: Any = None
        self._contract: Any = None

    def _get_web3(self) -> Any:
        """Lazily initialize web3 connection."""
        if self._web3 is None:
            web3_cls = _require_web3()
            self._web3 = web3_cls(web3_cls.HTTPProvider(self._config.rpc_url))
        return self._web3

    def _get_contract(self) -> Any:
        """Lazily initialize contract instance."""
        if self._contract is None:
            w3 = self._get_web3()
            self._contract = w3.eth.contract(
                address=self._config.reputation_registry,
                abi=REPUTATION_REGISTRY_ABI,
            )
        return self._contract

    def publish_assertions(
        self,
        plugin_token_id: str,
        commit_hash: str,
        assertions: list[AssertionResult],
    ) -> str:
        """Publish L1/L2/L3 assertion results on-chain.

        Args:
            plugin_token_id: The plugin's identity token ID.
            commit_hash: Git commit hash these assertions apply to.
            assertions: List of assertion outcomes to publish.

        Returns:
            Transaction hash of the publish operation.

        Raises:
            PermissionError: If no private key is configured.

        """
        if self._config.is_read_only:
            msg = "Cannot send transactions in read-only mode (no private key)"
            raise PermissionError(msg)

        w3 = self._get_web3()
        contract = self._get_contract()
        data = _serialize_assertions(assertions)

        account = w3.eth.account.from_key(self._config.private_key)

        fn = contract.functions.publishAssertions(
            int(plugin_token_id), commit_hash, data
        )
        tx = fn.build_transaction(
            {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "chainId": self._config.chain_id,
            },
        )
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        result_hash = receipt.transactionHash.hex()
        logger.info(
            "Published %d assertions for commit %s (tx: %s)",
            len(assertions),
            commit_hash[:8],
            result_hash,
        )
        return str(result_hash)

    def get_assertion_history(
        self,
        plugin_token_id: str,
        limit: int = 10,
    ) -> list[AssertionRecord]:
        """Query assertion history for a plugin.

        Args:
            plugin_token_id: The plugin's identity token ID.
            limit: Maximum number of records to return.

        Returns:
            List of AssertionRecord objects, most recent first.

        """
        contract = self._get_contract()
        try:
            results = contract.functions.getAssertionHistory(
                int(plugin_token_id), limit
            ).call()
            records = []
            for item in results:
                commit_hash, data, published_at = item
                records.append(
                    AssertionRecord(
                        commit_hash=commit_hash,
                        assertions=_deserialize_assertions(data),
                        published_at=published_at,
                        tx_hash="",
                    ),
                )
            return records
        except Exception:
            logger.debug(
                "No assertion history for token %s",
                plugin_token_id,
            )
            return []

    def get_trust_score(self, plugin_token_id: str) -> TrustScore:
        """Calculate aggregate trust score from assertion history.

        Fetches the full assertion history and computes pass rates
        per assertion level (L1/L2/L3).

        Args:
            plugin_token_id: The plugin's identity token ID.

        Returns:
            TrustScore with per-level pass rates and totals.

        """
        records = self.get_assertion_history(plugin_token_id, limit=100)

        all_assertions: list[AssertionResult] = []
        commit_hashes: set[str] = set()

        for record in records:
            all_assertions.extend(record.assertions)
            commit_hashes.add(record.commit_hash)

        if not all_assertions:
            return TrustScore()

        return TrustScore(
            l1_pass_rate=_calculate_pass_rate(all_assertions, "L1"),
            l2_pass_rate=_calculate_pass_rate(all_assertions, "L2"),
            l3_pass_rate=_calculate_pass_rate(all_assertions, "L3"),
            total_assertions=len(all_assertions),
            versions_verified=len(commit_hashes),
        )
