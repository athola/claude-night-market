"""Tests for iron_law Nen Court validator (issue #406).

Feature: Verify tests are committed before implementations.

As the Night Market vow enforcement system
I want a Nen Court validator that audits commit order
So that the Iron Law (no impl without failing test first) graduates
from Soft to Nen Court enforcement.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def validator_module():
    """Import iron_law validator via importlib."""
    validators_path = Path(__file__).resolve().parents[3] / "validators"
    module_path = validators_path / "iron_law.py"
    spec = importlib.util.spec_from_file_location("iron_law", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["iron_law"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestImplToTestPath:
    """Feature: Map an implementation file to its expected test file.

    As the validator
    I want to derive the test path from an implementation path
    So that I can pair them for commit-order analysis.
    """

    @pytest.mark.unit
    def test_python_src_module_maps_to_tests_dir(self, validator_module):
        """src/foo/bar.py -> tests/foo/test_bar.py."""
        result = validator_module.impl_to_test_paths("src/foo/bar.py")
        assert "tests/foo/test_bar.py" in result

    @pytest.mark.unit
    def test_python_unit_test_path_alternative(self, validator_module):
        """src/foo.py -> tests/unit/test_foo.py is also a valid candidate."""
        result = validator_module.impl_to_test_paths("src/foo.py")
        assert any("test_foo.py" in p for p in result)

    @pytest.mark.unit
    def test_test_file_returns_empty(self, validator_module):
        """A path that is itself a test returns no candidates."""
        result = validator_module.impl_to_test_paths("tests/test_foo.py")
        assert result == []

    @pytest.mark.unit
    def test_non_python_returns_empty(self, validator_module):
        """A markdown or yaml file has no implementation/test pairing."""
        result = validator_module.impl_to_test_paths("docs/readme.md")
        assert result == []


class TestAnalyzeCommitOrder:
    """Feature: Detect impl-before-test violations from commit timestamps.

    As the validator
    I want to compare first-touch timestamps for impl vs. test files
    So that violations can be reported with concrete evidence.
    """

    @pytest.mark.unit
    def test_test_first_then_impl_passes(self, validator_module):
        """Test committed before impl in different commits -> pass."""
        commits = [
            {"sha": "aaa", "ts": 100, "files": ["tests/test_foo.py"]},
            {"sha": "bbb", "ts": 200, "files": ["src/foo.py"]},
        ]
        result = validator_module.analyze_commit_order(commits)
        assert result["verdict"] == "pass"

    @pytest.mark.unit
    def test_impl_first_then_test_violates(self, validator_module):
        """Impl committed before test -> violation."""
        commits = [
            {"sha": "aaa", "ts": 100, "files": ["src/foo.py"]},
            {"sha": "bbb", "ts": 200, "files": ["tests/test_foo.py"]},
        ]
        result = validator_module.analyze_commit_order(commits)
        assert result["verdict"] == "violation"
        ev_files = {ev["impl_file"] for ev in result["evidence"]}
        assert "src/foo.py" in ev_files

    @pytest.mark.unit
    def test_test_and_impl_same_commit_passes(self, validator_module):
        """Both touched in the same commit is acceptable (test-first
        commit could have included both files).
        """
        commits = [
            {
                "sha": "aaa",
                "ts": 100,
                "files": ["src/foo.py", "tests/test_foo.py"],
            },
        ]
        result = validator_module.analyze_commit_order(commits)
        assert result["verdict"] == "pass"

    @pytest.mark.unit
    def test_impl_without_test_inconclusive(self, validator_module):
        """Impl with no matching test in any commit -> inconclusive."""
        commits = [
            {"sha": "aaa", "ts": 100, "files": ["src/foo.py"]},
        ]
        result = validator_module.analyze_commit_order(commits)
        assert result["verdict"] == "inconclusive"
        assert any("no test" in str(ev).lower() for ev in result["evidence"])

    @pytest.mark.unit
    def test_multiple_impls_partial_violation(self, validator_module):
        """Some files comply, one doesn't -> overall violation, with the
        offending file in evidence.
        """
        commits = [
            # foo: test-first (good)
            {"sha": "a", "ts": 100, "files": ["tests/test_foo.py"]},
            {"sha": "b", "ts": 200, "files": ["src/foo.py"]},
            # bar: impl-first (bad)
            {"sha": "c", "ts": 300, "files": ["src/bar.py"]},
            {"sha": "d", "ts": 400, "files": ["tests/test_bar.py"]},
        ]
        result = validator_module.analyze_commit_order(commits)
        assert result["verdict"] == "violation"
        ev_files = {ev["impl_file"] for ev in result["evidence"]}
        assert "src/bar.py" in ev_files
        assert "src/foo.py" not in ev_files

    @pytest.mark.unit
    def test_empty_commits_passes(self, validator_module):
        """Empty range trivially passes."""
        result = validator_module.analyze_commit_order([])
        assert result["verdict"] == "pass"


class TestCliEntry:
    """Feature: Validator runs as a standalone CLI script."""

    @pytest.mark.unit
    def test_main_with_explicit_commits(self, validator_module, capsys):
        """main() with explicit commits payload returns verdict JSON."""
        payload = json.dumps(
            {
                "commits": [
                    {"sha": "a", "ts": 100, "files": ["tests/test_x.py"]},
                    {"sha": "b", "ts": 200, "files": ["src/x.py"]},
                ]
            }
        )
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["verdict"] == "pass"

    @pytest.mark.unit
    def test_main_violation_exits_one(self, validator_module, capsys):
        payload = json.dumps(
            {
                "commits": [
                    {"sha": "a", "ts": 100, "files": ["src/x.py"]},
                    {"sha": "b", "ts": 200, "files": ["tests/test_x.py"]},
                ]
            }
        )
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["verdict"] == "violation"

    @pytest.mark.unit
    def test_main_inconclusive_exit_two(self, validator_module, capsys):
        payload = json.dumps(
            {"commits": [{"sha": "a", "ts": 100, "files": ["src/x.py"]}]}
        )
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 2
        out = json.loads(capsys.readouterr().out)
        assert out["verdict"] == "inconclusive"

    @pytest.mark.unit
    def test_main_malformed_input_inconclusive(self, validator_module, capsys):
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 2
