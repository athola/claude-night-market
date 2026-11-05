"""Hooks and the night run must survive malformed or unusual on-disk state.

Each test pins one defect found by a bug review: a crash or a wrong answer
where the input was legal JSON or legal git output the code did not expect.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import night_run
import pytest
from _manifest_utils import get_items, has_active_work
from manifest import Manifest, load_manifest, save_manifest
from rate_limit_hook import main as rate_limit_main
from scout import post_discussion


def _manifest_path(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / ".egregore" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))
    return path


class TestProofWithoutFullSuite:
    """A handoff with no commands.full_test must still produce a proof."""

    def test_write_proof_records_skipped_full_suite(self, tmp_path):
        result = night_run.ItemResult(
            item="item-1",
            status="ready",
            full_suite={
                "command": None,
                "skipped": True,
                "reason": "the handoff declares no commands.full_test",
            },
        )

        proof = night_run.write_proof(tmp_path, result)

        text = proof.read_text()
        assert "## Full suite" in text
        assert "no commands.full_test" in text


class TestStopHookManifestShapes:
    """The Stop hook reads the manifest on every stop and must not raise."""

    @pytest.mark.parametrize(
        "payload",
        [[], "text", 7, None, {"work_items": ["wrk_001"]}, {"items": [3, None]}],
    )
    def test_has_active_work_is_false_for_unusable_shapes(self, tmp_path, payload):
        path = _manifest_path(tmp_path, payload)

        assert has_active_work(path) is False

    def test_has_active_work_ignores_non_dict_items_beside_real_ones(self, tmp_path):
        path = _manifest_path(
            tmp_path, {"work_items": ["junk", {"id": "wrk_001", "status": "active"}]}
        )

        assert has_active_work(path) is True

    def test_has_active_work_is_false_for_non_utf8_manifest(self, tmp_path):
        path = _manifest_path(tmp_path, {})
        path.write_bytes(b"\xff\xfe{")

        assert has_active_work(path) is False

    def test_get_items_drops_entries_that_are_not_objects(self):
        assert get_items({"work_items": ["junk", {"id": "a"}, 4]}) == [{"id": "a"}]


class TestSubprocessRunnerDecoding:
    """Command output is evidence even when it is not valid UTF-8."""

    def test_run_keeps_output_that_is_not_utf8(self):
        completed = night_run.SubprocessRunner().run(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'ok\\xff')"]
        )

        assert completed.returncode == 0
        assert completed.output.startswith("ok")


class TestGitQuotedPaths:
    """Porcelain output quotes unusual names; the fence needs the real name."""

    class _Scripted:
        def __init__(self, outputs):
            self.outputs = outputs

        def run(self, command, cwd=None, timeout=0, env=None):
            del cwd, timeout, env
            key = " ".join(command)
            for fragment, text in self.outputs.items():
                if fragment in key:
                    return night_run.Completed(0, text)
            return night_run.Completed(0, "")

    def test_untracked_unquotes_a_name_with_a_space(self, tmp_path):
        runner = self._Scripted(
            {"status --porcelain": '?? ".github/my flows/a.yml"\n?? plain.txt\n'}
        )

        names = night_run._untracked(runner, tmp_path)

        assert names == [".github/my flows/a.yml", "plain.txt"]

    def test_untracked_decodes_octal_escapes_for_non_ascii_names(self, tmp_path):
        runner = self._Scripted({"status --porcelain": '?? "na\\303\\257ve.txt"\n'})

        assert night_run._untracked(runner, tmp_path) == ["naïve.txt"]

    def test_untracked_ends_a_short_octal_escape_at_the_first_non_octal(self, tmp_path):
        runner = self._Scripted({"status --porcelain": '?? "a\\11b\\0789.txt"\n'})

        assert night_run._untracked(runner, tmp_path) == ["a\tb\x0789.txt"]

    def test_changed_files_unquotes_tracked_names(self, tmp_path):
        runner = self._Scripted(
            {"diff HEAD --name-only": '"na\\303\\257ve \\"q\\".txt"\n'}
        )

        assert night_run._changed_files(runner, tmp_path) == ['naïve "q".txt']


class TestRateLimitHookBadConfig:
    """A recorded cooldown must survive config files of the wrong shape."""

    @pytest.mark.parametrize("config", [{"budget": None}, [], {"budget": []}])
    def test_cooldown_is_recorded_despite_malformed_config(
        self, tmp_path, monkeypatch, config
    ):
        egregore_dir = tmp_path / ".egregore"
        egregore_dir.mkdir()
        (egregore_dir / "manifest.json").write_text(
            json.dumps({"work_items": [{"id": "wrk_001", "status": "active"}]})
        )
        (egregore_dir / "config.json").write_text(json.dumps(config))
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.stdin", StringIO(json.dumps({"error": "rate_limit"})))

        with pytest.raises(SystemExit) as exit_info:
            rate_limit_main()

        assert exit_info.value.code == 0
        recorded = json.loads((egregore_dir / "budget.json").read_text())
        assert recorded["cooldown_until"] is not None


class TestScoutPostDiscussionBadResponse:
    """post_discussion promises None plus a stderr reason, never a raise."""

    @patch("subprocess.run")
    def test_non_json_response_returns_none(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="<html>bad gateway</html>", stderr=""
        )

        url = post_discussion("title", "body", "DIC_x", "owner", "repo")

        assert url is None

    @patch("subprocess.run")
    def test_null_data_in_response_returns_none(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"data": null}', stderr=""
        )

        url = post_discussion("title", "body", "DIC_x", "owner", "repo")

        assert url is None


class TestSaveManifestKeepsLastGoodCopy:
    """The watchdog and Stop hook read the manifest while the loop writes it."""

    def test_failed_write_leaves_the_previous_manifest_intact(
        self, tmp_path, monkeypatch
    ):
        path = tmp_path / ".egregore" / "manifest.json"
        manifest = Manifest(project_dir=str(tmp_path))
        manifest.add_work_item("prompt", "first")
        save_manifest(manifest, path)
        before = path.read_text()

        real_fdopen = os.fdopen

        class _HalfWriter:
            """A file handle whose write lands half its text, then fails."""

            def __init__(self, handle):
                self._handle = handle

            def __enter__(self):
                return self

            def __exit__(self, *exc_info):
                self._handle.close()
                return False

            def write(self, text):
                self._handle.write(text[: len(text) // 2])
                self._handle.flush()
                raise OSError("disk full")

        def half_writing_fdopen(fd, *args, **kwargs):
            return _HalfWriter(real_fdopen(fd, *args, **kwargs))

        monkeypatch.setattr(os, "fdopen", half_writing_fdopen)
        manifest.add_work_item("prompt", "second")
        with pytest.raises(OSError, match="disk full"):
            save_manifest(manifest, path)

        assert path.read_text() == before
        assert len(load_manifest(path).work_items) == 1
