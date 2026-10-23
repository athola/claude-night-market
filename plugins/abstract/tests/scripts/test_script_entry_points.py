"""In-process runs of abstract wrapper scripts, for branches coverage cannot see in a child process.

Covers the improvement-suggester CLI entry point and the leyline-less
fallbacks of the discussion scripts (ADR-0001: a missing peer turns its
feature off with a clear message, and the rest keeps working).
"""

from __future__ import annotations

import importlib.abc
import importlib.util
import json
import runpy
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"

SKILL_MD = "---\nname: demo\ndescription: Use when testing\n---\n\n# Demo\n\nBody.\n"


class _BlockPackage(importlib.abc.MetaPathFinder):
    def __init__(self, package: str) -> None:
        self.package = package

    def find_spec(
        self,
        name: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> None:
        if name.split(".", maxsplit=1)[0] == self.package:
            raise ModuleNotFoundError(f"No module named {name!r}")


@pytest.fixture
def without_leyline() -> Iterator[None]:
    """Hide leyline, including any copy already imported, for one test."""
    saved = {
        n: sys.modules.pop(n) for n in list(sys.modules) if n.split(".")[0] == "leyline"
    }
    blocker = _BlockPackage("leyline")
    sys.meta_path.insert(0, blocker)
    yield
    sys.meta_path.remove(blocker)
    sys.modules.update(saved)


def _run_suggester(monkeypatch: pytest.MonkeyPatch, *argv: str) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    monkeypatch.setattr(sys, "argv", ["improvement_suggester.py", *argv])
    runpy.run_path(str(SCRIPTS / "improvement_suggester.py"), run_name="__main__")


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "skills" / "demo"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(SKILL_MD)
    return directory


@pytest.mark.unit
@pytest.mark.parametrize("given", ["directory", "file"])
def test_suggester_cli_plans_for_a_skill_given_as_directory_or_skill_md(
    given: str, skill_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both spellings of a skill path reach the same skill.

    GIVEN a skill directory holding SKILL.md
    WHEN the CLI gets the directory, or the SKILL.md path inside it
    THEN a JSON plan is written to --output.
    """
    target = skill_dir if given == "directory" else skill_dir / "SKILL.md"
    out = tmp_path / "plan.json"

    _run_suggester(monkeypatch, str(target), "--format", "json", "--output", str(out))

    assert isinstance(json.loads(out.read_text()), dict)


@pytest.mark.unit
def test_suggester_cli_exits_one_when_the_path_holds_no_skill_md(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A directory without SKILL.md is a usage error, not an empty plan.

    GIVEN an empty directory
    WHEN the CLI is run on it
    THEN it exits 1 and writes nothing.
    """
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "plan.json"

    with pytest.raises(SystemExit) as exc:
        _run_suggester(monkeypatch, str(empty), "--output", str(out))

    assert exc.value.code == 1
    assert not out.exists()


@pytest.mark.unit
def test_suggester_cli_exits_one_when_the_output_cannot_be_written(
    skill_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A bad --output path fails the run with one stderr line.

    GIVEN an --output path inside a directory that does not exist
    WHEN the CLI is run on a valid skill
    THEN it exits 1 and names the path on stderr.
    """
    out = tmp_path / "missing-dir" / "plan.json"

    with pytest.raises(SystemExit) as exc:
        _run_suggester(monkeypatch, str(skill_dir), "--output", str(out))

    assert exc.value.code == 1
    assert "cannot write" in capsys.readouterr().err


def _load(script: str, as_name: str, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec = importlib.util.spec_from_file_location(as_name, SCRIPTS / script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules[cls.__module__].
    monkeypatch.setitem(sys.modules, as_name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_posting_without_leyline_raises_an_error_callers_can_catch(
    without_leyline: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GitHub posting turns off with a typed error when leyline is absent.

    GIVEN leyline cannot be imported
    WHEN the module is imported and its graphql stub is called
    THEN a RuntimeError subclass says posting is off and carries the command.
    """
    monkeypatch.syspath_prepend(str(SCRIPTS))
    module = _load(
        "post_learnings_to_discussions.py", "post_learnings_no_leyline", monkeypatch
    )

    with pytest.raises(module._GhError, match="GitHub posting is off") as exc:
        module._gh_graphql("{ viewer { login } }")

    assert isinstance(exc.value, RuntimeError)
    assert type(exc.value) is not RuntimeError
    assert exc.value.cmd == ["gh", "api", "graphql"]


@pytest.mark.unit
def test_promote_direct_run_without_leyline_exits_naming_it(
    without_leyline: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A direct run says what is missing instead of printing a traceback.

    GIVEN leyline cannot be imported
    WHEN promote_discussion_to_issue.py runs as __main__
    THEN SystemExit carries a message naming the script and leyline.
    """
    monkeypatch.syspath_prepend(str(SCRIPTS))

    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(SCRIPTS / "promote_discussion_to_issue.py"), run_name="__main__"
        )

    assert exc.value.code == (
        "promote_discussion_to_issue.py: requires the leyline plugin, "
        "which is not installed"
    )


@pytest.mark.unit
def test_promote_import_without_leyline_raises_import_error(
    without_leyline: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An importer handles the missing peer itself.

    GIVEN leyline cannot be imported
    WHEN promote_discussion_to_issue is imported as a module
    THEN ImportError propagates and the process does not exit.
    """
    monkeypatch.syspath_prepend(str(SCRIPTS))

    with pytest.raises(ImportError, match="leyline"):
        _load("promote_discussion_to_issue.py", "promote_no_leyline", monkeypatch)
