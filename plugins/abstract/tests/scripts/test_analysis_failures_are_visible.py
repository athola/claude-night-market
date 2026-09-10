"""A skill that fails to analyze must not vanish from the report.

``token_estimator`` and ``skill_analyzer`` each caught every exception
around one file and called ``logger.debug``. The root logger defaults to
WARNING, so nothing was emitted: a malformed skill dropped out of the
results and the shortened list looked complete. ``validate_budget.py``
writes to stderr for the same failure, which is the behavior copied here.

The sweep still continues past a bad file. One unparseable skill should
not cost the whole report; it should just be impossible to miss.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "analyzer",
    [
        ("token_estimator", "TokenEstimator", "analyze_directory"),
        ("skill_analyzer", "SkillAnalyzer", "analyze_directory"),
    ],
    ids=lambda value: value[0],
)
def test_an_unanalyzable_skill_is_reported_on_stderr(
    analyzer: tuple[str, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The failure reaches stderr rather than a silent debug call."""
    module_name, class_name, method = analyzer
    module = _load(module_name)
    skill = tmp_path / "broken" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: broken\n---\n\nBody.\n", encoding="utf-8")

    instance = getattr(module, class_name)()

    def explode(*args: object, **kwargs: object) -> None:
        raise ValueError("unparseable frontmatter")

    monkeypatch.setattr(instance, "analyze_file", explode)
    results = getattr(instance, method)(tmp_path)

    assert results == []
    captured = capsys.readouterr()
    assert "broken" in captured.err, (
        "the failure produced no stderr output, so a malformed skill drops "
        f"out of the report silently. stderr was: {captured.err!r}"
    )
