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


class TestMP008JaccardDeadCodeRemoved:
    """MP-008: _stored_texts and _should_store_jaccard are dead; must be removed.

    faiss-cpu is a mandatory dependency and _use_faiss is always True,
    making _stored_texts and _should_store_jaccard unreachable. AST-based
    tests avoid the faiss import so they run on system Python.
    """

    def _dedup_source(self) -> ast.Module:
        src_path = (
            Path(__file__).parent.parent
            / "src"
            / "memory_palace"
            / "corpus"
            / "semantic_deduplicator.py"
        )
        return ast.parse(src_path.read_text(encoding="utf-8"))

    def test_stored_texts_attribute_removed_from_init(self) -> None:
        """__init__ must not assign self._stored_texts.

        _stored_texts was populated only by add_text which is a no-op in
        FAISS mode, making the attribute permanently empty and misleading.
        """
        tree = self._dedup_source()
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name != "__init__":
                continue
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Assign)
                    and isinstance(child.targets[0], ast.Attribute)
                    and child.targets[0].attr == "_stored_texts"
                ):
                    assert False, (
                        "Dead attribute self._stored_texts still assigned in __init__; "
                        "remove it (MP-008)"
                    )

    def test_should_store_jaccard_method_removed(self) -> None:
        """SemanticDeduplicator class must not define _should_store_jaccard.

        The method is unreachable: should_store's else-branch only runs when
        _use_faiss is False, which never happens with mandatory faiss-cpu.
        """
        tree = self._dedup_source()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "SemanticDeduplicator":
                method_names = [
                    m.name for m in ast.walk(node) if isinstance(m, ast.FunctionDef)
                ]
                assert "_should_store_jaccard" not in method_names, (
                    "Dead method _should_store_jaccard still present; remove it (MP-008)"
                )


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
