"""``Path.parents`` must not be sliced anywhere a 3.9 hook can reach.

``PurePath.parents`` only became a full sequence in Python 3.10. On 3.9
it supports integer indexing and nothing else, so ``parents[:4]`` raises
``TypeError: '<' not supported between instances of 'slice' and 'int'``
at the moment the module is imported.

Hooks run under the system interpreter, which the ``python39-compat``
workflow pins to 3.9 for exactly this reason. A slice that reaches a
hook import chain therefore takes down every test in that chain during
collection, which is how it presents: not one failing assertion but a
whole job erroring out before it runs.

No linter catches this. Ruff's ``UP`` rules find ``X | Y`` annotations
without ``from __future__ import annotations``, and
``leyline/tests/test_python39_compat.py`` finds the 3.11+
``datetime.UTC`` alias, but a slice on ``parents`` is valid syntax at
every version and legal on the 3.12 interpreter a developer runs
locally. It fails only on the version that ships.

This is a repo-wide scan rather than a per-plugin one because the
regression that prompted it spanned two plugins at once: the shared
resolution rule in ``leyline/plugin_data.py`` and the local copy of it
in ``memory_palace/paths.py`` were written from the same template, so
one review missed both.

Feature: no module reachable from a hook slices ``Path.parents``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PLUGINS = _REPO_ROOT / "plugins"


def _parents_aliases(tree: ast.AST) -> set[str]:
    """Return local names bound to a ``.parents`` attribute.

    The regression this guard exists for did not slice inline. It read
    ``parents = plugin_root.parents`` and sliced the local one line
    later, so the subscript target was an ``ast.Name`` and a detector
    looking only for ``ast.Attribute`` reported nothing. Both forms have
    to be tracked or the guard passes vacuously, which it did until this
    was written.
    """
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Attribute) or value.attr != "parents":
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        aliases.update(t.id for t in targets if isinstance(t, ast.Name))
    return aliases


def _sliced_parents(path: Path) -> list[str]:
    """Return descriptions of sliced ``.parents`` access found in ``path``.

    AST-based, so prose and comments discussing the pattern are not
    flagged, and integer indexing (``parents[3]``, the correct form) is
    left alone. A named constant index parses as ``ast.Name`` in the
    subscript position rather than ``ast.Slice`` and so also passes.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        # Deliberately not a failure: this guard reports one specific
        # incompatibility, and a file that cannot be parsed is a
        # different problem belonging to a different gate.
        return []

    aliases = _parents_aliases(tree)
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript) or not isinstance(node.slice, ast.Slice):
            continue
        target = node.value
        inline = isinstance(target, ast.Attribute) and target.attr == "parents"
        aliased = isinstance(target, ast.Name) and target.id in aliases
        if inline or aliased:
            hits.append(f"line {node.lineno}: sliced `.parents[...]`")
    return hits


def _python_files() -> list[Path]:
    """Return every plugin Python file, hooks and importable sources alike.

    Scoped wider than ``hooks/`` on purpose. The failure that prompted
    this guard was in ``src/``, two imports below the hook that broke.
    """
    files: list[Path] = []
    for plugin in sorted(_PLUGINS.iterdir()):
        if not plugin.is_dir():
            continue
        for subdir in ("hooks", "src", "scripts"):
            root = plugin / subdir
            if root.is_dir():
                files.extend(
                    p
                    for p in sorted(root.rglob("*.py"))
                    if "__pycache__" not in p.parts
                )
    return files


class TestNoSlicedPathParents:
    """The invariant, and a check that the detector can actually fail."""

    @pytest.mark.unit
    def test_no_plugin_module_slices_path_parents(self) -> None:
        """GIVEN every plugin hook, source, and script module
        WHEN each is parsed
        THEN none slices ``Path.parents``.
        """
        offenders = {
            str(path.relative_to(_REPO_ROOT)): hits
            for path in _python_files()
            if (hits := _sliced_parents(path))
        }

        assert not offenders, (
            "Path.parents slicing raises TypeError on Python 3.9, which "
            "hooks run under. Index one level at a time instead: "
            f"{offenders}"
        )

    @pytest.mark.unit
    def test_the_detector_flags_a_slice(self, tmp_path: Path) -> None:
        """GIVEN a module that slices ``.parents``
        WHEN it is scanned
        THEN the slice is reported.

        Without this, deleting the detector's body would leave the guard
        above passing and the invariant unenforced.
        """
        probe = tmp_path / "probe.py"
        probe.write_text(
            "from pathlib import Path\na, b = Path('/x/y/z').parents[:2]\n",
            encoding="utf-8",
        )

        assert _sliced_parents(probe)

    @pytest.mark.unit
    def test_the_detector_flags_a_slice_through_a_local_name(
        self, tmp_path: Path
    ) -> None:
        """GIVEN ``.parents`` bound to a local and then sliced
        WHEN the module is scanned
        THEN the slice is reported.

        This is the exact shape that shipped and broke CI. A detector
        matching only the inline form passed while the bug was present,
        so this case is the one that keeps the guard honest.
        """
        probe = tmp_path / "probe.py"
        probe.write_text(
            "from pathlib import Path\n"
            "DEPTH = 2\n"
            "parents = Path('/x/y/z').parents\n"
            "a, b = parents[:DEPTH]\n",
            encoding="utf-8",
        )

        assert _sliced_parents(probe)

    @pytest.mark.unit
    def test_the_detector_allows_integer_indexing(self, tmp_path: Path) -> None:
        """GIVEN a module that indexes ``.parents`` by integer and by a
        named constant
        WHEN it is scanned
        THEN nothing is reported, because both work on 3.9.
        """
        probe = tmp_path / "probe.py"
        probe.write_text(
            "from pathlib import Path\n"
            "DEPTH = 2\n"
            "first = Path('/x/y/z').parents[0]\n"
            "named = Path('/x/y/z').parents[DEPTH]\n"
            "parents = Path('/x/y/z').parents\n"
            "aliased = parents[DEPTH]\n",
            encoding="utf-8",
        )

        assert _sliced_parents(probe) == []
