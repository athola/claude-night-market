"""Regression tests for the bug-review sweep: hook config and annotation parsing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from graph_auto_update import _is_auto_update_enabled
from graph_auto_update import main as auto_update_main
from precommit_gate import _graph_staleness_warning
from precommit_gate import main as gate_main

from gauntlet.knowledge_store import KnowledgeStore
from tests.conftest import fake_git


@pytest.fixture()
def gauntlet_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".gauntlet"
    d.mkdir()
    return d


class TestAutoUpdateConfigShapes:
    """A malformed config must read as disabled, not crash the hook."""

    @pytest.mark.unit
    def test_empty_yaml_config_reads_as_disabled(self, gauntlet_dir: Path) -> None:
        pytest.importorskip("yaml")
        (gauntlet_dir / "config.yaml").write_text("")
        assert _is_auto_update_enabled(gauntlet_dir) is False

    @pytest.mark.unit
    def test_list_json_config_reads_as_disabled(self, gauntlet_dir: Path) -> None:
        (gauntlet_dir / "config.json").write_text(json.dumps(["auto_update"]))
        assert _is_auto_update_enabled(gauntlet_dir) is False


class TestAnnotationShapes:
    """One stray annotation file must not break every knowledge query."""

    @pytest.mark.unit
    def test_non_mapping_annotation_is_skipped(self, gauntlet_dir: Path) -> None:
        pytest.importorskip("yaml")
        annotations = gauntlet_dir / "annotations"
        annotations.mkdir()
        (annotations / "stray.yaml").write_text("- just\n- a list\n")
        (annotations / "good.yaml").write_text(
            "module: pkg.mod\nconcept: retry\ndetail: why\ndifficulty: 2\n"
        )

        entries = KnowledgeStore(gauntlet_dir).load(include_annotations=True)

        assert [e.module for e in entries] == ["pkg.mod"]

    @pytest.mark.unit
    def test_non_integer_difficulty_does_not_break_query(
        self, gauntlet_dir: Path
    ) -> None:
        pytest.importorskip("yaml")
        annotations = gauntlet_dir / "annotations"
        annotations.mkdir()
        (annotations / "odd.yaml").write_text(
            "module: pkg.mod\nconcept: retry\ndetail: why\ndifficulty: hard\n"
        )

        # Must not raise TypeError comparing str with int, and the entry
        # with no usable difficulty is skipped rather than guessed at.
        assert KnowledgeStore(gauntlet_dir).query(files=["pkg.mod"]) == []


class TestContextRidesInHookSpecificOutput:
    """The documented shape nests additionalContext in hookSpecificOutput.

    A top-level ``additionalContext`` is an unrecognized key: the harness
    drops it and logs a warning only under ``claude --debug``.
    """

    @pytest.mark.unit
    def test_nudge_mode_context_is_nested_for_pre_tool_use(
        self, sample_knowledge_base: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gauntlet_dir = sample_knowledge_base.parent
        (gauntlet_dir / "config.json").write_text(
            json.dumps({"precommit": {"mode": "nudge"}})
        )
        monkeypatch.chdir(gauntlet_dir.parent)

        with patch("precommit_gate.subprocess.run", side_effect=fake_git(["billing"])):
            result = gate_main({"tool_input": {"command": "git commit -m 'x'"}})

        assert result is not None
        assert "additionalContext" not in result
        output = result["hookSpecificOutput"]
        assert output["hookEventName"] == "PreToolUse"
        assert "Gauntlet challenge required" in output["additionalContext"]
        assert "permissionDecision" not in output

    @pytest.mark.unit
    def test_graph_update_context_is_nested_for_post_tool_use(
        self, gauntlet_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (gauntlet_dir / "config.json").write_text(json.dumps({"auto_update": True}))
        (gauntlet_dir / "graph.db").touch()
        report = {"files_parsed": 3, "nodes_created": 9}
        monkeypatch.chdir(gauntlet_dir.parent)

        with patch("gauntlet.incremental.incremental_update", return_value=report):
            result = auto_update_main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git commit -m 'x'"},
                    "tool_response": {"stdout": "[main abc] x", "stderr": ""},
                }
            )

        assert result is not None
        assert "additionalContext" not in result
        output = result["hookSpecificOutput"]
        assert output["hookEventName"] == "PostToolUse"
        assert "Graph updated: 3 files" in output["additionalContext"]


class TestStalenessConfigShape:
    """A malformed config.json must not turn the staleness check into a crash."""

    @pytest.mark.unit
    def test_list_config_json_falls_back_to_the_default_threshold(
        self, gauntlet_dir: Path
    ) -> None:
        graph_db = gauntlet_dir / "graph.db"
        graph_db.touch()
        (gauntlet_dir / "config.json").write_text(json.dumps(["stale_threshold_hours"]))

        assert _graph_staleness_warning(gauntlet_dir) is None


class TestAnnotationDifficultyCoercion:
    """YAML writes a whole-number difficulty as 2.0 as readily as 2."""

    @pytest.mark.unit
    def test_whole_number_float_difficulty_is_kept(self, gauntlet_dir: Path) -> None:
        pytest.importorskip("yaml")
        annotations = gauntlet_dir / "annotations"
        annotations.mkdir()
        (annotations / "float.yaml").write_text(
            "module: pkg.mod\nconcept: retry\ndetail: why\ndifficulty: 2.0\n"
        )

        entries = KnowledgeStore(gauntlet_dir).load(include_annotations=True)

        assert [e.difficulty for e in entries] == [2]
