#!/usr/bin/env python3
"""Tests for the supply_chain_scan.py script.

Feature: Supply chain scanning across repository lockfiles

As a marketplace maintainer
I want a script that scans all lockfiles for known compromised versions
So that CI and local make targets can detect supply chain attacks.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# Load the script module dynamically
_SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "supply_chain_scan.py"
_spec = importlib.util.spec_from_file_location("supply_chain_scan", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["supply_chain_scan_script"] = _mod
_spec.loader.exec_module(_mod)

scan_lockfiles = _mod.scan_lockfiles
scan_artifacts = _mod.scan_artifacts
load_blocklist = _mod.load_blocklist


SAMPLE_BLOCKLIST = {
    "badpkg": [
        {
            "versions": ["0.9.9"],
            "date": "2026-01-01",
            "description": "Malicious payload.",
            "indicators": ["evil.pth"],
            "source": "https://example.com/advisory",
            "severity": "critical",
        }
    ]
}


class TestScanLockfiles:
    """
    Feature: Lockfile scanning for compromised versions

    As a CI pipeline
    I want all uv.lock files scanned against a blocklist
    So that compromised versions are caught before deployment.
    """

    @pytest.mark.unit
    def test_detects_compromised_version_in_nested_lockfile(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: Nested plugin lockfile has a bad version
        Given a uv.lock in plugins/foo/ with badpkg==0.9.9
        When scan_lockfiles runs from root
        Then it returns a finding.
        """
        plugin_dir = tmp_path / "plugins" / "foo"
        plugin_dir.mkdir(parents=True)
        lockfile = plugin_dir / "uv.lock"
        lockfile.write_text('[[package]]\nname = "badpkg"\nversion = "0.9.9"\n')
        findings = scan_lockfiles(tmp_path, SAMPLE_BLOCKLIST)
        assert len(findings) == 1
        assert "badpkg" in findings[0]

    @pytest.mark.unit
    def test_clean_repo_returns_empty(self, tmp_path: Path) -> None:
        """
        Scenario: No lockfiles contain compromised versions
        Given a uv.lock with only safe packages
        When scanned
        Then no findings are returned.
        """
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text('[[package]]\nname = "goodpkg"\nversion = "1.0.0"\n')
        findings = scan_lockfiles(tmp_path, SAMPLE_BLOCKLIST)
        assert findings == []

    @pytest.mark.unit
    def test_skips_dotdirs(self, tmp_path: Path) -> None:
        """
        Scenario: Lockfile inside .venv should be skipped
        Given a uv.lock in .venv/ with a compromised version
        When scanned
        Then it is not flagged.
        """
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        lockfile = venv_dir / "uv.lock"
        lockfile.write_text('[[package]]\nname = "badpkg"\nversion = "0.9.9"\n')
        findings = scan_lockfiles(tmp_path, SAMPLE_BLOCKLIST)
        assert findings == []


class TestScanArtifacts:
    """
    Feature: Malicious artifact detection

    As a developer
    I want the scan to find known malicious files
    So that compromised artifacts are detected on disk.
    """

    @pytest.mark.unit
    def test_detects_malicious_artifact(self, tmp_path: Path) -> None:
        """
        Scenario: Malicious .pth file exists
        Given an evil.pth file in the tree
        When scan_artifacts runs
        Then it returns a finding.
        """
        evil_file = tmp_path / "evil.pth"
        evil_file.write_text("import os")
        findings = scan_artifacts(tmp_path, SAMPLE_BLOCKLIST)
        assert len(findings) == 1
        assert "evil.pth" in findings[0]

    @pytest.mark.unit
    def test_clean_tree_returns_empty(self, tmp_path: Path) -> None:
        """
        Scenario: No malicious artifacts present
        Given a clean directory tree
        When scan_artifacts runs
        Then no findings are returned.
        """
        (tmp_path / "normal.py").write_text("pass")
        findings = scan_artifacts(tmp_path, SAMPLE_BLOCKLIST)
        assert findings == []


class TestLoadBlocklist:
    """
    Feature: Blocklist loading

    As the scan script
    I want to load and parse the blocklist JSON
    So that I have the data needed for scanning.
    """

    @pytest.mark.unit
    def test_loads_valid_blocklist(self, tmp_path: Path) -> None:
        """
        Scenario: Valid blocklist exists
        Given a properly formatted known-bad-versions.json
        When loaded
        Then _meta is stripped and package entries are returned.
        """
        blocklist_dir = (
            tmp_path / "plugins" / "leyline" / "skills" / "supply-chain-advisory"
        )
        blocklist_dir.mkdir(parents=True)
        data = {"_meta": {"description": "test"}, "badpkg": [{"versions": ["1.0"]}]}
        (blocklist_dir / "known-bad-versions.json").write_text(json.dumps(data))
        result = load_blocklist(tmp_path)
        assert "_meta" not in result
        assert "badpkg" in result

    @pytest.mark.unit
    def test_returns_empty_when_missing(self, tmp_path: Path) -> None:
        """
        Scenario: No blocklist file exists
        Given an empty directory tree
        When load_blocklist is called
        Then an empty dict is returned.
        """
        result = load_blocklist(tmp_path)
        assert result == {}


