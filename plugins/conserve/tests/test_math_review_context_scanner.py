"""Counts the context scanner prints (math review B2-16 to B2-18).

Each test pins a count the scan report got wrong. The "...N more" tail
for dependencies and directories could never print, and relative
imports of same-named modules were all credited to whichever file was
indexed first.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
cs = importlib.import_module("context_scanner")


def _result(**overrides):
    fields = {
        "project_name": "p",
        "total_files": 1,
        "directories": [],
        "ecosystems": [],
        "config_files": [],
    }
    fields.update(overrides)
    return cs.ScanResult(**fields)


def test_markdown_says_how_many_dependencies_were_cut() -> None:
    """summarize() cut the list first, so the tail always read 0 (B2-16)."""
    deps = [cs.Dependency(f"dep{i}") for i in range(20)]
    eco = cs.EcosystemResult(name="Python", package_manager="uv", dependencies=deps)
    md = cs.render_markdown(_result(ecosystems=[eco]), max_deps=8)
    assert sum(line.startswith("  - dep") for line in md.splitlines()) == 8
    assert "...12 more" in md


def test_structure_section_says_how_many_directories_were_cut() -> None:
    """The section path never ran summarize(), so its tail was 0 (B2-17)."""
    dirs = [cs.DirectoryInfo(f"d{i}", 1) for i in range(20)]
    section = cs.render_section(_result(directories=dirs), "structure")
    assert "...8 more" in section


def test_relative_imports_resolve_inside_their_own_package(tmp_path: Path) -> None:
    """Both packages' `from .utils import X` went to alpha/utils.py (B2-18)."""
    for pkg in ("alpha", "beta"):
        (tmp_path / pkg).mkdir()
        (tmp_path / pkg / "__init__.py").write_text("")
        (tmp_path / pkg / "utils.py").write_text("X = 1\n")
        for i in range(3):
            (tmp_path / pkg / f"m{i}.py").write_text("from .utils import X\n")

    graph = cs.build_import_graph(tmp_path)
    counts = {k: len(v) for k, v in graph.imported_by.items()}
    assert counts == {"alpha/utils.py": 3, "beta/utils.py": 3}


def test_a_parent_relative_import_climbs_one_package(tmp_path: Path) -> None:
    """`from ..core import X` names the sibling of the importer's package."""
    (tmp_path / "pkg" / "sub").mkdir(parents=True)
    (tmp_path / "pkg" / "core.py").write_text("X = 1\n")
    (tmp_path / "pkg" / "sub" / "user.py").write_text("from ..core import X\n")

    graph = cs.build_import_graph(tmp_path)
    assert dict(graph.imported_by) == {"pkg/core.py": {"pkg/sub/user.py"}}
