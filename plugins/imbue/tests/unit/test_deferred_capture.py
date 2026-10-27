# ruff: noqa: D101,D102,D103,S603,S607
"""Tests for imbue deferred_capture.py wrapper.

Validates plugin-specific config and enrichment. Shared logic
is tested in plugins/leyline/tests/unit/src/test_deferred_capture.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "deferred_capture.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestImbueConfig:
    """Feature: imbue wrapper uses correct labels and enrichment."""

    def test_dry_run_produces_valid_json(self) -> None:
        result = _run(
            "--title",
            "Test",
            "--source",
            "scope-guard",
            "--context",
            "ctx",
            "--dry-run",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "dry_run"

    def test_labels_include_imbue_sources(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "scope-guard",
            "--context",
            "c",
            "--dry-run",
        )
        labels = json.loads(result.stdout)["labels"]
        assert "deferred" in labels
        assert "scope-guard" in labels

    def test_scope_guard_enrichment(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "scope-guard",
            "--context",
            "Base",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "worthiness scoring" in body

    def test_no_enrichment_for_feature_review(self) -> None:
        result = _run(
            "--title",
            "T",
            "--source",
            "feature-review",
            "--context",
            "Base",
            "--dry-run",
        )
        body = json.loads(result.stdout)["body"]
        assert "worthiness scoring" not in body


class TestImbueConfigInProcess:
    """Feature: the wrapper's config, imported the way the coverage gate sees it."""

    def _module(self):
        import importlib.util  # noqa: PLC0415 - loaded per test, script is not a package

        spec = importlib.util.spec_from_file_location("imbue_deferred_capture", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_config_names_imbue_and_its_source_labels(self) -> None:
        config = self._module().CONFIG
        assert config.plugin_name == "imbue"
        assert set(config.label_colors) == {"deferred", "scope-guard", "feature-review"}

    def test_only_scope_guard_context_is_enriched(self) -> None:
        enrich = self._module()._enrich
        assert enrich("scope-guard", "Base").startswith("Base\n\n")
        assert "worthiness scoring" in enrich("scope-guard", "Base")
        assert enrich("feature-review", "Base") == "Base"

    def test_missing_leyline_exits_1_with_an_install_hint(self, monkeypatch, capsys):
        monkeypatch.setitem(sys.modules, "leyline.deferred_capture", None)
        with pytest.raises(SystemExit) as exc:
            self._module()
        assert exc.value.code == 1
        assert "leyline not found" in capsys.readouterr().err
