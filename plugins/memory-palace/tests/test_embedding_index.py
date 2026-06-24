"""Regression tests for embedding index provider management."""

from __future__ import annotations

import ast
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


class TestMP011OptionalDepExceptionNarrowing:
    """MP-011: module-level optional-dep catches must use ImportError, not Exception."""

    def test_optional_import_blocks_catch_only_import_error(self) -> None:
        """numpy and sentence_transformers import try/except must catch ImportError.

        except Exception swallows AttributeError, RuntimeError, and other bugs in
        optional dependencies. Only ImportError (and its subclass ModuleNotFoundError)
        is expected when an optional package is absent.
        """
        src = (
            Path(__file__).parent.parent
            / "src"
            / "memory_palace"
            / "corpus"
            / "embedding_index.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(src)

        # Collect all module-level (depth-1) try/except handlers
        top_level_bare_exceptions = []
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if handler.type is None:
                    top_level_bare_exceptions.append("bare except")
                elif isinstance(handler.type, ast.Name):
                    if handler.type.id == "Exception":
                        top_level_bare_exceptions.append("except Exception")

        assert top_level_bare_exceptions == [], (
            f"Module-level import blocks must use except ImportError, "
            f"found: {top_level_bare_exceptions} (MP-011)"
        )