class TestScanLockfilesEdgeCases:
    """
    Feature: Lockfile scanning edge cases

    As a CI pipeline
    I want hidden dirs and build caches excluded from scanning
    So that only real project lockfiles are checked.
    """

    @pytest.mark.unit
    def test_skips_node_modules(self, tmp_path: Path) -> None:
        """
        Scenario: Lockfile inside node_modules is ignored
        Given a uv.lock in node_modules/ with a compromised version
        When scanned
        Then it is not flagged.
        """
        nm_dir = tmp_path / "node_modules" / "some-pkg"
        nm_dir.mkdir(parents=True)
        lockfile = nm_dir / "uv.lock"
        lockfile.write_text('[[package]]\nname = "badpkg"\nversion = "0.9.9"\n')
        findings = scan_lockfiles(tmp_path, SAMPLE_BLOCKLIST)
        assert findings == []

    @pytest.mark.unit
    def test_skips_pycache(self, tmp_path: Path) -> None:
        """
        Scenario: Lockfile inside __pycache__ is ignored
        Given a uv.lock in __pycache__/ with a compromised version
        When scanned
        Then it is not flagged.
        """
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        lockfile = cache_dir / "uv.lock"
        lockfile.write_text('[[package]]\nname = "badpkg"\nversion = "0.9.9"\n')
        findings = scan_lockfiles(tmp_path, SAMPLE_BLOCKLIST)
        assert findings == []

    @pytest.mark.unit
    def test_multiple_blocklist_packages(self, tmp_path: Path) -> None:
        """
        Scenario: Blocklist has multiple packages
        Given a blocklist with two packages and a lockfile matching both
        When scanned
        Then findings are returned for each match.
        """
        multi_blocklist = {
            "badpkg": [
                {
                    "versions": ["0.9.9"],
                    "date": "2026-01-01",
                    "description": "Malicious payload.",
                    "indicators": [],
                    "source": "",
                    "severity": "critical",
                }
            ],
            "evillib": [
                {
                    "versions": ["2.0.0"],
                    "date": "2026-02-01",
                    "description": "Data exfiltration.",
                    "indicators": [],
                    "source": "",
                    "severity": "high",
                }
            ],
        }
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text(
            '[[package]]\nname = "badpkg"\nversion = "0.9.9"\n\n'
            '[[package]]\nname = "evillib"\nversion = "2.0.0"\n'
        )
        findings = scan_lockfiles(tmp_path, multi_blocklist)
        assert len(findings) == 2


class TestScanArtifactsEdgeCases:
    """
    Feature: Artifact scanning exclusion rules

    As a developer
    I want artifacts inside hidden dirs excluded
    So that .git or .venv contents do not trigger false positives.
    """

    @pytest.mark.unit
    def test_skips_artifacts_in_dotdirs(self, tmp_path: Path) -> None:
        """
        Scenario: Malicious artifact in .git is ignored
        Given an evil.pth inside .git/hooks/
        When scan_artifacts runs
        Then it is not flagged.
        """
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        (git_dir / "evil.pth").write_text("import os")
        findings = scan_artifacts(tmp_path, SAMPLE_BLOCKLIST)
        assert findings == []


class TestMain:
    """
    Feature: Script main() integration

    As a CI pipeline
    I want main() to return non-zero on findings
    So that the make target fails on compromised dependencies.
    """

    @pytest.mark.unit
    def test_returns_zero_when_blocklist_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: No blocklist file exists
        Given an empty repository
        When main() runs
        Then it returns 0.
        """
        monkeypatch.setattr(
            _mod, "__file__", str(tmp_path / "scripts" / "supply_chain_scan.py")
        )
        (tmp_path / "scripts").mkdir(parents=True)
        result = _mod.main()
        assert result == 0

    @pytest.mark.unit
    def test_returns_one_on_compromised_lockfile(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Lockfile contains a compromised version
        Given a repository with blocklist and bad lockfile
        When main() runs
        Then it returns 1.
        """
        # Create blocklist
        blocklist_dir = (
            tmp_path / "plugins" / "leyline" / "skills" / "supply-chain-advisory"
        )
        blocklist_dir.mkdir(parents=True)
        data = {
            "_meta": {"description": "test"},
            "badpkg": [
                {
                    "versions": ["0.9.9"],
                    "date": "2026-01-01",
                    "description": "Malicious.",
                    "indicators": [],
                    "source": "",
                    "severity": "critical",
                }
            ],
        }
        (blocklist_dir / "known-bad-versions.json").write_text(json.dumps(data))
        # Create bad lockfile
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text('[[package]]\nname = "badpkg"\nversion = "0.9.9"\n')
        # Point main() to our tmp root
        monkeypatch.setattr(
            _mod, "__file__", str(tmp_path / "scripts" / "supply_chain_scan.py")
        )
        (tmp_path / "scripts").mkdir(parents=True)
        result = _mod.main()
        assert result == 1

    @pytest.mark.unit
    def test_returns_zero_on_clean_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: No compromised versions found
        Given a repository with blocklist but clean lockfiles
        When main() runs
        Then it returns 0.
        """
        blocklist_dir = (
            tmp_path / "plugins" / "leyline" / "skills" / "supply-chain-advisory"
        )
        blocklist_dir.mkdir(parents=True)
        data = {
            "_meta": {"description": "test"},
            "badpkg": [
                {
                    "versions": ["0.9.9"],
                    "date": "2026-01-01",
                    "description": "Malicious.",
                    "indicators": [],
                    "source": "",
                    "severity": "critical",
                }
            ],
        }
        (blocklist_dir / "known-bad-versions.json").write_text(json.dumps(data))
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text('[[package]]\nname = "goodpkg"\nversion = "1.0.0"\n')
        monkeypatch.setattr(
            _mod, "__file__", str(tmp_path / "scripts" / "supply_chain_scan.py")
        )
        (tmp_path / "scripts").mkdir(parents=True)
        result = _mod.main()
        assert result == 0
