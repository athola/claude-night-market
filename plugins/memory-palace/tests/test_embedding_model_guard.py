"""An index built by one embedding model must not be queried by another."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from memory_palace.corpus.embedding_index import (
    EmbeddingDimensionError,
    EmbeddingIndex,
    EmbeddingModelMismatchError,
)


def _built_hash_index(path: Path) -> EmbeddingIndex:
    index = EmbeddingIndex(str(path), provider="hash")
    index.entries = {"alpha": index.vectorize("alpha beta")}
    index.add_to_room("r1", "gamma", "gamma delta")
    index.export()
    return index


def _rewrite_model_id(path: Path, model_id: str | None) -> None:
    store = yaml.safe_load(path.read_text(encoding="utf-8"))
    block = store["providers"]["hash"]
    if model_id is None:
        block.pop("model_id", None)
    else:
        block["model_id"] = model_id
    path.write_text(yaml.safe_dump(store, sort_keys=False), encoding="utf-8")


def test_export_records_the_model_that_built_the_index(tmp_path: Path) -> None:
    path = tmp_path / "emb.yaml"
    index = _built_hash_index(path)

    store = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert store["providers"]["hash"]["model_id"] == index.model_id


def test_search_raises_when_stored_model_differs_from_query_model(
    tmp_path: Path,
) -> None:
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, "some-other-16-dim-model")

    index = EmbeddingIndex(str(path), provider="hash")

    with pytest.raises(EmbeddingModelMismatchError, match="some-other-16-dim-model"):
        index.search("alpha")


def test_room_searches_raise_when_stored_model_differs(tmp_path: Path) -> None:
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, "some-other-16-dim-model")
    index = EmbeddingIndex(str(path), provider="hash")

    with pytest.raises(EmbeddingModelMismatchError):
        index.search_room("r1", "gamma")
    with pytest.raises(EmbeddingModelMismatchError):
        index.search_across_rooms("gamma")


def test_search_works_when_stored_model_matches(tmp_path: Path) -> None:
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)

    index = EmbeddingIndex(str(path), provider="hash")

    assert index.search("alpha beta")[0][0] == "alpha"
    assert index.search_room("r1", "gamma delta")[0][0] == "gamma"


def test_legacy_index_without_model_id_still_searches(tmp_path: Path) -> None:
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, None)

    index = EmbeddingIndex(str(path), provider="hash")

    assert index.search("alpha beta")[0][0] == "alpha"


def test_saving_a_legacy_index_leaves_its_model_unknown(tmp_path: Path) -> None:
    # Stamping the current model would guess: hash-fallback vectors saved
    # before sentence-transformers was installed would pass as MiniLM and
    # every later search would rank noise without an error.
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, None)
    index = EmbeddingIndex(str(path), provider="hash")

    index.export()

    store = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "model_id" not in store["providers"]["hash"]


def test_local_store_queried_after_model_load_failure_names_both_models(
    tmp_path: Path,
) -> None:
    """A local store whose model did not load falls back to hash vectors."""
    path = tmp_path / "emb.yaml"
    store = {
        "providers": {
            "local": {
                "model_id": "all-MiniLM-L6-v2",
                "embeddings": {"alpha": [0.1] * 16},
            }
        },
        "metadata": {"default_provider": "local"},
    }
    path.write_text(yaml.safe_dump(store, sort_keys=False), encoding="utf-8")
    index = EmbeddingIndex(str(path), provider="local")
    index.model = None  # SentenceTransformer unavailable or failed to load

    with pytest.raises(EmbeddingModelMismatchError, match="all-MiniLM-L6-v2"):
        index.search("alpha")


def test_mismatch_error_is_caught_where_dimension_errors_already_are() -> None:
    assert issubclass(EmbeddingModelMismatchError, EmbeddingDimensionError)


def test_add_to_room_raises_when_stored_model_differs(tmp_path: Path) -> None:
    """Mixing a second model's vectors into a room made the store unqueryable."""
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, "some-other-16-dim-model")
    index = EmbeddingIndex(str(path), provider="hash")

    with pytest.raises(EmbeddingModelMismatchError):
        index.add_to_room("r1", "epsilon", "epsilon zeta")


def test_export_refuses_to_restamp_another_models_vectors(tmp_path: Path) -> None:
    """Export wrote the current model id over vectors another model built."""
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, "some-other-16-dim-model")
    index = EmbeddingIndex(str(path), provider="hash")

    with pytest.raises(EmbeddingModelMismatchError):
        index.export()
    store = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert store["providers"]["hash"]["model_id"] == "some-other-16-dim-model"


def test_export_with_explicit_entries_rebuilds_an_index_from_another_model(
    tmp_path: Path,
) -> None:
    """The mismatch error said to rebuild the index, and no call could."""
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, "some-other-16-dim-model")
    index = EmbeddingIndex(str(path), provider="hash")

    index.export(entries={"alpha": index.vectorize("alpha beta")})

    block = yaml.safe_load(path.read_text(encoding="utf-8"))["providers"]["hash"]
    assert block["model_id"] == index.model_id
    assert "rooms" not in block
    reloaded = EmbeddingIndex(str(path), provider="hash")
    assert reloaded.search("alpha")[0][0] == "alpha"


def test_mismatch_error_names_the_rebuild_call(tmp_path: Path) -> None:
    path = tmp_path / "emb.yaml"
    _built_hash_index(path)
    _rewrite_model_id(path, "some-other-16-dim-model")
    index = EmbeddingIndex(str(path), provider="hash")

    with pytest.raises(EmbeddingModelMismatchError, match=r"export\(entries="):
        index.search("alpha")
