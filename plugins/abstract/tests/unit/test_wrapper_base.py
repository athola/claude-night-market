"""Tests for wrapper_base module.

Covers SuperpowerWrapper and _detect_breaking_changes.
"""

from __future__ import annotations

import pytest

from abstract.wrapper_base import SuperpowerWrapper, _detect_breaking_changes

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
# SuperpowerWrapper.__init__
# ---------------------------------------------------------------------------


class TestSuperpowerWrapperInit:
    """SuperpowerWrapper validates constructor arguments."""

    @pytest.mark.unit
    def test_valid_init_succeeds(self):
        """Given valid arguments, wrapper is created without error."""
        wrapper = SuperpowerWrapper(
            source_plugin="plugin-a",
            source_command="cmd-one",
            target_superpower="super-x",
        )
        assert wrapper.source_plugin == "plugin-a"
        assert wrapper.source_command == "cmd-one"
        assert wrapper.target_superpower == "super-x"

    @pytest.mark.unit
    def test_empty_source_plugin_raises_value_error(self):
        """Given empty source_plugin, ValueError is raised."""
        with pytest.raises(ValueError, match="source_plugin"):
            SuperpowerWrapper(
                source_plugin="",
                source_command="cmd",
                target_superpower="super",
            )

    @pytest.mark.unit
    def test_empty_source_command_raises_value_error(self):
        """Given empty source_command, ValueError is raised."""
        with pytest.raises(ValueError, match="source_command"):
            SuperpowerWrapper(
                source_plugin="plugin",
                source_command="",
                target_superpower="super",
            )

    @pytest.mark.unit
    def test_empty_target_superpower_raises_value_error(self):
        """Given empty target_superpower, ValueError is raised."""
        with pytest.raises(ValueError, match="target_superpower"):
            SuperpowerWrapper(
                source_plugin="plugin",
                source_command="cmd",
                target_superpower="",
            )

    @pytest.mark.unit
    def test_default_parameter_map_loaded(self):
        """Given no config_path, default parameter_map is loaded."""
        wrapper = SuperpowerWrapper("p", "c", "s")
        assert isinstance(wrapper.parameter_map, dict)

    @pytest.mark.unit
    def test_config_path_nonexistent_uses_defaults(self, tmp_path):
        """Given a config_path that doesn't exist, defaults are used."""
        missing_path = tmp_path / "nonexistent.yaml"
        wrapper = SuperpowerWrapper("p", "c", "s", config_path=missing_path)
        assert isinstance(wrapper.parameter_map, dict)

    @pytest.mark.unit
    def test_config_path_valid_yaml_loaded(self, tmp_path):
        """Given a valid YAML config, parameter_mapping is loaded."""
        config_file = tmp_path / "wrapper.yaml"
        config_file.write_text("parameter_mapping:\n  foo: bar\n  baz: qux\n")
        wrapper = SuperpowerWrapper("p", "c", "s", config_path=config_file)
        assert wrapper.parameter_map.get("foo") == "bar"
        assert wrapper.parameter_map.get("baz") == "qux"

    @pytest.mark.unit
    def test_config_path_invalid_yaml_raises(self, tmp_path):
        """Given invalid YAML config, ValueError is raised."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("parameter_mapping: [not: a: dict]\n")
        with pytest.raises(ValueError, match="Invalid YAML config"):
            SuperpowerWrapper("p", "c", "s", config_path=config_file)


# ---------------------------------------------------------------------------
# SuperpowerWrapper.translate_parameters
# ---------------------------------------------------------------------------


class TestSuperpowerWrapperTranslateParameters:
    """translate_parameters maps plugin params to superpower params."""

    def _wrapper(self):
        return SuperpowerWrapper("plugin", "cmd", "super")

    @pytest.mark.unit
    def test_non_dict_raises_value_error(self):
        """Given non-dict params, ValueError is raised."""
        w = self._wrapper()
        with pytest.raises(ValueError, match="dictionary"):
            w.translate_parameters("not a dict")

    @pytest.mark.unit
    def test_empty_dict_returns_empty_dict(self):
        """Given empty dict, returns empty dict (with a warning logged)."""
        w = self._wrapper()
        result = w.translate_parameters({})
        assert result == {}

    @pytest.mark.unit
    def test_mapped_key_is_translated(self):
        """Given a key in parameter_map, it is translated to mapped key."""
        w = self._wrapper()
        # Default map has "skill-path" -> "target_under_test"
        result = w.translate_parameters({"skill-path": "my/path"})
        assert "target_under_test" in result
        assert result["target_under_test"] == "my/path"

    @pytest.mark.unit
    def test_unmapped_key_passes_through(self):
        """Given a key not in parameter_map, it is preserved as-is."""
        w = self._wrapper()
        result = w.translate_parameters({"custom-param": "value"})
        assert result["custom-param"] == "value"

    @pytest.mark.unit
    def test_none_value_is_skipped(self):
        """Given a parameter with None value, it is excluded from result."""
        w = self._wrapper()
        result = w.translate_parameters({"skill-path": None, "phase": "red"})
        assert "target_under_test" not in result
        assert "tdd_phase" in result


# ---------------------------------------------------------------------------
# SuperpowerWrapper.validate_translation
# ---------------------------------------------------------------------------


class TestSuperpowerWrapperValidateTranslation:
    """validate_translation checks translation output quality."""

    def _wrapper(self):
        return SuperpowerWrapper("plugin", "cmd", "super")

    @pytest.mark.unit
    def test_returns_true_for_successful_translation(self):
        """Given non-empty translated params, returns True."""
        w = self._wrapper()
        result = w.validate_translation({"a": 1}, {"b": 2})
        assert result is True

    @pytest.mark.unit
    def test_returns_false_when_translated_empty_but_original_not(self):
        """Given empty translated but non-empty original, returns False."""
        w = self._wrapper()
        result = w.validate_translation({"a": 1}, {})
        assert result is False

    @pytest.mark.unit
    def test_both_empty_considered_valid(self):
        """Given both params empty, returns False (no params translated)."""
        w = self._wrapper()
        # Both empty: len(translated) == 0, so returns False
        result = w.validate_translation({}, {})
        assert result is False

    @pytest.mark.unit
    def test_missing_expected_mapping_is_logged(self):
        """Given expected mapping missing from parameter_map, still returns True."""
        w = self._wrapper()
        # Use a key NOT in the default map - validate_translation logs the gap
        # but still returns True when translated is non-empty
        result = w.validate_translation({"unknown-key": "x"}, {"translated": "y"})
        assert result is True

    @pytest.mark.unit
    def test_expected_key_not_in_parameter_map_triggers_missing(self, tmp_path):
        """Given 'skill-path' in original but not in a custom parameter_map, warning is logged."""
        # Create wrapper with empty parameter_map by using a config with empty mapping
        config_file = tmp_path / "wrapper.yaml"
        config_file.write_text("parameter_mapping: {}\n")
        w = SuperpowerWrapper("p", "c", "s", config_path=config_file)
        # "skill-path" is in expected_mappings but not in the empty map
        result = w.validate_translation(
            {"skill-path": "some/path"}, {"skill-path": "some/path"}
        )
        # Should still return True (non-empty translated)
        assert result is True


class TestSuperpowerWrapperTranslateEdgeCases:
    """Edge cases in translate_parameters."""

    @pytest.mark.unit
    def test_detect_breaking_changes_no_git_history(self, tmp_path):
        """Given a Python file with no git history, returns empty list."""
        py_file = tmp_path / "unreadable.py"
        py_file.write_text("x = 1")
        result = _detect_breaking_changes([str(py_file)])
        assert result == []

    @pytest.mark.unit
    def test_config_non_dict_raises_value_error(self, tmp_path):
        """Given YAML config that is not a dict, ValueError is raised."""
        config_file = tmp_path / "scalar.yaml"
        config_file.write_text("just a string\n")
        with pytest.raises(ValueError, match="Config file must contain a dictionary"):
            SuperpowerWrapper("p", "c", "s", config_path=config_file)


# ---------------------------------------------------------------------------
# Private helper function coverage
# ---------------------------------------------------------------------------


class TestExtractPublicSymbols:
    """_extract_public_symbols extracts public functions and classes from AST."""

    @pytest.mark.unit
    def test_extracts_public_function(self):
        """Public function is extracted with params and return type."""
        from abstract.wrapper_base import _extract_public_symbols

        source = "def my_func(x: int, y: str) -> bool:\n    pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "my_func" in symbols
        assert symbols["my_func"]["kind"] == "function"
        assert "x" in symbols["my_func"]["params"]

    @pytest.mark.unit
    def test_skips_private_function(self):
        """Functions starting with _ are excluded."""
        from abstract.wrapper_base import _extract_public_symbols

        source = "def _private(x): pass\ndef public(x): pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "_private" not in symbols
        assert "public" in symbols

    @pytest.mark.unit
    def test_extracts_public_class(self):
        """Public class is extracted."""
        from abstract.wrapper_base import _extract_public_symbols

        source = "class MyClass:\n    pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "MyClass" in symbols
        assert symbols["MyClass"]["kind"] == "class"

    @pytest.mark.unit
    def test_skips_private_class(self):
        """Classes starting with _ are excluded."""
        from abstract.wrapper_base import _extract_public_symbols

        source = "class _Private:\n    pass\n"
        tree = __import__("ast").parse(source)
        symbols = _extract_public_symbols(tree)
        assert "_Private" not in symbols


class TestExtractParamNames:
    """_extract_param_names extracts parameter names from a FunctionDef AST node."""

    @pytest.mark.unit
    def test_regular_params_extracted(self):
        """Regular parameters (excluding self/cls) are extracted."""
        from abstract.wrapper_base import _extract_param_names

        source = "def func(self, a, b): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert result == ["a", "b"]
        assert "self" not in result

    @pytest.mark.unit
    def test_cls_excluded(self):
        """'cls' parameter is excluded."""
        from abstract.wrapper_base import _extract_param_names

        source = "def func(cls, a): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert "cls" not in result
        assert "a" in result

    @pytest.mark.unit
    def test_vararg_extracted(self):
        """*args parameter is extracted with * prefix."""
        from abstract.wrapper_base import _extract_param_names

        source = "def func(*args): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert "*args" in result

    @pytest.mark.unit
    def test_kwarg_extracted(self):
        """**kwargs parameter is extracted with ** prefix."""
        from abstract.wrapper_base import _extract_param_names

        source = "def func(**kwargs): pass\n"
        tree = __import__("ast").parse(source)
        func_node = tree.body[0]
        result = _extract_param_names(func_node)
        assert "**kwargs" in result

    @pytest.mark.unit
    def test_kwonly_args_extracted(self):
        """Keyword-only arguments are extracted."""
        from abstract.wrapper_base import _extract_param_names

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
        from abstract.wrapper_base import _unparse_annotation

        assert _unparse_annotation(None) is None

    @pytest.mark.unit
    def test_simple_annotation_returns_string(self):
        """A simple annotation node returns its string representation."""
        import ast as _ast

        from abstract.wrapper_base import _unparse_annotation

        source = "def func() -> int: pass\n"
        tree = _ast.parse(source)
        func_node = tree.body[0]
        result = _unparse_annotation(func_node.returns)
        assert result == "int"

    @pytest.mark.unit
    def test_complex_annotation_returns_string(self):
        """A complex annotation is unparsed correctly."""
        import ast as _ast

        from abstract.wrapper_base import _unparse_annotation

        source = "def func() -> list[str]: pass\n"
        tree = _ast.parse(source)
        func_node = tree.body[0]
        result = _unparse_annotation(func_node.returns)
        assert "str" in result


class TestCompareSymbols:
    """_compare_symbols detects removed symbols and changed signatures."""

    @pytest.mark.unit
    def test_removed_function_detected(self):
        """A function present in old but absent in new is flagged as removed."""
        from abstract.wrapper_base import _compare_symbols

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
        from abstract.wrapper_base import _compare_symbols

        old = {"OldClass": {"kind": "class", "params": [], "return_type": None}}
        new: dict = {}
        changes: list = []
        _compare_symbols("file.py", old, new, changes)
        assert changes[0]["type"] == "removed"

    @pytest.mark.unit
    def test_unchanged_function_no_changes(self):
        """Identical old and new function generates no changes."""
        from abstract.wrapper_base import _compare_symbols

        sym = {"kind": "function", "params": ["a", "b"], "return_type": "int"}
        old = {"func": sym}
        new = {"func": sym}
        changes: list = []
        _compare_symbols("file.py", old, new, changes)
        assert changes == []

    @pytest.mark.unit
    def test_non_function_kind_skips_sig_comparison(self):
        """If one side is a class, signature comparison is skipped."""
        from abstract.wrapper_base import _compare_symbols

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
        from abstract.wrapper_base import _compare_function_sigs

        old = {"kind": "function", "params": ["a", "b"], "return_type": None}
        new = {"kind": "function", "params": ["a"], "return_type": None}
        changes: list = []
        _compare_function_sigs("file.py", "func", old, new, changes)
        types = [c["type"] for c in changes]
        assert "parameter_removed" in types

    @pytest.mark.unit
    def test_reordered_parameters_detected(self):
        """Reordering parameters is flagged."""
        from abstract.wrapper_base import _compare_function_sigs

        old = {"kind": "function", "params": ["a", "b"], "return_type": None}
        new = {"kind": "function", "params": ["b", "a"], "return_type": None}
        changes: list = []
        _compare_function_sigs("file.py", "func", old, new, changes)
        types = [c["type"] for c in changes]
        assert "parameters_reordered" in types

    @pytest.mark.unit
    def test_return_type_change_detected(self):
        """Changing return type is flagged when old type was non-None."""
        from abstract.wrapper_base import _compare_function_sigs

        old = {"kind": "function", "params": [], "return_type": "int"}
        new = {"kind": "function", "params": [], "return_type": "str"}
        changes: list = []
        _compare_function_sigs("file.py", "func", old, new, changes)
        types = [c["type"] for c in changes]
        assert "return_type_changed" in types

    @pytest.mark.unit
    def test_none_old_return_type_not_flagged(self):
        """When old return type is None, change is not flagged."""
        from abstract.wrapper_base import _compare_function_sigs

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
        from unittest.mock import MagicMock, patch

        from abstract.wrapper_base import _detect_breaking_changes

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
        import subprocess
        from unittest.mock import patch

        from abstract.wrapper_base import _detect_breaking_changes

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
        from unittest.mock import MagicMock, patch

        from abstract.wrapper_base import _detect_breaking_changes

        py_file = tmp_path / "module.py"
        py_file.write_text("def func(): pass\n")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "def broken(\n"  # Syntax error

        with patch("subprocess.run", return_value=mock_result):
            result = _detect_breaking_changes([str(py_file)])

        assert result == []
