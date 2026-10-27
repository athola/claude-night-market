"""In-process tests for skill_execution_logger's redaction and error paths.

The subprocess tests cover the stdin contract and the happy paths. These
cover the branches a subprocess run cannot reach cheaply: secret redaction
in logged output, unreadable history, orphan-state cleanup failures, a
corrupt pre-state, the log path containment check, and the top-level
catch that keeps a hook failure from blocking the session.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import time
from pathlib import Path
from types import ModuleType

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
SKILL = "abstract:skill-auditor"


@pytest.fixture
def hook(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
    monkeypatch.syspath_prepend(str(HOOKS_DIR))
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
    return importlib.import_module("skill_execution_logger")


def _run_main(
    hook: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tool_response: str = "Success",
) -> tuple[int, str, str]:
    payload = {
        "tool_name": "Skill",
        "tool_input": {"skill": SKILL},
        "tool_response": tool_response,
        "session_id": "sess-1",
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    with pytest.raises(SystemExit) as exc:
        hook.main()
    out = capsys.readouterr()
    return exc.value.code, out.out, out.err


class TestSanitizeOutput:
    """Failure output is logged, so secrets in it must not be."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("raw", "secret"),
        [
            (
                "api_key = 'abcdefghijklmnopqrstuvwxyz123'",
                "abcdefghijklmnopqrstuvwxyz123",
            ),
            ("Authorization: Bearer eyJhbGciOi.payload.sig", "eyJhbGciOi.payload.sig"),
            ("password: hunter2!", "hunter2!"),
            ("token=0123456789abcdef0123", "0123456789abcdef0123"),
            ("AWS_SECRET_ACCESS_KEY=abc/def+ghi=jklmno", "abc/def+ghi=jklmno"),
            ("aws_access_key_id=AKIAABCDEFGHIJKLMNOP", "AKIAABCDEFGHIJKLMNOP"),
            ("pushed with ghp_" + "a" * 36, "ghp_" + "a" * 36),
            ("credential: " + "Q" * 40, "Q" * 40),
        ],
        ids=[
            "api-key",
            "bearer",
            "password",
            "token",
            "aws-secret-access-key",
            "aws-access-key-id",
            "github",
            "base64",
        ],
    )
    def test_secret_is_redacted(self, hook: ModuleType, raw: str, secret: str) -> None:
        sanitized = hook.sanitize_output(raw)

        assert secret not in sanitized
        assert "REDACTED" in sanitized

    @pytest.mark.unit
    def test_long_output_is_truncated_before_redaction(self, hook: ModuleType) -> None:
        sanitized = hook.sanitize_output("x" * 300, max_length=200)

        assert sanitized.startswith("x" * 200)
        assert "truncated from 300 chars" in sanitized
        assert "x" * 201 not in sanitized

    @pytest.mark.unit
    def test_failure_entry_logs_redacted_preview(
        self, hook: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
    ) -> None:
        """A failing skill's output reaches the log only through redaction."""
        code, _, _ = _run_main(
            hook, monkeypatch, capsys, "Error: auth failed, password: hunter2!"
        )

        (log_file,) = (
            tmp_path / "skills" / "logs" / "abstract" / "skill-auditor"
        ).glob("*.jsonl")
        entry = json.loads(log_file.read_text())
        assert code == 0
        assert entry["outcome"] == "failure"
        assert "hunter2!" not in entry["context"]["output_preview"]


class TestHistoryLoadErrors:
    """An unreadable history starts empty and says why."""

    @pytest.mark.unit
    def test_unreadable_history_is_reported_and_starts_empty(
        self, hook: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        history = tmp_path / ".history.json"
        history.mkdir()

        evaluator = hook.ContinualEvaluator(history)

        assert dict(evaluator.skill_history) == {}
        assert "failed to load history" in capsys.readouterr().err


class TestOrphanPurge:
    """Orphan cleanup tolerates files that vanish or cannot be removed."""

    @pytest.mark.unit
    def test_vanished_state_file_is_dropped(
        self, hook: ModuleType, tmp_path: Path
    ) -> None:
        live = tmp_path / f"{SKILL}:1.json"
        live.write_text("{}")

        assert hook._purge_orphan_states([tmp_path / "gone.json", live]) == [live]

    @pytest.mark.unit
    def test_failed_orphan_unlink_is_reported_and_excluded(
        self,
        hook: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        orphan = tmp_path / f"{SKILL}:1.json"
        orphan.write_text("{}")
        old = time.time() - hook.ORPHAN_STATE_MAX_AGE_S - 60
        os.utime(orphan, (old, old))

        def deny(self: Path, missing_ok: bool = False) -> None:
            raise PermissionError("read-only")

        monkeypatch.setattr(Path, "unlink", deny)

        assert hook._purge_orphan_states([orphan]) == []
        assert "orphan cleanup failed" in capsys.readouterr().err


class TestCorruptPreState:
    """A pre-state that cannot be claimed or parsed leaves duration unmeasured."""

    @pytest.mark.unit
    def test_corrupt_state_is_removed_and_duration_unmeasured(
        self,
        hook: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        obs = tmp_path / "skills" / "observability"
        obs.mkdir(parents=True)
        (obs / f"{SKILL}:1.json").write_text("{not json")

        code, out, _ = _run_main(hook, monkeypatch, capsys)

        assert code == 0
        assert json.loads(out)["hookSpecificOutput"]["duration_ms"] is None
        assert list(obs.iterdir()) == []

    @pytest.mark.unit
    def test_state_claimed_by_another_hook_is_left_unmeasured(
        self,
        hook: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """A rename losing the race to a parallel post hook is not an error."""
        obs = tmp_path / "skills" / "observability"
        obs.mkdir(parents=True)
        (obs / f"{SKILL}:1.json").write_text(json.dumps({"timestamp": "x"}))

        def lost_race(self: Path, target: Path) -> Path:
            raise FileNotFoundError(str(self))

        monkeypatch.setattr(Path, "rename", lost_race)

        code, out, err = _run_main(hook, monkeypatch, capsys)

        assert code == 0
        assert json.loads(out)["hookSpecificOutput"]["duration_ms"] is None
        assert "skill_execution_logger error" not in err


class TestSaveLogEntryContainment:
    """Log writes stay inside the log directory."""

    @pytest.mark.unit
    def test_path_traversal_in_entry_is_refused(
        self, hook: ModuleType, tmp_path: Path
    ) -> None:
        entry = {
            "plugin": "..",
            "skill_name": "..",
            "timestamp": "2026-03-01T00:00:00+00:00",
        }

        with pytest.raises(ValueError, match="Path traversal"):
            hook.save_log_entry(entry)
        assert not (tmp_path / "2026-03-01.jsonl").exists()


class TestTopLevelCatch:
    """No failure inside main() may block the session."""

    @pytest.mark.unit
    def test_unexpected_failure_exits_zero_with_labelled_stderr(
        self,
        hook: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """A log tree that cannot be created must not block the session."""
        (tmp_path / "skills").mkdir()
        (tmp_path / "skills" / "logs").write_text("a file where a directory goes")

        code, out, err = _run_main(hook, monkeypatch, capsys)

        assert code == 0
        assert out == ""
        assert "skill_execution_logger error:" in err
