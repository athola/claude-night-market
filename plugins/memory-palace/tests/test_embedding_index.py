"""Regression tests for embedding index provider management."""

from __future__ import annotations

from pathlib import Path

import yaml

from memory_palace.corpus.embedding_index import EmbeddingIndex


def test_loads_named_provider_block(tmp_path: Path) -> None:
    """EmbeddingIndex should hydrate entries for the requested provider."""
    embeddings_path = tmp_path / "embeddings.yaml"
    data = {
        "providers": {
            "hash": {"embeddings": {"alpha-entry": [0.1, 0.2]}},
            "local": {"embeddings": {"beta-entry": [0.9, 0.8]}},
        },
        "metadata": {"default_provider": "hash"},
    }
    embeddings_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    index = EmbeddingIndex(str(embeddings_path), provider="local")

    assert "beta-entry" in index.entries
    assert index.active_provider == "local"


def test_export_persists_provider_vectors(tmp_path: Path) -> None:
    """Export should persist vectors under the provider block."""
    embeddings_path = tmp_path / "embeddings.yaml"
    index = EmbeddingIndex(str(embeddings_path), provider="hash")
    index.entries = {"franklin-protocol": [0.1] * 4}

    output_path = tmp_path / "exported.yaml"
    index.export(output_path)

    data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert "hash" in data["providers"]
    stored = data["providers"]["hash"]["embeddings"]["franklin-protocol"]
    assert stored == index.entries["franklin-protocol"]
    assert data["metadata"]["default_provider"] == "hash"
