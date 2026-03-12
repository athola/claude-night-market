"""Tests for agents and config modules.

Covers AnalysisError, ConfigLoader, and SkillLoader.validate_metadata.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from parseltongue.agents import AnalysisError
from parseltongue.config import ConfigLoader
from parseltongue.skills.skill_loader import SkillLoader


class TestAnalysisError:
    """Tests for the AnalysisError exception."""

    @pytest.mark.unit
    def test_analysis_error_is_exception(self) -> None:
        """AnalysisError should be a subclass of Exception."""
        assert issubclass(AnalysisError, Exception)

    @pytest.mark.unit
    def test_analysis_error_can_be_raised_and_caught(self) -> None:
        """AnalysisError can be raised with a message."""
        with pytest.raises(AnalysisError, match="test failure"):
            raise AnalysisError("test failure")

    @pytest.mark.unit
    def test_analysis_error_message(self) -> None:
        """AnalysisError preserves its message."""
        err = AnalysisError("something went wrong")
        assert str(err) == "something went wrong"


class TestConfigLoader:
    """Tests for ConfigLoader."""

    @pytest.mark.unit
    def test_load_valid_config(self) -> None:
        """Given a valid JSON config file, return parsed dict."""
        loader = ConfigLoader()
        data = {"python_version": "3.11", "debug": False}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)
        result = loader.load_config(path)
        assert result["python_version"] == "3.11"

    @pytest.mark.unit
    def test_load_config_raises_on_non_object(self) -> None:
        """Given a JSON array, raise ValueError."""
        loader = ConfigLoader()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([1, 2, 3], f)
            path = Path(f.name)
        with pytest.raises(ValueError, match="JSON object"):
            loader.load_config(path)

    @pytest.mark.unit
    def test_load_config_raises_on_bad_python_version(self) -> None:
        """Given python_version as non-string, raise ValueError."""
        loader = ConfigLoader()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"python_version": 311}, f)
            path = Path(f.name)
        with pytest.raises(ValueError, match="python_version must be a string"):
            loader.load_config(path)

    @pytest.mark.unit
    def test_load_config_raises_on_malformed_json(self) -> None:
        """Given malformed JSON, raise json.JSONDecodeError."""
        loader = ConfigLoader()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json}")
            path = Path(f.name)
        with pytest.raises(json.JSONDecodeError):
            loader.load_config(path)


class TestSkillLoaderValidateMetadata:
    """Tests for SkillLoader.validate_metadata (sync method)."""

    @pytest.mark.unit
    def test_valid_metadata(self) -> None:
        """Given complete metadata, return valid result."""
        loader = SkillLoader()
        result = loader.validate_metadata(
            {"name": "my-skill", "description": "does things", "tools": []}
        )
        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.unit
    def test_missing_name(self) -> None:
        """Given metadata without name, report error."""
        loader = SkillLoader()
        result = loader.validate_metadata({"description": "ok"})
        assert result["valid"] is False
        assert any("name" in e for e in result["errors"])

    @pytest.mark.unit
    def test_none_description(self) -> None:
        """Given description=None, report error."""
        loader = SkillLoader()
        result = loader.validate_metadata({"name": "x", "description": None})
        assert result["valid"] is False
        assert any("description" in e for e in result["errors"])

    @pytest.mark.unit
    def test_tools_not_list(self) -> None:
        """Given tools as non-list, report error."""
        loader = SkillLoader()
        result = loader.validate_metadata(
            {"name": "x", "description": "ok", "tools": "not-a-list"}
        )
        assert result["valid"] is False
        assert any("tools" in e for e in result["errors"])
