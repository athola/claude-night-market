"""End-to-end runs of ``attune_arch_init.main`` in a temporary project.

The interactive prompts are driven through ``input``; git runs for real
inside ``tmp_path``. Nothing here mocks the initializer's own helpers.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

import attune_arch_init

# web-api, moderate, 5-15, python, no framework, defaults for the rest.
CONTEXT_ANSWERS = ["1", "2", "2", "1", "", "", "", ""]


def _answers(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> Iterator[str]:
    feed = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(feed))
    return feed


def _run_main(
    monkeypatch: pytest.MonkeyPatch, project: Path, *flags: str, name: str = "my-app"
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["attune_arch_init.py", "--path", str(project), "--name", name, *flags],
    )
    attune_arch_init.main()


@pytest.mark.integration
def test_forced_architecture_scaffolds_its_directories_and_docs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--arch layered with --accept-recommendation writes structure, ADR, session."""
    _answers(monkeypatch, CONTEXT_ANSWERS)

    _run_main(
        monkeypatch,
        tmp_path,
        "--arch",
        "layered",
        "--no-research",
        "--accept-recommendation",
    )

    readme = (tmp_path / "ARCHITECTURE.md").read_text()
    assert "Layered" in readme
    assert "src/my_app/" in readme
    adr = (tmp_path / "docs" / "adr" / "001-architecture-paradigm.md").read_text()
    assert "Layered" in adr
    session = json.loads((tmp_path / ".attune" / "arch-init-session.json").read_text())
    assert session
    assert (tmp_path / ".git").is_dir()
    assert any(p.is_dir() for p in (tmp_path / "src" / "my_app").iterdir())


@pytest.mark.integration
def test_paradigm_without_a_structure_template_still_writes_docs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A paradigm the YAML has no layout for creates no extra dirs, and says so."""
    _answers(monkeypatch, CONTEXT_ANSWERS)

    _run_main(
        monkeypatch,
        tmp_path,
        "--arch",
        "cqrs-es",
        "--no-research",
        "--accept-recommendation",
    )

    out = capsys.readouterr().out
    assert "Created 0 architecture-specific directories" in out
    assert "No directory template for cqrs-es" in out
    assert (
        "Cqrs Es"
        in (tmp_path / "docs" / "adr" / "001-architecture-paradigm.md").read_text()
    )
    assert (tmp_path / "ARCHITECTURE.md").is_file()


@pytest.mark.integration
def test_interactive_run_prints_research_queries_and_asks_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without --no-research the queries are printed; a 'y' accepts the pick."""
    _answers(monkeypatch, [*CONTEXT_ANSWERS, "maybe", "y"])

    _run_main(monkeypatch, tmp_path)

    out = capsys.readouterr().out
    assert 'Command: WebSearch("' in out
    assert "Please enter 'y' or 'n'" in out
    assert (tmp_path / "ARCHITECTURE.md").is_file()


@pytest.mark.integration
def test_declining_the_recommendation_exits_zero_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An 'n' at the confirmation prompt cancels before any file is created."""
    _answers(monkeypatch, [*CONTEXT_ANSWERS, "n"])

    with pytest.raises(SystemExit) as exc:
        _run_main(monkeypatch, tmp_path, "--no-research")

    assert exc.value.code == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.integration
def test_research_file_steers_the_recommendation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Avoiding the matrix pick in --research-file moves the recommendation.

    For web-api, moderate, 5-15 the matrix picks modular-monolith; research
    that avoids it leaves hexagonal, which then shapes the scaffold.
    """
    research = tmp_path / "research.json"
    research.write_text(json.dumps({"avoid": ["modular-monolith"]}))
    project = tmp_path / "proj"
    project.mkdir()
    _answers(monkeypatch, CONTEXT_ANSWERS)

    _run_main(
        monkeypatch,
        project,
        "--research-file",
        str(research),
        "--accept-recommendation",
    )

    assert "Auto-accepted: hexagonal" in capsys.readouterr().out
    assert "Hexagonal" in (project / "ARCHITECTURE.md").read_text()


@pytest.mark.integration
def test_a_dotted_project_name_scaffolds_an_importable_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--name my.app writes src/my_app/, not src/my.app/."""
    _answers(monkeypatch, CONTEXT_ANSWERS)

    _run_main(
        monkeypatch,
        tmp_path,
        "--arch",
        "layered",
        "--no-research",
        "--accept-recommendation",
        name="my.app",
    )

    assert (tmp_path / "src" / "my_app").is_dir()
    assert not (tmp_path / "src" / "my.app").exists()
