"""Regression tests for the verified API-review findings in scribe."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scribe import pattern_loader
from scribe.session_parser import detect_format, parse_session
from scribe.tape_generator import TapeConfig, generate_tape


def _write(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


_CODEX_USER = json.dumps({"type": "message", "role": "user", "content": "hi"})
_CLAUDE_USER = json.dumps({"type": "user", "message": {"content": "hi"}})


class TestSessionParserRobustness:
    @pytest.mark.unit
    def test_detect_format_skips_non_object_json_lines(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "s.jsonl", ["123", _CODEX_USER])

        assert detect_format(path) == "codex"

    @pytest.mark.unit
    def test_parse_session_skips_non_object_json_lines(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "s.jsonl", ["123", '"text"', _CLAUDE_USER])

        turns = parse_session(path)

        assert [t.text for t in turns] == ["hi"]

    @pytest.mark.unit
    def test_parse_session_skips_non_object_lines_in_codex_files(
        self, tmp_path: Path
    ) -> None:
        path = _write(tmp_path / "s.jsonl", [_CODEX_USER, "[1, 2]"])

        turns = parse_session(path, format="codex")

        assert [t.text for t in turns] == ["hi"]


class TestSessionParserArgumentValidation:
    @pytest.mark.unit
    def test_parse_session_rejects_unknown_format(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "s.jsonl", [_CODEX_USER])

        with pytest.raises(ValueError, match="format"):
            parse_session(path, format="Codex")

    @pytest.mark.unit
    def test_parse_session_rejects_unknown_show_layer(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "s.jsonl", [_CLAUDE_USER])

        with pytest.raises(ValueError, match="users"):
            parse_session(path, show="users")

    @pytest.mark.unit
    def test_parse_session_accepts_thinking_layer(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "s.jsonl", [_CLAUDE_USER])

        assert parse_session(path, show="user,thinking")[0].text == "hi"


class TestTapeConfigValidation:
    @pytest.mark.unit
    def test_zero_max_duration_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="max_duration"):
            TapeConfig(max_duration=0.0)

    @pytest.mark.unit
    def test_non_positive_dimensions_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="width"):
            TapeConfig(width=0)
        with pytest.raises(ValueError, match="height"):
            TapeConfig(height=-1)

    @pytest.mark.unit
    def test_none_max_duration_still_means_no_limit(self) -> None:
        assert generate_tape([], TapeConfig(max_duration=None))


class TestPatternLoaderEmptyFile:
    @pytest.mark.unit
    def test_empty_yaml_loads_as_empty_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "en.yaml").write_text("", encoding="utf-8")
        monkeypatch.setattr(pattern_loader, "DATA_DIR", tmp_path)

        assert pattern_loader.load_language_patterns("en") == {}
