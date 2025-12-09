"""Lightweight embedding index with optional sentence-transformer integration."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime
from pathlib import Path

import yaml


def _hash_vector(text: str, dim: int = 16) -> list[float]:
    """Fallback vectorization using hashing (no external deps)."""
    text = text.lower().strip()
    vec = [0.0] * dim
    for idx, chunk in enumerate(text.split()):
        digest = hashlib.sha256(chunk.encode("utf-8")).digest()
        value = digest[0] / 255.0
        vec[idx % dim] += value
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class EmbeddingIndex:
    """Simple embedding index that supports local + hashed providers."""

    def __init__(self, embeddings_path: str, provider: str = "none") -> None:
        self.requested_provider = provider
        self.embeddings_path = Path(embeddings_path)
        self.raw_store = self._load_store()
        self.active_provider, self.entries = self._select_entries()
        self.model = None
        if self.active_provider == "local":
            self._maybe_load_model()

    def _load_store(self) -> dict[str, Any]:
        if not self.embeddings_path.exists():
            return {"providers": {}, "metadata": {}}
        data = yaml.safe_load(self.embeddings_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("providers", {})
        data.setdefault("metadata", {})
        return data

    def _select_entries(self) -> tuple[str, dict[str, list[float]]]:
        providers = self.raw_store.get("providers", {})
        metadata = self.raw_store.get("metadata", {})

        if providers:
            if self.requested_provider in providers:
                return self.requested_provider, providers[self.requested_provider].get(
                    "embeddings", {}
                )

            default_provider = metadata.get("default_provider")
            if default_provider in providers:
                return default_provider, providers[default_provider].get("embeddings", {})

            fallback_provider = next(iter(providers))
            return fallback_provider, providers[fallback_provider].get("embeddings", {})

        # Legacy single-provider structure
        if "embeddings" in self.raw_store:
            legacy_provider = self.raw_store.get("provider") or self.requested_provider
            embeddings = self.raw_store.get("embeddings") or {}
            self.raw_store["providers"] = {
                legacy_provider: {"embeddings": embeddings},
            }
            self.raw_store.setdefault("metadata", {})["default_provider"] = legacy_provider
            self.raw_store.pop("embeddings", None)
            self.raw_store.pop("provider", None)
            return legacy_provider, embeddings

        # No data yet – honor requested provider for future exports
        return self.requested_provider, {}

    def _maybe_load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            self.model = None

    @property
    def provider(self) -> str:
        """Expose the provider currently in use."""
        return self.active_provider

    def vectorize(self, text: str) -> list[float]:
        if self.active_provider == "local" and self.model is not None:
            vector = self.model.encode(text).tolist()  # type: ignore[assignment]
            norm = math.sqrt(sum(v * v for v in vector)) or 1.0
            return [v / norm for v in vector]
        return _hash_vector(text)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        if not self.entries:
            return []
        query_vec = self.vectorize(query)
        scores = []
        for entry, vector in self.entries.items():
            score = self._dot(query_vec, vector)
            scores.append((entry, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def export(
        self,
        path: str | Path | None = None,
        *,
        provider: str | None = None,
        entries: dict[str, list[float]] | None = None,
    ) -> Path:
        """Persist vectors under the provider block."""
        target_path = Path(path) if path else self.embeddings_path
        target_provider = provider or self.requested_provider or self.active_provider
        payload = entries if entries is not None else self.entries

        store = self.raw_store
        store.setdefault("providers", {})
        store.setdefault("metadata", {})
        store["providers"][target_provider] = {
            "embeddings": payload,
            "updated_at": datetime.now().isoformat(),
            "vector_dimension": len(next(iter(payload.values()))) if payload else 0,
        }
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
