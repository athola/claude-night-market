"""The package roots resolve their exports lazily, and completely.

``memory_palace`` and ``memory_palace.corpus`` import nothing eagerly,
so a hook that wants one stdlib-only leaf does not pay for PyYAML. The
cost of that shape is a second list, ``_EXPORT_SOURCES``, that can
drift from ``__all__`` and fail only at the first ``from memory_palace
import ThatName``. These tests hold the two lists together and pin the
branches the hook-import test never reaches: the unknown name, the
``dir()`` listing, and the corpus fallback for an optional dependency.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest

import memory_palace
from memory_palace import corpus

ROOTS = [memory_palace, corpus]
ROOT_IDS = [module.__name__ for module in ROOTS]


@pytest.mark.parametrize("root", ROOTS, ids=ROOT_IDS)
def test_every_declared_export_resolves(root: ModuleType) -> None:
    """GIVEN a package root that resolves exports on first access.

    WHEN each name in __all__ is read
    THEN each resolves, so the source map and __all__ have not drifted
    """
    unresolved = [name for name in root.__all__ if not hasattr(root, name)]

    assert unresolved == []


@pytest.mark.parametrize("root", ROOTS, ids=ROOT_IDS)
def test_resolved_export_comes_from_the_module_that_defines_it(
    root: ModuleType,
) -> None:
    """GIVEN a lazily resolved class.

    WHEN its __module__ is read
    THEN it is a submodule of the root, not a copy made in the root
    """
    for name in root.__all__:
        exported = getattr(root, name)
        if isinstance(exported, type):
            assert exported.__module__.startswith(root.__name__ + ".")


@pytest.mark.parametrize("root", ROOTS, ids=ROOT_IDS)
def test_unknown_name_raises_attribute_error_naming_the_module(
    root: ModuleType,
) -> None:
    """GIVEN a name no submodule defines.

    WHEN it is read from the root
    THEN AttributeError names the root, as a plain module would
    """
    with pytest.raises(AttributeError, match=root.__name__):
        _ = root.NotAnExport


@pytest.mark.parametrize("root", ROOTS, ids=ROOT_IDS)
def test_dir_lists_every_export(root: ModuleType) -> None:
    """GIVEN __getattr__ is invisible to dir().

    WHEN dir() is called on the root
    THEN every export is listed, so the root does not look empty
    """
    listed = set(dir(root))

    assert set(root.__all__) <= listed


def test_optional_corpus_exports_fall_back_when_the_dependency_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GIVEN semantic_deduplicator cannot be imported.

    WHEN the two exports it provides are read
    THEN the threshold is 0.85 and the class is None, as before the
         root went lazy
    """
    monkeypatch.setitem(sys.modules, "memory_palace.corpus.semantic_deduplicator", None)

    assert corpus.DEFAULT_THRESHOLD == 0.85
    assert corpus.SemanticDeduplicator is None


def test_optional_corpus_exports_resolve_when_the_dependency_is_present() -> None:
    """GIVEN the dependency imports (the test venv carries it).

    WHEN the same two exports are read
    THEN they come from the real module, not the fallback
    """
    real = importlib.import_module("memory_palace.corpus.semantic_deduplicator")

    assert corpus.SemanticDeduplicator is real.SemanticDeduplicator
    assert corpus.DEFAULT_THRESHOLD == real.DEFAULT_THRESHOLD
