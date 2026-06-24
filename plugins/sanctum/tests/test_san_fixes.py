"""Tests for SAN code refinement findings.

Covers: SAN-002, SAN-004 through SAN-019.
TDD RED tests are written first; GREEN after implementation.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Script loader helpers
# ---------------------------------------------------------------------------

SCRIPTS = Path(__file__).parent.parent / "scripts"


def _load(name: str):
    """Load a script module by stem name."""
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_san_{name}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# SAN-006: read_skill_content – narrow except Exception
# ---------------------------------------------------------------------------


class TestSAN006ReadSkillContentNarrowException:
    """read_skill_content must not swallow non-OSError exceptions.

    GIVEN read_skill_content encounters a non-OSError during file open
    WHEN the exception escapes OSError and UnicodeDecodeError
    THEN it propagates to the caller (not silently caught).
    """

    def test_runtime_error_propagates_after_narrow(self, tmp_path: Path) -> None:
        meta = _load("meta_evaluation")
        evaluator = meta.MetaEvaluator(tmp_path)

        skill_dir = tmp_path / "abstract" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# content\n", encoding="utf-8")

        with patch.object(Path, "open", side_effect=RuntimeError("unexpected")):
            with pytest.raises(RuntimeError, match="unexpected"):
                evaluator.read_skill_content(skill_dir)


# ---------------------------------------------------------------------------
# SAN-011: _validate_registration – split into query + mutate
# ---------------------------------------------------------------------------


class TestSAN011ValidateRegistrationSplit:
    """_validate_registration returns warnings list; does not mutate plugin_data.

    GIVEN a plugin with hook discrepancies
    WHEN _validate_registration is called
    THEN it returns a list[str] of MANUAL messages
    AND plugin_data is not mutated.
    """

    def _make_registrar(self, tmp_path: Path):
        mod = _load("update_plugin_registrations")
        registrar = mod.PluginRegistrationAuditor(tmp_path)
        return registrar, mod

    def test_returns_list_not_tuple(self, tmp_path: Path) -> None:
        registrar, _ = self._make_registrar(tmp_path)
        plugin_path = tmp_path / "myplugin"
        plugin_path.mkdir()
        (plugin_path / "hooks").mkdir()
        (plugin_path / "hooks" / "hooks.json").write_text("[]")
        plugin_data: dict = {"hooks": "./hooks/hooks.json"}
        registrar.discrepancies["myplugin"] = {
            "missing": {"hooks": ["session-start.sh"]},
            "stale": {},
        }
        result = registrar._validate_registration("myplugin", plugin_path, plugin_data)
        assert isinstance(result, list), f"expected list, got {type(result)}"

    def test_hook_warnings_in_returned_list(self, tmp_path: Path) -> None:
        registrar, _ = self._make_registrar(tmp_path)
        plugin_path = tmp_path / "myplugin"
        plugin_path.mkdir()
        (plugin_path / "hooks").mkdir()
        (plugin_path / "hooks" / "hooks.json").write_text("[]")
        plugin_data: dict = {"hooks": "./hooks/hooks.json"}
        registrar.discrepancies["myplugin"] = {
            "missing": {"hooks": ["session-start.sh"]},
            "stale": {},
        }
        warnings = registrar._validate_registration(
            "myplugin", plugin_path, plugin_data
        )
        assert any("session-start.sh" in w for w in warnings)

    def test_does_not_mutate_plugin_data_for_hooks(self, tmp_path: Path) -> None:
        registrar, _ = self._make_registrar(tmp_path)
        plugin_path = tmp_path / "myplugin"
        plugin_path.mkdir()
        (plugin_path / "hooks").mkdir()
        (plugin_path / "hooks" / "hooks.json").write_text("[]")
        plugin_data: dict = {"hooks": "./hooks/hooks.json"}
        original_data = json.loads(json.dumps(plugin_data))
        registrar.discrepancies["myplugin"] = {
            "missing": {"hooks": ["session-start.sh"]},
            "stale": {},
        }
        registrar._validate_registration("myplugin", plugin_path, plugin_data)
        assert plugin_data == original_data, "plugin_data must not be mutated for hooks"


# ---------------------------------------------------------------------------
# SAN-016: _check_bdd_compliance – regex over-matches inside classes
# ---------------------------------------------------------------------------


class TestSAN016BDDRegexNoOvermatch:
    """_check_bdd_compliance must not merge bodies of adjacent methods in a class.

    GIVEN a test class with two methods, each with their own docstring
    WHEN _check_bdd_compliance runs
    THEN each method is evaluated independently.
    """

    def _make_checker(self, tmp_path: Path):
        mod = _load("quality_checker")
        test_file = tmp_path / "test_example.py"
        test_file.write_text("x = 1\n")
        checker = mod.TestQualityChecker(test_file)
        return checker, mod

    def test_adjacent_class_methods_evaluated_independently(
        self, tmp_path: Path
    ) -> None:
        checker, _ = self._make_checker(tmp_path)
        # First method has all BDD keywords; second has none.
        # If regex over-matches, second's body folds into first's match
        # and no BDD warning is raised for second.
        content = (
            "class TestSomething:\n"
            "    def test_first_method(self):\n"
            '        """docstring.\n'
            "        GIVEN something WHEN it runs THEN it works AND it passes\n"
            '        """\n'
            "        assert True\n"
            "\n"
            "    def test_second_method(self):\n"
            '        """docstring without any bdd keywords.\n'
            '        """\n'
            "        assert True\n"
        )
        analysis: dict = {
            "bdd_compliance": [],
            "assertion_issues": [],
            "documentation": [],
            "structure_issues": [],
            "naming_issues": [],
        }
        checker._check_bdd_compliance(content, analysis)
        missing_bdd = [
            i for i in analysis["bdd_compliance"] if "second_method" in i.message
        ]
        assert missing_bdd, (
            "_check_bdd_compliance did not flag test_second_method (regex over-match)"
        )
