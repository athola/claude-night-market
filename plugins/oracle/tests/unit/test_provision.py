"""Tests for oracle venv provisioning."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from oracle.provision import (
    get_oracle_data_dir,
    get_venv_path,
    is_provisioned,
    provision_venv,
)


class TestOracleDataDir:
    """
    Feature: Oracle data directory management

    As the oracle plugin
    I want a stable data directory for venv and state
    So that provisioning survives plugin updates
    """

    @pytest.mark.unit
    def test_uses_claude_plugin_data_env(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: CLAUDE_PLUGIN_DATA env var is set
        Given CLAUDE_PLUGIN_DATA points to a directory
        When get_oracle_data_dir is called
        Then it returns that path
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/plugin-data/oracle")
        result = get_oracle_data_dir()
        assert result == Path("/tmp/plugin-data/oracle")

    @pytest.mark.unit
    def test_falls_back_to_home_dir(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: CLAUDE_PLUGIN_DATA is not set
        Given no CLAUDE_PLUGIN_DATA env var
        When get_oracle_data_dir is called
        Then it returns ~/.oracle-inference
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        result = get_oracle_data_dir()
        assert result == Path.home() / ".oracle-inference"


class TestVenvPath:
    """
    Feature: Venv path resolution

    As the oracle plugin
    I want a consistent venv location
    So that the daemon can find its Python interpreter
    """

    @pytest.mark.unit
    def test_venv_under_data_dir(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: Venv path is under the data directory
        Given a data directory
        When get_venv_path is called
        Then it returns data_dir / venv
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/oracle-data")
        result = get_venv_path()
        assert result == Path("/tmp/oracle-data") / "venv"


class TestIsProvisioned:
    """
    Feature: Provisioning status check

    As the oracle daemon lifecycle hook
    I want to check if the venv is ready
    So that I only start the daemon when provisioned
    """

    @pytest.mark.unit
    def test_not_provisioned_when_no_venv(self, tmp_path: Path):
        """
        Scenario: No venv directory exists
        Given an empty data directory
        When is_provisioned is called
        Then it returns False
        """
        assert is_provisioned(tmp_path / "venv") is False

    @pytest.mark.unit
    def test_provisioned_when_python_exists(self, tmp_path: Path):
        """
        Scenario: Venv with Python binary exists
        Given a venv directory with bin/python
        When is_provisioned is called
        Then it returns True
        """
        venv = tmp_path / "venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        assert is_provisioned(venv) is True


class TestProvisionVenv:
    """
    Feature: Venv provisioning via uv

    As a user running /oracle:setup
    I want the venv and onnxruntime installed automatically
    So that I don't need to manage Python environments
    """

    @pytest.mark.unit
    def test_provision_calls_uv_with_correct_args(self, tmp_path: Path):
        """
        Scenario: Provisioning runs uv commands
        Given a target directory
        When provision_venv is called
        Then it runs uv venv and uv pip install
        """
        with patch("oracle.provision.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = provision_venv(tmp_path / "venv")
            assert result.success is True
            calls = mock_run.call_args_list
            assert "venv" in str(calls[0])
            assert "onnxruntime" in str(calls[1])

    @pytest.mark.unit
    def test_provision_fails_when_uv_missing(self, tmp_path: Path):
        """
        Scenario: uv is not installed
        Given uv is not on PATH
        When provision_venv is called
        Then it returns failure with helpful message
        """
        with patch("oracle.provision.subprocess.run", side_effect=FileNotFoundError):
            result = provision_venv(tmp_path / "venv")
            assert result.success is False
            assert "uv" in result.message.lower()

    @pytest.mark.unit
    def test_provision_fails_when_venv_creation_fails(self, tmp_path: Path):
        """
        Scenario: uv venv returns non-zero exit code
        Given uv venv fails
        When provision_venv is called
        Then it returns failure with stderr message
        """
        with patch("oracle.provision.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="python 3.11 not found",
            )
            result = provision_venv(tmp_path / "venv")
            assert result.success is False
            assert "venv" in result.message.lower()

    @pytest.mark.unit
    def test_provision_fails_when_install_fails(self, tmp_path: Path):
        """
        Scenario: uv pip install returns non-zero exit code
        Given venv creation succeeds but onnxruntime install fails
        When provision_venv is called
        Then it returns failure with stderr message
        """
        with patch("oracle.provision.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),
                MagicMock(returncode=1, stderr="network error"),
            ]
            result = provision_venv(tmp_path / "venv")
            assert result.success is False
            assert "onnxruntime" in result.message.lower()

    @pytest.mark.unit
    def test_provision_fails_on_timeout(self, tmp_path: Path):
        """
        Scenario: uv command times out
        Given a slow network or system
        When provision_venv is called
        Then it returns failure with timeout message
        """
        with patch(
            "oracle.provision.subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired(cmd="uv", timeout=120),
        ):
            result = provision_venv(tmp_path / "venv")
            assert result.success is False
            assert "timed out" in result.message.lower()
