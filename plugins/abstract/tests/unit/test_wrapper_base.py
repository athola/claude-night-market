"""Tests for wrapper_base module — _detect_breaking_changes and helpers.

SuperpowerWrapper was removed (ABS-006): 0 production consumers as of 2026-03.
"""

from __future__ import annotations

import ast as _ast
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from abstract.wrapper_base import (
    _compare_function_sigs,
    _compare_symbols,
    _detect_breaking_changes,
    _extract_param_names,
    _extract_public_symbols,
    _unparse_annotation,
)

# ---------------------------------------------------------------------------
# _detect_breaking_changes
# ---------------------------------------------------------------------------


class TestDetectBreakingChanges:
    """_detect_breaking_changes detects API changes between working tree and HEAD."""

    @pytest.mark.unit
    def test_empty_list_returns_empty(self):
        """Given empty file list, returns empty list."""
        result = _detect_breaking_changes([])
        assert result == []

    @pytest.mark.unit
    def test_nonexistent_file_returns_empty(self, tmp_path):
        """Given a path that doesn't exist, returns empty list."""
        result = _detect_breaking_changes([str(tmp_path / "missing.py")])
        assert result == []

    @pytest.mark.unit
    def test_valid_python_file_no_git_returns_empty(self, tmp_path):
        """Given a valid Python file with no git history, returns empty list."""
        py_file = tmp_path / "module.py"
        py_file.write_text("def hello():\n    return 'hello'\n")
        result = _detect_breaking_changes([str(py_file)])
        assert result == []

    @pytest.mark.unit
    def test_non_python_file_skipped(self, tmp_path):
        """Given a non-Python file, it is skipped."""
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("hello")
        result = _detect_breaking_changes([str(txt_file)])
        assert result == []

    @pytest.mark.unit
    def test_syntax_error_file_returns_empty(self, tmp_path):
        """Given a Python file with syntax errors, returns empty list."""
        py_file = tmp_path / "bad.py"
        py_file.write_text("def broken(\n")
        result = _detect_breaking_changes([str(py_file)])
        assert result == []


# ---------------------------------------------------------------------------
# Private helper function coverage
# ---------------------------------------------------------------------------


class TestExtractPublicSymbols:
    """_extract_public_symbols extracts public functions and classes from AST."""

    @pytest.mark.unit
    def test_extracts_public_function(self):
        """Public function is extracted with params and return type."""
        source = "def my_func(x: int, y: str) -> bool:\n    pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "my_func" in symbols
        assert symbols["my_func"]["kind"] == "function"
        assert "x" in symbols["my_func"]["params"]

    @pytest.mark.unit
    def test_skips_private_function(self):
        """Functions starting with _ are excluded."""
        source = "def _private(x): pass\ndef public(x): pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "_private" not in symbols
        assert "public" in symbols

    @pytest.mark.unit
    def test_extracts_public_class(self):
        """Public class is extracted."""
        source = "class MyClass:\n    pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "MyClass" in symbols
        assert symbols["MyClass"]["kind"] == "class"

    @pytest.mark.unit
    def test_skips_private_class(self):
        """Classes starting with _ are excluded."""
        source = "class _Private:\n    pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "_Private" not in symbols


class TestExtractParamNames:
    """_extract_param_names extracts parameter names from a FunctionDef AST node."""

    @pytest.mark.unit
    def test_regular_params_extracted(self):
        """Regular parameters (excluding self/cls) are extracted."""
        source = "def func(self, a, b): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert result == ["a", "b"]
        assert "self" not in result

    @pytest.mark.unit
    def test_cls_excluded(self):
        """'cls' parameter is excluded."""
        source = "def func(cls, a): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert "cls" not in result
        assert "a" in result

    @pytest.mark.unit
    def test_vararg_extracted(self):
        """*args parameter is extracted with * prefix."""
        source = "def func(*args): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert "*args" in result

    @pytest.mark.unit
    def test_kwarg_extracted(self):
        """**kwargs parameter is extracted with ** prefix."""
        source = "def func(**kwargs): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert "**kwargs" in result

    @pytest.mark.unit
    def test_kwonly_args_extracted(self):
        """Keyword-only arguments are extracted."""
        source = "def func(*, key_only): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert "key_only" in result


class TestUnparseAnnotation:
    """_unparse_annotation converts AST annotation nodes to strings."""

    @pytest.mark.unit
    def test_none_returns_none(self):
        """None input returns None."""
        assert _unparse_annotation(None) is None

    @pytest.mark.unit
    def test_simple_annotation_returns_string(self):
        """A simple annotation node returns its string representation."""
        source = "def func() -> int: pass\n"
        tree = _ast.parse(source)
        func_node = tree.body[0]
        result = _unparse_annotation(func_node.returns)
        assert result == "int"

    @pytest.mark.unit
    def test_complex_annotation_returns_string(self):
        """A complex annotation is unparsed correctly."""
        source = "def func() -> list[str]: pass\n"
        tree = _ast.parse(source)
        func_node = tree.body[0]
        result = _unparse_annotation(func_node.returns)
        assert "str" in result

    @pytest.mark.unit
    def test_memory_error_propagates(self):
        """MemoryError must not be swallowed; only ValueError/TypeError are caught."""
        node = MagicMock()
        with patch("abstract.wrapper_base.ast.unparse", side_effect=MemoryError("oom")):
            with pytest.raises(MemoryError):
                _unparse_annotation(node)


