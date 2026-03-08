"""Tests for plugin dependency map generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/generate_dependency_map.py")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestDependencyMapGenerator:
    """Test dependency map generation."""

    def test_script_runs_successfully(self) -> None:
        """Given the script exists, when run, then exit 0."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stderr

    def test_output_is_valid_json(self) -> None:
        """Given the script runs, when output captured,
        then it is valid JSON."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert "version" in data
        assert "dependencies" in data
        assert "reverse_index" in data

    def test_abstract_is_universal_dependency(self) -> None:
        """Given abstract provides Make includes to all,
        when map generated, then abstract has wildcard."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert "abstract" in data["dependencies"]
        assert data["dependencies"]["abstract"]["dependents"] == ["*"]

    def test_conjure_depends_on_leyline(self) -> None:
        """Given conjure optionally imports leyline,
        when map generated, then reverse_index shows it."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        assert "leyline" in data["reverse_index"].get("conjure", [])

    def test_all_plugins_in_reverse_index(self) -> None:
        """Given 17 plugins exist, when map generated,
        then all non-abstract plugins appear in reverse_index."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stdout"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        data = json.loads(result.stdout)
        # abstract itself is a dependency, not a dependent
        assert len(data["reverse_index"]) >= 16
