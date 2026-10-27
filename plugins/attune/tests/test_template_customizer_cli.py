"""CLI contract for scripts/template_customizer.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import template_customizer

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "template_customizer.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.unit
def test_prints_the_paradigm_structure_with_the_module_substituted() -> None:
    """Each template path is printed with {module} filled in."""
    result = _run("--paradigm", "functional-core", "--module", "billing")

    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "Generated structure for functional-core:"
    assert "  - src/billing/core/domain.py" in lines
    assert not any("{module}" in line for line in lines)


@pytest.mark.unit
def test_unknown_paradigm_exits_nonzero_naming_it() -> None:
    """A paradigm missing from the YAML fails loudly, printing no structure."""
    result = _run("--paradigm", "no-such-paradigm", "--module", "billing")

    assert result.returncode != 0
    assert "Unknown paradigm: no-such-paradigm" in result.stderr
    assert result.stdout == ""


@pytest.mark.unit
def test_missing_templates_file_raises_naming_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A deleted architecture_templates.yaml is an error, not an empty catalog."""
    missing = tmp_path / "architecture_templates.yaml"
    monkeypatch.setattr(template_customizer, "TEMPLATES_FILE", missing)

    with pytest.raises(FileNotFoundError, match=str(missing)):
        template_customizer.load_templates()


@pytest.mark.unit
def test_language_without_a_structure_is_rejected() -> None:
    """A paradigm with no layout for the language fails naming both."""
    customizer = template_customizer.TemplateCustomizer(
        "layered", "billing", language="cobol"
    )

    with pytest.raises(ValueError, match="No structure defined for cobol in layered"):
        customizer.generate_structure()


@pytest.mark.unit
def test_main_prints_structure_in_process(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """main() prints each path of the chosen paradigm for the given module."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["template_customizer.py", "--paradigm", "hexagonal", "--module", "shop"],
    )
    template_customizer.main()

    out = capsys.readouterr().out
    assert out.startswith("Generated structure for hexagonal:")
    assert "src/shop/domain/models.py" in out


@pytest.mark.unit
@pytest.mark.parametrize(
    "render",
    ["generate_architecture_readme", "generate_architecture_adr"],
)
def test_generated_docs_reference_the_paradigm_skill_by_its_plugin_name(
    render: str,
) -> None:
    """The paradigm skills ship in archetypes, so a reference needs that prefix."""
    customizer = template_customizer.TemplateCustomizer("hexagonal", "shop")
    skill_dir = (
        Path(__file__).resolve().parents[2]
        / "archetypes"
        / "skills"
        / "architecture-paradigm-hexagonal"
    )

    text = getattr(customizer, render)()

    assert skill_dir.is_dir()
    assert "`Skill(archetypes:architecture-paradigm-hexagonal)`" in text
