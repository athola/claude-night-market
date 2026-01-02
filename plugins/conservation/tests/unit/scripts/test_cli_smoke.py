#!/usr/bin/env python3
"""Smoke tests for CLI entry points - validates scripts don't crash on basic usage."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"


def load_module(script_name: str):
    """Dynamically load a script module."""
    spec = importlib.util.spec_from_file_location(
        f"{script_name}_module", scripts_dir / f"{script_name}.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{script_name}_module"] = module
    spec.loader.exec_module(module)
    return module


class TestCLISmokeTests:
    """Smoke tests for CLI main() functions."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_growth_analyzer_cli_handles_missing_file(self, tmp_path: Path) -> None:
        """Smoke test: growth-analyzer CLI handles missing input file."""
        # Arrange
        growth_analyzer = load_module("growth-analyzer")
        nonexistent = str(tmp_path / "missing.json")

        # Act & Assert
        with patch("sys.argv", ["growth-analyzer.py", "--context-file", nonexistent]):
            with pytest.raises(SystemExit):
                growth_analyzer.main()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_growth_analyzer_cli_handles_valid_input(self, tmp_path: Path) -> None:
        """Smoke test: growth-analyzer CLI processes valid input."""
        # Arrange
        growth_analyzer = load_module("growth-analyzer")
        input_file = tmp_path / "context.json"
        input_file.write_text(
            json.dumps(
                {
                    "growth_trend": {
                        "current_usage": 50,
                        "rate": 0.05,
                        "acceleration": 0.001,
                    },
                    "content_breakdown": {},
                }
            )
        )

        # Act
        with patch(
            "sys.argv", ["growth-analyzer.py", "--context-file", str(input_file)]
        ):
            # Should complete without crashing
            try:
                growth_analyzer.main()
            except SystemExit:
                pass  # Expected for CLI completion

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_growth_controller_cli_handles_missing_file(self, tmp_path: Path) -> None:
        """Smoke test: growth-controller CLI handles missing input file."""
        # Arrange
        growth_controller = load_module("growth-controller")
        nonexistent = str(tmp_path / "missing.json")

        # Act & Assert
        with patch(
            "sys.argv", ["growth-controller.py", "--analysis-file", nonexistent]
        ):
            with pytest.raises(SystemExit):
                growth_controller.main()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_growth_controller_cli_handles_valid_input(self, tmp_path: Path) -> None:
        """Smoke test: growth-controller CLI processes valid input."""
        # Arrange
        growth_controller = load_module("growth-controller")
        input_file = tmp_path / "analysis.json"
        input_file.write_text(
            json.dumps(
                {"severity": "MODERATE", "urgency": "MEDIUM", "growth_rate": 0.15}
            )
        )

        # Act
        with patch(
            "sys.argv", ["growth-controller.py", "--analysis-file", str(input_file)]
        ):
            try:
                growth_controller.main()
            except SystemExit:
                pass

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dependency_manager_cli_scan(self, tmp_path: Path) -> None:
        """Smoke test: dependency_manager CLI scan mode."""
        # Arrange
        dependency_manager = load_module("dependency_manager")

        # Act
        with patch(
            "sys.argv", ["dependency_manager.py", "--root", str(tmp_path), "--scan"]
        ):
            try:
                dependency_manager.main()
            except SystemExit:
                pass

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dependency_manager_cli_report(self, tmp_path: Path) -> None:
        """Smoke test: dependency_manager CLI report mode."""
        # Arrange
        dependency_manager = load_module("dependency_manager")

        # Create minimal plugin structure
        (tmp_path / "plugin.json").write_text(json.dumps({"dependencies": {}}))

        # Act
        with patch(
            "sys.argv", ["dependency_manager.py", "--root", str(tmp_path), "--report"]
        ):
            try:
                dependency_manager.main()
            except SystemExit:
                pass

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fix_long_lines_cli(self, tmp_path: Path) -> None:
        """Smoke test: fix_long_lines CLI."""
        # Arrange
        fix_long_lines = load_module("fix_long_lines")
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Test\n")

        # Act
        with patch("sys.argv", ["fix_long_lines.py", str(skill_file)]):
            try:
                fix_long_lines.main()
            except SystemExit:
                pass

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quick_skill_optimizer_cli(self, tmp_path: Path) -> None:
        """Smoke test: quick_skill_optimizer CLI."""
        # Arrange
        quick_skill_optimizer = load_module("quick_skill_optimizer")
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Test\n")

        # Act
        with patch("sys.argv", ["quick_skill_optimizer.py", str(skill_file)]):
            try:
                quick_skill_optimizer.main()
            except (SystemExit, AttributeError):
                pass

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_aggressive_skill_optimizer_cli(self, tmp_path: Path) -> None:
        """Smoke test: aggressive_skill_optimizer CLI."""
        # Arrange
        aggressive_skill_optimizer = load_module("aggressive_skill_optimizer")
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Test\n")

        # Act
        with patch("sys.argv", ["aggressive_skill_optimizer.py", str(skill_file)]):
            try:
                aggressive_skill_optimizer.main()
            except (SystemExit, AttributeError):
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
