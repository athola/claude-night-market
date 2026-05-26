"""Scanner walks a tree; CLI accepts --focus and emits a report."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from pensive.harden.cli import run_cli
from pensive.harden.scanner import scan_directory


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
