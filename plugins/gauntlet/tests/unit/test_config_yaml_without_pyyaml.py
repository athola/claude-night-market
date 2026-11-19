"""Without PyYAML, gauntlet skipped `.gauntlet/config.yaml` in silence, so a
user's `precommit: {mode: "off"}` left the gate on (ARCH-2).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))

import graph_auto_update  # noqa: E402 - hooks dir joins sys.path above
import precommit_gate  # noqa: E402 - hooks dir joins sys.path above


@pytest.fixture()
def yaml_config_without_pyyaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "config.yaml").write_text(
        "precommit:\n  mode: off\nauto_update: true\n"
    )
    monkeypatch.setitem(sys.modules, "yaml", None)
    return tmp_path


def test_precommit_gate_warns_when_config_yaml_unreadable(
    yaml_config_without_pyyaml: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    precommit_gate._load_config(yaml_config_without_pyyaml)
    assert "config.yaml" in capsys.readouterr().err


def test_auto_update_warns_when_config_yaml_unreadable(
    yaml_config_without_pyyaml: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    graph_auto_update._is_auto_update_enabled(yaml_config_without_pyyaml)
    assert "config.yaml" in capsys.readouterr().err


def test_auto_update_without_a_parser_runs_in_the_plugin_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Under a python3 without tree-sitter, every commit reported "Graph not
    updated" (GAU-3). The update now runs detached under `uv run --project`.
    """
    from unittest.mock import MagicMock, patch  # noqa: PLC0415 - imported after pyyaml is blocked

    gauntlet_dir = tmp_path / ".gauntlet"
    gauntlet_dir.mkdir()
    (gauntlet_dir / "graph.db").write_bytes(b"")
    (gauntlet_dir / "config.json").write_text('{"auto_update": true}')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(graph_auto_update, "_get_gauntlet_dir", lambda: gauntlet_dir)
    monkeypatch.setattr(graph_auto_update, "parser_available", lambda: False)
    monkeypatch.setattr(graph_auto_update.shutil, "which", lambda name: "/bin/uv")
    popen = MagicMock()
    with patch.object(graph_auto_update.subprocess, "Popen", popen):
        output = graph_auto_update.main(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "git commit -m x"},
                "tool_response": {"stdout": "1 file changed"},
            }
        )

    argv = popen.call_args.args[0]
    assert argv[:3] == ["/bin/uv", "run", "--project"]
    assert str(tmp_path) in argv
    assert "--incremental" in argv
    assert "background" in output["hookSpecificOutput"]["additionalContext"]


def test_auto_update_waits_while_a_rebuild_holds_its_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second writer on the graph during a version rebuild races it."""
    from unittest.mock import MagicMock, patch  # noqa: PLC0415 - imported after pyyaml is blocked

    gauntlet_dir = tmp_path / ".gauntlet"
    gauntlet_dir.mkdir()
    (gauntlet_dir / "rebuild.lock").write_text("")
    monkeypatch.setattr(graph_auto_update.shutil, "which", lambda name: "/bin/uv")
    popen = MagicMock()
    with patch.object(graph_auto_update.subprocess, "Popen", popen):
        assert graph_auto_update._update_in_plugin_env(gauntlet_dir) is None
    popen.assert_not_called()
