"""The ``abstract`` root resolves its exports lazily, and completely.

The root imports nothing eagerly so ``hooks/shared/dir_utils.py`` can
reach ``abstract.paths`` without PyYAML. ``_EXPORT_SOURCES`` is the
second list that shape needs, and it can drift from ``__all__``. These
tests hold the two together and pin the branches the hook-import test
never reaches, plus the one ``paths`` branch its callers did not
exercise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import abstract
from abstract import paths, utils


def test_every_declared_export_resolves() -> None:
    """GIVEN a root that resolves exports on first access.

    WHEN each name in __all__ is read
    THEN each resolves, so the source map and __all__ have not drifted
    """
    unresolved = [name for name in abstract.__all__ if not hasattr(abstract, name)]

    assert unresolved == []


def test_resolved_class_comes_from_its_defining_submodule() -> None:
    """GIVEN a lazily resolved class.

    WHEN its __module__ is read
    THEN it is an abstract submodule, not a copy made in the root
    """
    for name in abstract.__all__:
        exported = getattr(abstract, name)
        if isinstance(exported, type):
            assert exported.__module__.startswith("abstract.")


def test_unknown_name_raises_attribute_error_naming_the_module() -> None:
    """GIVEN a name no submodule defines.

    WHEN it is read from the root
    THEN AttributeError names the root, as a plain module would
    """
    with pytest.raises(AttributeError, match="abstract"):
        _ = abstract.NotAnExport


def test_dir_lists_every_export() -> None:
    """GIVEN __getattr__ is invisible to dir().

    WHEN dir() is called on the root
    THEN every export is listed, so the root does not look empty
    """
    assert set(abstract.__all__) <= set(dir(abstract))


def test_observability_dir_is_created_on_request_under_claude_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GIVEN CLAUDE_HOME points at an empty directory.

    WHEN get_observability_dir(create=True) is called
    THEN the directory exists under that home, not under ~/.claude
    """
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))

    created = paths.get_observability_dir(create=True)

    assert created == tmp_path / "skills" / "observability"
    assert created.is_dir()


def test_observability_dir_is_not_created_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GIVEN the same home.

    WHEN the directory is only resolved
    THEN nothing is written, so a read-only caller leaves no trace
    """
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))

    resolved = paths.get_observability_dir()

    assert resolved == tmp_path / "skills" / "observability"
    assert not resolved.exists()


def test_utils_re_exports_are_the_paths_functions() -> None:
    """GIVEN callers still import the helpers from abstract.utils.

    WHEN the two modules' attributes are compared
    THEN they are the same objects, so a caller and a hook cannot
         diverge by resolving different code
    """
    assert utils.get_log_directory is paths.get_log_directory
    assert utils.get_config_dir is paths.get_config_dir
    assert utils.get_observability_dir is paths.get_observability_dir
