"""Lightweight embedding index with optional sentence-transformer integration."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

try:
    from sentence_transformers import (  # type: ignore[import-not-found]
        SentenceTransformer,
    )

    _HAS_ST = True
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore[assignment]
    _HAS_ST = False


def _hash_vector(text: str, dim: int = 16) -> list[float]:
    """Provide a secondary vectorization using hashing (no external deps)."""
    text = text.lower().strip()
    vec = [0.0] * dim
    for idx, chunk in enumerate(text.split()):
        digest = hashlib.sha256(chunk.encode("utf-8")).digest()
        value = digest[0] / 255.0
        vec[idx % dim] += value
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class EmbeddingIndex:
    """Simple embedding index that supports local + hashed providers.

    Supports room-scoped partitioning to prevent cross-domain knowledge
    contamination. Entries can be added to named rooms, and searches can
    be scoped to individual rooms or run across multiple rooms.
    """

    def __init__(self, embeddings_path: str, provider: str = "none") -> None:
        """Initialize embedding index with optional provider name."""
        self.requested_provider = provider
        self.embeddings_path = Path(embeddings_path)
        self.raw_store = self._load_store()
        self.active_provider, self.entries = self._select_entries()
        self._room_entries: dict[str, dict[str, list[float]]] = {}
        self._load_room_entries()
        self.model = None
        if self.active_provider == "local":
            self._maybe_load_model()

    def _load_store(self) -> dict[str, Any]:
        """Load embeddings YAML into a dictionary structure."""
        if not self.embeddings_path.exists():
            return {"providers": {}, "metadata": {}}
        data = yaml.safe_load(self.embeddings_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("providers", {})
        data.setdefault("metadata", {})
        return data

    def _select_entries(self) -> tuple[str, dict[str, list[float]]]:
        """Select active provider + embeddings from stored payload."""
        providers = self.raw_store.get("providers", {})
        metadata = self.raw_store.get("metadata", {})

        if providers:
            if self.requested_provider in providers:
                return self.requested_provider, providers[self.requested_provider].get(
                    "embeddings", {}
                )

            default_provider = metadata.get("default_provider")
            if default_provider in providers:
                return default_provider, providers[default_provider].get(
                    "embeddings", {}
                )

            secondary_provider = next(iter(providers))
            return secondary_provider, providers[secondary_provider].get(
                "embeddings", {}
            )

        # Legacy single-provider structure
        if "embeddings" in self.raw_store:
            legacy_provider = self.raw_store.get("provider") or self.requested_provider
            embeddings = self.raw_store.get("embeddings") or {}
            self.raw_store["providers"] = {
                legacy_provider: {"embeddings": embeddings},
            }
            self.raw_store.setdefault("metadata", {})["default_provider"] = (
                legacy_provider
            )
            self.raw_store.pop("embeddings", None)
            self.raw_store.pop("provider", None)
            return legacy_provider, embeddings

        # No data yet -- honor requested provider for future exports
        return self.requested_provider, {}

    def _load_room_entries(self) -> None:
        """Load room-partitioned entries from the active provider's data."""
        providers = self.raw_store.get("providers", {})
        provider_data = providers.get(self.active_provider, {})
        rooms = provider_data.get("rooms", {})
        for room_name, room_data in rooms.items():
            embeddings = room_data.get("embeddings", {})
            if embeddings:
                self._room_entries[room_name] = dict(embeddings)

    def _maybe_load_model(self) -> None:
        if _HAS_ST and SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.model = None
        else:
            self.model = None

    @property
    def provider(self) -> str:
        """Expose the provider currently in use."""
        return self.active_provider

    def vectorize(self, text: str) -> list[float]:
        """Vectorize text using the active provider."""
        if self.active_provider == "local" and self.model is not None:
            vector = self.model.encode(text).tolist()  # type: ignore[assignment]
            norm = math.sqrt(sum(v * v for v in vector)) or 1.0
            return [v / norm for v in vector]
        return _hash_vector(text)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Return top-k matches for a query."""
        if not self.entries:
            return []
        query_vec = self.vectorize(query)
        scores = []
        for entry, vector in self.entries.items():
            score = self._dot(query_vec, vector)
            scores.append((entry, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    # -- Room-scoped operations ------------------------------------------------

    def add_to_room(self, room: str, entry_id: str, text: str) -> None:
        """Add an entry to a room-specific index partition."""
        if room not in self._room_entries:
            self._room_entries[room] = {}
        vector = self.vectorize(text)
        self._room_entries[room][entry_id] = vector

    def search_room(
        self, room: str, query: str, top_k: int = 5
    ) -> list[tuple[str, float]]:
        """Search within a specific room's index only."""
        room_data = self._room_entries.get(room, {})
        if not room_data:
            return []
        query_vec = self.vectorize(query)
        scores: list[tuple[str, float]] = []
        for entry_id, vector in room_data.items():
            score = self._dot(query_vec, vector)
            scores.append((entry_id, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def search_across_rooms(
        self,
        query: str,
        rooms: list[str] | None = None,
        top_k: int = 5,
    ) -> list[tuple[str, str, float]]:
        """Search across multiple rooms, returning (entry_id, room, score) tuples."""
        target_rooms = rooms if rooms is not None else list(self._room_entries.keys())
        query_vec = self.vectorize(query)
        scores: list[tuple[str, str, float]] = []
        for room_name in target_rooms:
            room_data = self._room_entries.get(room_name, {})
            for entry_id, vector in room_data.items():
                score = self._dot(query_vec, vector)
                scores.append((entry_id, room_name, score))
        scores.sort(key=lambda x: x[2], reverse=True)
        return scores[:top_k]

    def get_room_entries(self) -> dict[str, dict[str, list[float]]]:
        """Return the internal room-partitioned entries dict."""
        return dict(self._room_entries)

    def get_room_stats(self) -> dict[str, int]:
        """Return entry counts per room."""
        return {room: len(entries) for room, entries in self._room_entries.items()}

    # -- Persistence -----------------------------------------------------------

    def export(
        self,
        path: str | Path | None = None,
        *,
        provider: str | None = None,
        entries: dict[str, list[float]] | None = None,
    ) -> Path:
        """Persist vectors under the provider block.

        When room-partitioned entries exist, they are serialized under a
        ``rooms`` key inside the provider block. Flat (non-room) entries
        are stored under the ``embeddings`` key as before.
        """
        target_path = Path(path) if path else self.embeddings_path
        target_provider = provider or self.requested_provider or self.active_provider
        payload = entries if entries is not None else self.entries

        store = self.raw_store
        store.setdefault("providers", {})
        store.setdefault("metadata", {})

        provider_block: dict[str, Any] = {
            "updated_at": datetime.now().isoformat(),
        }

        # Persist flat entries when present
        if payload:
            provider_block["embeddings"] = payload
            provider_block["vector_dimension"] = (
                len(next(iter(payload.values()))) if payload else 0
            )

        # Persist room-partitioned entries when present
        if self._room_entries:
            rooms_block: dict[str, Any] = {}
            for room_name, room_data in self._room_entries.items():
                rooms_block[room_name] = {
                    "embeddings": room_data,
                }
            provider_block["rooms"] = rooms_block
            # Set vector_dimension from room data if not set from flat entries
            if "vector_dimension" not in provider_block:
                for room_data in self._room_entries.values():
                    if room_data:
                        first_vec = next(iter(room_data.values()))
                        provider_block["vector_dimension"] = len(first_vec)
                        break

        store["providers"][target_provider] = provider_block
        if not store["metadata"].get("default_provider"):
            store["metadata"]["default_provider"] = target_provider

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(yaml.safe_dump(store, sort_keys=False), encoding="utf-8")

        self.raw_store = store
        self.active_provider = target_provider
        self.entries = payload

        return target_path

    @staticmethod
    def _dot(a: list[float], b: list[float]) -> float:
        length = min(len(a), len(b))
        return sum(a[i] * b[i] for i in range(length))