class TestCompareSymbols:
    """_compare_symbols detects removed symbols and changed signatures."""

    @pytest.mark.unit
    def test_removed_function_detected(self):
        """A function present in old but absent in new is flagged as removed."""
        old = {"old_func": {"kind": "function", "params": ["x"], "return_type": None}}
        new: dict = {}
        changes: list = []
        _compare_symbols("file.py", old, new, changes)
        assert len(changes) == 1
        assert changes[0]["type"] == "removed"
        assert changes[0]["name"] == "old_func"

    @pytest.mark.unit
    def test_class_removal_detected(self):
        """A class removed from public API is flagged."""
        old = {"OldClass": {"kind": "class", "params": [], "return_type": None}}
        new: dict = {}
        changes: list = []
        _compare_symbols("file.py", old, new, changes)
        assert changes[0]["type"] == "removed"

    @pytest.mark.unit
    def test_unchanged_function_no_changes(self):
        """Identical old and new function generates no changes."""
        sym = {"kind": "function", "params": ["a", "b"], "return_type": "int"}
        old = {"func": sym}
        new = {"func": sym}
        changes: list = []
        _compare_symbols("file.py", old, new, changes)
        assert changes == []

    @pytest.mark.unit
    def test_non_function_kind_skips_sig_comparison(self):
        """If one side is a class, signature comparison is skipped."""
        old = {"MyClass": {"kind": "class", "params": [], "return_type": None}}
        new = {"MyClass": {"kind": "function", "params": [], "return_type": None}}
        changes: list = []
        _compare_symbols("file.py", old, new, changes)
        # Class->function is kind mismatch; no sig comparison, no removal
        assert changes == []


class TestCompareFunctionSigs:
    """_compare_function_sigs detects parameter and return type changes."""

    @pytest.mark.unit
    def test_removed_parameter_detected(self):
        """Removing a parameter is flagged."""
        old = {"kind": "function", "params": ["a", "b"], "return_type": None}
        new = {"kind": "function", "params": ["a"], "return_type": None}
        changes: list = []
        _compare_function_sigs("file.py", "func", old, new, changes)
        types = [c["type"] for c in changes]
        assert "parameter_removed" in types

    @pytest.mark.unit
    def test_reordered_parameters_detected(self):
        """Reordering parameters is flagged."""
        old = {"kind": "function", "params": ["a", "b"], "return_type": None}
        new = {"kind": "function", "params": ["b", "a"], "return_type": None}
        changes: list = []
        _compare_function_sigs("file.py", "func", old, new, changes)
        types = [c["type"] for c in changes]
        assert "parameters_reordered" in types

    @pytest.mark.unit
    def test_return_type_change_detected(self):
        """Changing return type is flagged when old type was non-None."""
        old = {"kind": "function", "params": [], "return_type": "int"}
        new = {"kind": "function", "params": [], "return_type": "str"}
        changes: list = []
        _compare_function_sigs("file.py", "func", old, new, changes)
        types = [c["type"] for c in changes]
        assert "return_type_changed" in types

    @pytest.mark.unit
    def test_none_old_return_type_not_flagged(self):
        """When old return type is None, change is not flagged."""
        old = {"kind": "function", "params": [], "return_type": None}
        new = {"kind": "function", "params": [], "return_type": "str"}
        changes: list = []
        _compare_function_sigs("file.py", "func", old, new, changes)
        types = [c["type"] for c in changes]
        assert "return_type_changed" not in types


class TestDetectBreakingChangesWithMockedGit:
    """_detect_breaking_changes uses git to compare HEAD vs working tree."""

    @pytest.mark.unit
    def test_removed_function_detected_via_git(self, tmp_path):
        """When git HEAD has more functions, removed ones are flagged."""
        py_file = tmp_path / "module.py"
        py_file.write_text("def remaining(x):\n    pass\n")

        # Git HEAD version had two functions
        old_source = "def remaining(x):\n    pass\ndef removed(y):\n    pass\n"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = old_source

        with patch("subprocess.run", return_value=mock_result):
            changes = _detect_breaking_changes([str(py_file)])

        change_types = [c["type"] for c in changes]
        assert "removed" in change_types

    @pytest.mark.unit
    def test_git_timeout_skips_file(self, tmp_path):
        """When git times out, file is skipped gracefully."""
        py_file = tmp_path / "module.py"
        py_file.write_text("def func(): pass\n")

        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(["git"], 10),
        ):
            result = _detect_breaking_changes([str(py_file)])

        assert result == []

    @pytest.mark.unit
    def test_old_syntax_error_skips_file(self, tmp_path):
        """When git HEAD content has a syntax error, file is skipped."""
        py_file = tmp_path / "module.py"
        py_file.write_text("def func(): pass\n")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "def broken(\n"  # Syntax error

        with patch("subprocess.run", return_value=mock_result):
            result = _detect_breaking_changes([str(py_file)])

        assert result == []
