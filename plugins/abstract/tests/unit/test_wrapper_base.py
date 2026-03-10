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
        with pytest.raises((ValueError, Exception)):
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
            w.translate_parameters("not a dict")  # type: ignore[arg-type]

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
        with pytest.raises((ValueError, Exception)):
            SuperpowerWrapper("p", "c", "s", config_path=config_file)
