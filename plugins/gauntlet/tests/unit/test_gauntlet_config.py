"""One reader for `.gauntlet/config.yaml` and `config.json` across the hooks.

Each hook read the config its own way: the SessionStart rebuild read only
config.json, so `rebuild_on_upgrade: false` in config.yaml was ignored, and
the commit hook read config.json before config.yaml while the gate did the
reverse.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _gauntlet_config
import pytest
from _gauntlet_config import load_config


@pytest.mark.unit
class TestLoadConfig:
    """yaml first, json second, absent and unreadable told apart."""

    def test_no_config_file_reads_as_empty(self, tmp_path: Path) -> None:
        assert load_config(tmp_path) == {}

    def test_yaml_is_preferred_over_json(self, tmp_path: Path) -> None:
        (tmp_path / "config.yaml").write_text("auto_update: false\n")
        (tmp_path / "config.json").write_text(json.dumps({"auto_update": True}))
        assert load_config(tmp_path) == {"auto_update": False}

    def test_json_is_read_when_there_is_no_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text(json.dumps({"auto_update": True}))
        assert load_config(tmp_path) == {"auto_update": True}

    def test_a_config_that_is_not_a_mapping_reads_as_empty(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "config.json").write_text("[1, 2]")
        assert load_config(tmp_path) == {}

    def test_an_unparseable_config_reads_as_unreadable(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text("{not json")
        assert load_config(tmp_path) is None

    def test_yaml_without_pyyaml_falls_back_to_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "config.yaml").write_text("auto_update: false\n")
        (tmp_path / "config.json").write_text(json.dumps({"auto_update": True}))
        monkeypatch.setitem(sys.modules, "yaml", None)
        assert load_config(tmp_path) == {"auto_update": True}

    def test_yaml_without_pyyaml_and_no_json_reads_as_unreadable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "config.yaml").write_text("rebuild_on_upgrade: false\n")
        monkeypatch.setitem(sys.modules, "yaml", None)
        assert load_config(tmp_path) is None
        assert capsys.readouterr().err.count("PyYAML is not installed") == 1

    def test_module_imports_nothing_outside_the_standard_library(self) -> None:
        source = Path(_gauntlet_config.__file__).read_text()
        assert "import gauntlet" not in source
        assert "from gauntlet" not in source
