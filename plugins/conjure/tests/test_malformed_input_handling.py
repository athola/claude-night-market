"""Delegation and War Room code must survive unusual bytes, files and shapes.

Each test pins one defect found by a bug review: an answer thrown away, a
file truncated, or a crash where the input was legal but unexpected.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest
from scripts.delegation_executor import Delegator, LaunchSpec
from scripts.delegation_services import SERVICES
from scripts.delegation_verify import verify_service
from scripts.provider_ledger import ProviderLedger
from scripts.war_room import WarRoomSession
from scripts.war_room.persistence import load_session, persist_session

from scripts import delegation_executor


class TestLaunchProcessDecoding:
    """A provider that answered must not be reported as failed over one byte."""

    def test_exit_zero_with_non_utf8_output_is_still_a_success(
        self, temp_config_dir: Path
    ) -> None:
        """Undecodable stdout bytes do not turn an exit-0 run into a failure."""
        delegator = Delegator(config_dir=temp_config_dir)
        spec = LaunchSpec(
            cmd=[
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'answer \\xff end')",
            ],
            service_name="gemini",
            prompt="",
            files=None,
            timeout=30,
            start_time=time.time(),
        )

        result = delegator._launch_process(spec)

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout.startswith("answer ")


class TestDelegationConfigShape:
    """A config that parses but is not an object must fail closed."""

    @pytest.mark.parametrize("body", ["[]", '"text"', "7"])
    def test_non_object_config_turns_delegation_off(
        self, temp_config_dir: Path, body: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A JSON array, string or number config disables delegation."""
        monkeypatch.delenv(delegation_executor.DELEGATION_ENV_VAR, raising=False)
        (temp_config_dir / "config.json").write_text(body)

        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is False
        assert "config" in (delegator.delegation_off_reason or "")

    def test_non_utf8_config_turns_delegation_off(
        self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config bytes that are not UTF-8 disable delegation."""
        monkeypatch.delenv(delegation_executor.DELEGATION_ENV_VAR, raising=False)
        (temp_config_dir / "config.json").write_bytes(b"\xff\xfe{}")

        delegator = Delegator(config_dir=temp_config_dir)

        assert delegator.delegation_enabled is False


class TestPersistSessionKeepsLastGoodFile:
    """A save that fails must not destroy the session already on disk."""

    def test_unserializable_artifact_leaves_previous_session_json_intact(
        self, tmp_path: Path
    ) -> None:
        """A save that raises leaves the old file loadable and no .tmp file."""
        session = WarRoomSession(session_id="keep-me", problem_statement="p")
        persist_session(tmp_path, session)
        session_file = tmp_path / "war-table" / "keep-me" / "session.json"
        before = session_file.read_text()

        session.artifacts["bad"] = {"value": object()}
        with pytest.raises(TypeError):
            persist_session(tmp_path, session)

        assert session_file.read_text() == before
        assert load_session(tmp_path, "keep-me") is not None
        assert not list(session_file.parent.glob("*.tmp"))


class TestVerifyServiceUnrunnableBinary:
    """A binary that exists but cannot be executed is an unavailable provider."""

    def test_non_executable_command_is_reported_not_raised(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A command file lacking execute permission reports unavailable."""
        not_a_program = tmp_path / "gemini"
        not_a_program.write_text("not executable")
        not_a_program.chmod(0o644)
        monkeypatch.setenv("GEMINI_API_KEY", "placeholder")
        service = replace(
            SERVICES["gemini"],
            command=str(not_a_program),
            version_probe=("--version",),
            auth_files=(),
        )

        available, issues = verify_service(service)

        assert available is False
        assert issues


class TestProviderLedgerBadCache:
    """The ledger is a cache: a damaged file is a miss, never a crash."""

    @pytest.mark.parametrize(
        "content",
        [
            b"\xff\xfe\x00",
            b'{"version": 1, "providers": []}',
            b'{"version": 1, "providers": 5}',
        ],
    )
    def test_unusable_file_loads_as_empty(self, tmp_path: Path, content: bytes) -> None:
        """Undecodable bytes or a bad providers field load as no providers."""
        path = tmp_path / "provider-state.json"
        path.write_bytes(content)

        assert ProviderLedger(path=path).names() == ()


class TestUsageSummarySkipsDamagedLines:
    """One bad line in the append-only usage log must not hide the rest."""

    def test_line_with_unparseable_timestamp_is_skipped(
        self, temp_config_dir: Path
    ) -> None:
        """Lines with a bad timestamp or a non-object body are not counted."""
        delegator = Delegator(config_dir=temp_config_dir)
        good = {
            "timestamp": datetime.now().isoformat(),
            "service": "gemini",
            "success": True,
            "duration": 1.0,
            "tokens_used": 3,
        }
        lines = [
            json.dumps({**good, "timestamp": "not-a-time"}),
            json.dumps([1, 2]),
            json.dumps(good),
        ]
        delegator.usage_log.write_text("\n".join(lines) + "\n")

        summary = delegator.get_usage_summary()

        assert summary["total_requests"] == 1
