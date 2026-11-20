"""A list-shaped pass token denied every commit until deleted (ARCH-1)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))

import precommit_gate  # noqa: E402 - hooks dir joins sys.path above


def test_non_object_pass_token_is_no_token(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / "pass_token.json").write_text("[]")
    assert precommit_gate.check_pass_token(tmp_path, "abc") is False


def _write_token(tmp_path: Path, token: dict) -> None:
    import json  # noqa: PLC0415 - local to this helper

    state = tmp_path / "state"
    state.mkdir()
    (state / "pass_token.json").write_text(json.dumps(token))


def test_pass_token_with_null_timestamps_is_no_token(tmp_path: Path) -> None:
    """fromisoformat(None) raised TypeError, and run_gate denied every commit."""
    _write_token(tmp_path, {"staged_hash": "h", "expires_at": None, "issued_at": None})
    assert precommit_gate.check_pass_token(tmp_path, "h") is False


def test_pass_token_with_naive_timestamps_is_no_token(tmp_path: Path) -> None:
    """A naive time parsed, then raised TypeError against the aware now."""
    _write_token(
        tmp_path,
        {
            "staged_hash": "h",
            "expires_at": "2099-01-01T00:00:00",
            "issued_at": "2020-01-01T00:00:00",
        },
    )
    assert precommit_gate.check_pass_token(tmp_path, "h") is False


class TestPrecommitMode:
    """``precommit.mode`` comes from a user's YAML file, a trust boundary."""

    @staticmethod
    def _mode(tmp_path: Path, text: str) -> str:
        import pytest  # noqa: PLC0415 - skip guard local to the yaml cases

        pytest.importorskip("yaml")
        (tmp_path / "config.yaml").write_text(text)
        return precommit_gate._precommit_mode(precommit_gate._load_config(tmp_path))

    def test_unquoted_off_in_config_yaml_turns_the_gate_off(
        self, tmp_path: Path
    ) -> None:
        """YAML 1.1 reads bare ``off`` as False, which fell through to deny."""
        assert self._mode(tmp_path, "precommit:\n  mode: off\n") == "off"

    def test_empty_precommit_block_falls_back_to_gate(self, tmp_path: Path) -> None:
        """``precommit:`` parsed as None, and ``.get`` on it denied every commit."""
        assert self._mode(tmp_path, "precommit:\n") == "gate"

    def test_named_modes_are_kept(self, tmp_path: Path) -> None:
        assert self._mode(tmp_path, "precommit:\n  mode: nudge\n") == "nudge"

    def test_unknown_mode_warns_and_falls_back_to_gate(
        self, tmp_path: Path, capsys
    ) -> None:
        assert self._mode(tmp_path, "precommit:\n  mode: strict\n") == "gate"
        assert "strict" in capsys.readouterr().err

    def test_missing_precommit_block_is_gate(self) -> None:
        assert precommit_gate._precommit_mode({}) == "gate"
