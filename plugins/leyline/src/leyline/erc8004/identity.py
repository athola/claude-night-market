"""ERC-8004 Identity Registry wrapper.

Register and query plugin/skill identities as ERC-721 tokens
on the ERC-8004 Identity Registry contract.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from leyline.erc8004.config import ERC8004Config

logger = logging.getLogger(__name__)

# Minimal ABI for Identity Registry interactions
IDENTITY_REGISTRY_ABI: list[dict[str, Any]] = [
    {
        "name": "registerIdentity",
        "type": "function",
        "inputs": [
            {"name": "name", "type": "string"},
            {"name": "metadataURI", "type": "string"},
        ],
        "outputs": [{"name": "tokenId", "type": "uint256"}],
    },
    {
        "name": "registerSubIdentity",
        "type": "function",
        "inputs": [
            {"name": "parentTokenId", "type": "uint256"},
            {"name": "name", "type": "string"},
            {"name": "metadataURI", "type": "string"},
        ],
        "outputs": [{"name": "tokenId", "type": "uint256"}],
    },
    {
        "name": "getIdentityByName",
        "type": "function",
        "inputs": [{"name": "name", "type": "string"}],
        "outputs": [
            {"name": "tokenId", "type": "uint256"},
            {"name": "name", "type": "string"},
            {"name": "metadataURI", "type": "string"},
            {"name": "owner", "type": "address"},
        ],
    },
    {
        "name": "getSubIdentities",
        "type": "function",
        "inputs": [{"name": "parentTokenId", "type": "uint256"}],
        "outputs": [
            {
                "name": "identities",
                "type": "tuple[]",
                "components": [
                    {"name": "tokenId", "type": "uint256"},
                    {"name": "name", "type": "string"},
                    {"name": "metadataURI", "type": "string"},
                ],
            },
        ],
    },
]


def _require_web3() -> Any:
    """Import web3 or raise a clear error."""
    try:
        from web3 import Web3  # type: ignore[import-not-found]  # noqa: PLC0415

        return Web3
    except ImportError:
        msg = "Install web3 for ERC-8004 support: pip install web3"
        raise ImportError(msg) from None


class IdentityRegistry:
    """Register and query plugin/skill identities on ERC-8004.

    Each plugin is represented as an ERC-721 token on the Identity
    Registry. Skills are registered as sub-identities under their
    parent plugin.

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
                address=self._config.identity_registry,
                abi=IDENTITY_REGISTRY_ABI,
            )
        return self._contract

    def _build_and_send_tx(self, fn: Any) -> str:
        """Build, sign, and send a contract transaction.

        Args:
            fn: A prepared contract function call.

        Returns:
            Transaction hash as hex string.

        Raises:
            PermissionError: If config is read-only (no private key).

        """
        if self._config.is_read_only:
            msg = "Cannot send transactions in read-only mode (no private key)"
            raise PermissionError(msg)

        w3 = self._get_web3()
        account = w3.eth.account.from_key(self._config.private_key)

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

        return str(receipt.transactionHash.hex())

    def register_plugin(self, plugin_name: str, metadata_uri: str) -> str:
        """Register a plugin as an ERC-721 identity.

        Args:
            plugin_name: Unique name for the plugin (e.g. "leyline").
            metadata_uri: URI pointing to plugin metadata (e.g. IPFS URI).

        Returns:
            Transaction hash of the registration.

        Raises:
            PermissionError: If no private key is configured.

        """
        contract = self._get_contract()
        fn = contract.functions.registerIdentity(plugin_name, metadata_uri)
        tx_hash = self._build_and_send_tx(fn)
        logger.info(
            "Registered plugin '%s' (tx: %s)",
            plugin_name,
            tx_hash,
        )
        return tx_hash

    def register_skill(
        self, plugin_token_id: str, skill_name: str, metadata_uri: str
    ) -> str:
        """Register a skill under a plugin identity.

        Args:
            plugin_token_id: Parent plugin's token ID.
            skill_name: Name of the skill to register.
            metadata_uri: URI pointing to skill metadata.

        Returns:
            Transaction hash of the registration.

        Raises:
            PermissionError: If no private key is configured.

        """
        contract = self._get_contract()
        fn = contract.functions.registerSubIdentity(
            int(plugin_token_id), skill_name, metadata_uri
        )
        tx_hash = self._build_and_send_tx(fn)
        logger.info(
            "Registered skill '%s' under plugin %s (tx: %s)",
            skill_name,
            plugin_token_id,
            tx_hash,
        )
        return tx_hash

    def get_plugin_identity(self, plugin_name: str) -> dict[str, Any] | None:
        """Query plugin identity by name.

        Args:
            plugin_name: The plugin name to look up.

        Returns:
            Dictionary with token_id, name, metadata_uri, and owner,
            or None if not found.

        """
        contract = self._get_contract()
        try:
            result = contract.functions.getIdentityByName(plugin_name).call()
            token_id, name, metadata_uri, owner = result
            if token_id == 0:
                return None
            return {
                "token_id": str(token_id),
                "name": name,
                "metadata_uri": metadata_uri,
                "owner": owner,
            }
        except Exception:
            logger.debug("Identity not found for '%s'", plugin_name)
            return None

    def get_skills_for_plugin(self, plugin_token_id: str) -> list[dict[str, Any]]:
        """List all registered skills for a plugin.

        Args:
            plugin_token_id: The parent plugin's token ID.

        Returns:
            List of dicts with token_id, name, and metadata_uri.

        """
        contract = self._get_contract()
        try:
            results = contract.functions.getSubIdentities(int(plugin_token_id)).call()
            return [
                {
                    "token_id": str(item[0]),
                    "name": item[1],
                    "metadata_uri": item[2],
                }
                for item in results
            ]
        except Exception:
            logger.debug("No skills found for plugin token %s", plugin_token_id)
            return []
