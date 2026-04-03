"""Tests for the check_plugin_hooks pre-commit hook.

Feature: Prevent duplicate hooks/hooks.json in plugin manifests

As a plugin developer
I want commits blocked when plugin.json explicitly lists hooks/hooks.json
So that session-start "Duplicate hooks file" errors never reach users
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestCheckPluginHooks:
    """Verify detection of the auto-loaded hooks/hooks.json in manifests."""

    @pytest.mark.unit
    def test_rejects_explicit_hooks_json(self, tmp_path: Path) -> None:
        """
        Scenario: plugin.json lists the auto-loaded hooks file
        Given a plugin.json with hooks: ["./hooks/hooks.json"]
        When check_file runs
        Then it returns an error about duplicate hooks
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "hooks": ["./hooks/hooks.json"],
                }
            )
        )

        from scripts.check_plugin_hooks import check_file

        errors = check_file(manifest)
        assert len(errors) == 1
        assert "./hooks/hooks.json" in errors[0]
        assert "auto-loaded" in errors[0]

    @pytest.mark.unit
    def test_accepts_empty_hooks_array(self, tmp_path: Path) -> None:
        """
        Scenario: plugin.json has an empty hooks array
        Given a plugin.json with hooks: []
        When check_file runs
        Then it returns no errors
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "hooks": [],
                }
            )
        )

        from scripts.check_plugin_hooks import check_file

        errors = check_file(manifest)
        assert errors == []

    @pytest.mark.unit
    def test_accepts_additional_hook_files(self, tmp_path: Path) -> None:
        """
        Scenario: plugin.json lists only non-default hook files
        Given a plugin.json with hooks: ["./hooks/extra-hooks.json"]
        When check_file runs
        Then it returns no errors
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "hooks": ["./hooks/extra-hooks.json"],
                }
            )
        )

        from scripts.check_plugin_hooks import check_file

        errors = check_file(manifest)
        assert errors == []

    @pytest.mark.unit
    def test_rejects_default_among_additional_hooks(self, tmp_path: Path) -> None:
        """
        Scenario: plugin.json mixes the default with additional hooks
        Given a plugin.json with hooks containing both default and extra
        When check_file runs
        Then it returns an error for the default entry
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "hooks": [
                        "./hooks/hooks.json",
                        "./hooks/extra-hooks.json",
                    ],
                }
            )
        )

        from scripts.check_plugin_hooks import check_file

        errors = check_file(manifest)
        assert len(errors) == 1
        assert "./hooks/hooks.json" in errors[0]

    @pytest.mark.unit
    def test_accepts_missing_hooks_field(self, tmp_path: Path) -> None:
        """
        Scenario: plugin.json has no hooks field at all
        Given a plugin.json without a hooks key
        When check_file runs
        Then it returns no errors
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                }
            )
        )

        from scripts.check_plugin_hooks import check_file

        errors = check_file(manifest)
        assert errors == []

    @pytest.mark.unit
    def test_handles_invalid_json(self, tmp_path: Path) -> None:
        """
        Scenario: plugin.json contains invalid JSON
        Given a plugin.json with malformed content
        When check_file runs
        Then it returns a parse error
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text("{invalid json")

        from scripts.check_plugin_hooks import check_file

        errors = check_file(manifest)
        assert len(errors) == 1
        assert "failed to parse" in errors[0]

    @pytest.mark.unit
    def test_main_returns_1_on_violations(self, tmp_path: Path) -> None:
        """
        Scenario: main() scans files and finds violations
        Given plugin.json files passed as arguments
        When main runs with a violating file
        Then it returns exit code 1
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "bad-plugin",
                    "hooks": ["./hooks/hooks.json"],
                }
            )
        )

        from scripts.check_plugin_hooks import main

        exit_code = main([str(manifest)])
        assert exit_code == 1

    @pytest.mark.unit
    def test_main_returns_0_when_clean(self, tmp_path: Path) -> None:
        """
        Scenario: main() scans files and finds no violations
        Given plugin.json files passed as arguments
        When main runs with a clean file
        Then it returns exit code 0
        """
        manifest = tmp_path / "plugin.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "good-plugin",
                    "hooks": [],
                }
            )
        )

        from scripts.check_plugin_hooks import main

        exit_code = main([str(manifest)])
        assert exit_code == 0
