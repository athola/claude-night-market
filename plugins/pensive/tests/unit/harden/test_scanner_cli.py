"""Scanner walks a tree; CLI accepts --focus and emits a report."""

from __future__ import annotations

import json
import pathlib
import textwrap
from typing import TYPE_CHECKING

from pensive.harden.cli import run_cli
from pensive.harden.scanner import scan_directory

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


class TestScannerWalksDir:
    def test_walk_finds_findings_across_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text(
            textwrap.dedent("""
                import yaml
                def parse(s):
                    return yaml.load(s)
            """)
        )
        (tmp_path / "b.py").write_text(
            textwrap.dedent("""
                import requests
                def fetch(url):
                    return requests.get(url)
            """)
        )
        # Files that should not be scanned.
        (tmp_path / "README.md").write_text("# hi")
        (tmp_path / "data.json").write_text("{}")

        findings = scan_directory(tmp_path)
        ids = sorted({getattr(f, "id", "?") for f in findings})
        assert "PY02" in ids
        assert "PY20" in ids


class TestScannerSkipsVendored:
    def test_node_modules_skipped(self, tmp_path: Path) -> None:
        vendored = tmp_path / "node_modules" / "pkg"
        vendored.mkdir(parents=True)
        (vendored / "evil.py").write_text("import yaml\nyaml.load('x')\n")

        own = tmp_path / "own.py"
        own.write_text("import requests\nrequests.get('http://x')\n")

        findings = scan_directory(tmp_path)
        files = {getattr(f, "file", "?") for f in findings}
        assert any(p.endswith("own.py") for p in files)
        # Strip the tmp_path prefix before substring-checking, because
        # pytest names the per-test tmpdir after the test (here
        # "test_node_modules_skipped0"), which would always contain
        # the "node_modules" substring even when the scanner skipped
        # the actual node_modules dir correctly.
        scanned_segments = [p[len(str(tmp_path)) :] for p in files]
        assert not any("node_modules" in seg for seg in scanned_segments)

    def test_uv_cache_skipped(self, tmp_path: Path) -> None:
        # Revert guard (issue #575, B4): if ".uv-cache" is removed from
        # _SKIP_COMPONENTS, the cached file is scanned and this fails.
        cached = tmp_path / ".uv-cache" / "pkg"
        cached.mkdir(parents=True)
        (cached / "evil.py").write_text("import yaml\nyaml.load('x')\n")

        own = tmp_path / "own.py"
        own.write_text("import requests\nrequests.get('http://x')\n")

        findings = scan_directory(tmp_path)
        files = {getattr(f, "file", "?") for f in findings}
        assert any(p.endswith("own.py") for p in files)
        scanned_segments = [p[len(str(tmp_path)) :] for p in files]
        assert not any(".uv-cache" in seg for seg in scanned_segments)

    def test_cargo_skipped(self, tmp_path: Path) -> None:
        # Revert guard (issue #575, B4): if ".cargo" is removed from
        # _SKIP_COMPONENTS, the cached file is scanned and this fails.
        cached = tmp_path / ".cargo" / "registry"
        cached.mkdir(parents=True)
        (cached / "evil.py").write_text("import yaml\nyaml.load('x')\n")

        own = tmp_path / "own.py"
        own.write_text("import requests\nrequests.get('http://x')\n")

        findings = scan_directory(tmp_path)
        files = {getattr(f, "file", "?") for f in findings}
        assert any(p.endswith("own.py") for p in files)
        scanned_segments = [p[len(str(tmp_path)) :] for p in files]
        assert not any(".cargo" in seg for seg in scanned_segments)

    def test_project_under_a_target_directory_is_scanned(self, tmp_path: Path) -> None:
        # Only components below the scan root name a vendored tree. A
        # project checked out under /target/ is the project, not output.
        root = tmp_path / "target" / "proj"
        root.mkdir(parents=True)
        (root / "own.py").write_text("import requests\nrequests.get('http://x')\n")

        files = {getattr(f, "file", "?") for f in scan_directory(root)}
        assert any(p.endswith("own.py") for p in files)


class TestScannerSurfacesUnreadable:
    def test_unreadable_file_yields_advisory(self, tmp_path: Path) -> None:
        # Issue #575, B2: a file the scanner cannot read used to be
        # dropped silently, making it invisible to --strict. It must
        # now surface an ADVISORY finding.
        # A directory whose name ends in .py: rglob matches it, but
        # read_text() raises IsADirectoryError (an OSError subclass).
        (tmp_path / "unreadable.py").mkdir()

        findings = scan_directory(tmp_path)
        advisories = [f for f in findings if getattr(f, "severity", "") == "ADVISORY"]
        assert any("unreadable.py" in getattr(f, "file", "") for f in advisories)


class TestCliEntryPoint:
    def test_cli_emits_json(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "x.py").write_text(
            textwrap.dedent("""
                import yaml
                yaml.load("foo")
            """)
        )
        rc = run_cli(["--path", str(tmp_path), "--json"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["success"] is True
        assert payload["data"]["finding_count"] >= 1
        assert any(f["id"] == "PY02" for f in payload["data"]["findings"])

    def test_cli_strict_returns_nonzero_on_findings(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "x.py").write_text("import yaml\nyaml.load('foo')\n")
        rc = run_cli(["--path", str(tmp_path), "--strict", "--json"])
        # Strict + non-empty findings -> non-zero exit.
        assert rc != 0

    def test_cli_clean_path_returns_zero(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "ok.py").write_text("import json\njson.loads('{}')\n")
        rc = run_cli(["--path", str(tmp_path), "--strict", "--json"])
        # Clean + strict -> zero.
        assert rc == 0


class TestTheScannerProvesItScannedSomething:
    """Feature: zero files scanned is not "no findings".

    A typo'd path, a tree with no Python, or a permission wall all gave
    an empty rglob, and the CLI printed the clean line and exited 0,
    including under --strict, the CI mode. tome's answer to the same
    shape is a positive control (ADR-0020): prove the scanner can see
    before its silence counts. The planted fixture is that control.
    """

    _PLANTED = (
        pathlib.Path(__file__).resolve().parents[2]
        / "fixtures"
        / "harden"
        / "planted.py"
    )

    def test_an_empty_tree_is_not_reported_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Given a directory with no Python sources
        When the CLI runs
        Then it exits nonzero and says nothing was scanned
        """
        code = run_cli(["--path", str(tmp_path)])
        assert code != 0
        assert "nothing was scanned" in capsys.readouterr().out

    def test_json_carries_files_scanned(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "clean.py").write_text("x = 1\n")
        code = run_cli(["--path", str(tmp_path), "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert code == 0
        assert payload["data"]["files_scanned"] == 1
        assert payload["data"]["finding_count"] == 0

    def test_the_planted_fixture_fails_strict_mode(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """
        Given the committed fixture with a pickle.loads and an untimed subprocess
        When the CLI runs in --strict mode over its directory
        Then it exits 2

            If this passes clean, the scanner is blind and every
            "no findings" elsewhere is unearned.
        """
        assert self._PLANTED.is_file()
        code = run_cli(["--path", str(self._PLANTED.parent), "--strict"])
        out = capsys.readouterr().out
        assert code == 2, out
