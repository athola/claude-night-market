"""Tests for the supply_chain_check SessionStart hook.

Feature: Detect compromised package versions in lockfiles

As a developer
I want to be warned at session start if my lockfiles contain known-compromised packages
So that I can take immediate action before working with a compromised environment.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Load the hook module dynamically (same pattern as test_noqa_guard.py)
_HOOK_PATH = Path(__file__).parents[3] / "hooks" / "supply_chain_check.py"
_spec = importlib.util.spec_from_file_location("supply_chain_check", _HOOK_PATH)
assert _spec is not None
assert _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["supply_chain_check"] = _mod
_spec.loader.exec_module(_mod)

_scan_uv_lock = _mod._scan_uv_lock
_scan_requirements = _mod._scan_requirements
_find_blocklist = _mod._find_blocklist


SAMPLE_BLOCKLIST = {
    "litellm": [
        {
            "versions": ["1.82.7", "1.82.8"],
            "date": "2026-03-24",
            "description": "Compromised maintainer credentials. Credential stealer.",
            "indicators": ["litellm_init.pth"],
            "source": "https://docs.litellm.ai/blog/security-update-march-2026",
            "severity": "critical",
        }
    ]
}

COMPROMISED_UV_LOCK = """
[[package]]
name = "litellm"
version = "1.82.7"
source = { registry = "https://pypi.org/simple" }
"""

SAFE_UV_LOCK = """
[[package]]
name = "litellm"
version = "1.81.15"
source = { registry = "https://pypi.org/simple" }
"""

UNRELATED_UV_LOCK = """
[[package]]
name = "requests"
version = "2.31.0"
source = { registry = "https://pypi.org/simple" }
"""


class TestScanUvLock:
    """Feature: uv.lock scanning for compromised versions

    As a developer using uv for dependency management
    I want lockfiles checked against a blocklist
    So that compromised packages are detected before use.
    """

    @pytest.mark.unit
    def test_detects_compromised_version(self, tmp_path: Path) -> None:
        """Scenario: lockfile contains a known-bad version
        Given a uv.lock with litellm==1.82.7
        When scanned against the blocklist
        Then a finding is returned with severity and description.
        """
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text(COMPROMISED_UV_LOCK)
        findings = _scan_uv_lock(lockfile, SAMPLE_BLOCKLIST)
        assert len(findings) == 1
        assert findings[0]["package"] == "litellm"
        assert findings[0]["version"] == "1.82.7"
        assert findings[0]["severity"] == "critical"

    @pytest.mark.unit
    def test_ignores_safe_version(self, tmp_path: Path) -> None:
        """Scenario: lockfile contains a safe version
        Given a uv.lock with litellm==1.81.15
        When scanned against the blocklist
        Then no findings are returned.
        """
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text(SAFE_UV_LOCK)
        findings = _scan_uv_lock(lockfile, SAMPLE_BLOCKLIST)
        assert findings == []

    @pytest.mark.unit
    def test_ignores_unrelated_packages(self, tmp_path: Path) -> None:
        """Scenario: lockfile has no packages in the blocklist
        Given a uv.lock with only unrelated packages
        When scanned
        Then no findings are returned.
        """
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text(UNRELATED_UV_LOCK)
        findings = _scan_uv_lock(lockfile, SAMPLE_BLOCKLIST)
        assert findings == []

    @pytest.mark.unit
    def test_detects_both_compromised_versions(self, tmp_path: Path) -> None:
        """Scenario: lockfile somehow references both bad versions
        Given a uv.lock with both 1.82.7 and 1.82.8
        When scanned
        Then two findings are returned.
        """
        lockfile = tmp_path / "uv.lock"
        content = (
            COMPROMISED_UV_LOCK
            + """
[[package]]
name = "litellm"
version = "1.82.8"
source = { registry = "https://pypi.org/simple" }
"""
        )
        lockfile.write_text(content)
        findings = _scan_uv_lock(lockfile, SAMPLE_BLOCKLIST)
        assert len(findings) == 2
        versions = {f["version"] for f in findings}
        assert versions == {"1.82.7", "1.82.8"}

    @pytest.mark.unit
    def test_empty_blocklist_returns_nothing(self, tmp_path: Path) -> None:
        """Scenario: blocklist is empty
        Given an empty blocklist
        When any lockfile is scanned
        Then no findings are returned.
        """
        lockfile = tmp_path / "uv.lock"
        lockfile.write_text(COMPROMISED_UV_LOCK)
        findings = _scan_uv_lock(lockfile, {})
        assert findings == []


class TestScanRequirements:
    """Feature: requirements.txt scanning for compromised versions

    As a developer using pip-style requirements
    I want pinned requirements checked against a blocklist
    So that compromised packages are caught in legacy setups too.
    """

    @pytest.mark.unit
    def test_detects_compromised_pinned_version(self, tmp_path: Path) -> None:
        """Scenario: requirements.txt pins a compromised version
        Given requirements.txt with litellm==1.82.7
        When scanned
        Then a finding is returned.
        """
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text("litellm==1.82.7\nrequests==2.31.0\n")
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert len(findings) == 1
        assert findings[0]["package"] == "litellm"

    @pytest.mark.unit
    def test_ignores_safe_pinned_version(self, tmp_path: Path) -> None:
        """Scenario: requirements.txt pins a safe version
        Given requirements.txt with litellm==1.81.15
        When scanned
        Then no findings are returned.
        """
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text("litellm==1.81.15\n")
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert findings == []

    @pytest.mark.unit
    def test_handles_environment_markers(self, tmp_path: Path) -> None:
        """Scenario: requirement line has environment markers
        Given litellm==1.82.7; python_version>="3.9"
        When scanned
        Then the version is still detected.
        """
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text('litellm==1.82.7; python_version>="3.9"\n')
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert len(findings) == 1

    @pytest.mark.unit
    def test_skips_comments(self, tmp_path: Path) -> None:
        """Scenario: comment line mentions compromised version
        Given a comment like # litellm==1.82.7
        When scanned
        Then it is not flagged.
        """
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text("# litellm==1.82.7\nrequests==2.31.0\n")
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert findings == []


class TestFindBlocklist:
    """Feature: Blocklist discovery

    As a hook
    I want to find the blocklist via CLAUDE_PLUGIN_ROOT or relative path
    So that it works in both installed and development contexts.
    """

    @pytest.mark.unit
    def test_finds_blocklist_via_plugin_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: CLAUDE_PLUGIN_ROOT is set and blocklist exists
        Given CLAUDE_PLUGIN_ROOT points to a directory with the blocklist
        When _find_blocklist is called
        Then it returns the path.
        """
        skill_dir = tmp_path / "skills" / "supply-chain-advisory"
        skill_dir.mkdir(parents=True)
        blocklist = skill_dir / "known-bad-versions.json"
        blocklist.write_text("{}")
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        result = _find_blocklist()
        assert result is not None
        assert result == blocklist

    @pytest.mark.unit
    def test_returns_none_when_no_blocklist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: No blocklist exists anywhere
        Given CLAUDE_PLUGIN_ROOT points to empty directory
        When _find_blocklist is called
        Then it returns None.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        # Also ensure the relative path won't find it
        monkeypatch.setattr(_mod, "__file__", str(tmp_path / "fake_hook.py"))
        result = _find_blocklist()
        assert result is None

    @pytest.mark.unit
    def test_falls_back_to_relative_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: CLAUDE_PLUGIN_ROOT not set but relative path works
        Given no CLAUDE_PLUGIN_ROOT env var
        And blocklist exists relative to the hook file
        When _find_blocklist is called
        Then it returns the path via relative fallback.
        """
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
        # Simulate hook at <plugin>/hooks/supply_chain_check.py
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        skill_dir = tmp_path / "skills" / "supply-chain-advisory"
        skill_dir.mkdir(parents=True)
        blocklist = skill_dir / "known-bad-versions.json"
        blocklist.write_text("{}")
        monkeypatch.setattr(_mod, "__file__", str(hooks_dir / "supply_chain_check.py"))
        result = _find_blocklist()
        assert result is not None
        assert result == blocklist


class TestScanRequirementsEdgeCases:
    """Feature: requirements.txt edge cases

    As a developer
    I want non-pinned and varied format lines handled correctly
    So that scanning is precise and avoids false positives.
    """

    @pytest.mark.unit
    def test_ignores_unpinned_requirements(self, tmp_path: Path) -> None:
        """Scenario: requirement uses >= instead of ==
        Given requirements.txt with litellm>=1.82.7
        When scanned
        Then no findings are returned (only exact pins checked).
        """
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text("litellm>=1.82.7\n")
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert findings == []

    @pytest.mark.unit
    def test_case_insensitive_package_matching(self, tmp_path: Path) -> None:
        """Scenario: requirement has mixed-case package name
        Given requirements.txt with LiteLLM==1.82.7
        When scanned
        Then the finding is still detected via case-insensitive match.
        """
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text("LiteLLM==1.82.7\n")
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert len(findings) == 1

    @pytest.mark.unit
    def test_empty_requirements_file(self, tmp_path: Path) -> None:
        """Scenario: requirements file is empty
        Given an empty requirements.txt
        When scanned
        Then no findings are returned.
        """
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text("")
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert findings == []


class TestMainIntegration:
    """Feature: Hook main() integration

    As a session startup hook
    I want main() to output JSON warnings on findings
    And silently succeed when no issues are found.
    """

    @pytest.mark.unit
    def test_silent_when_no_blocklist(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Scenario: No blocklist exists
        Given CLAUDE_PLUGIN_ROOT points to empty directory
        When main() runs
        Then no output is produced.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        monkeypatch.setattr(_mod, "__file__", str(tmp_path / "fake.py"))
        _mod.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    @pytest.mark.unit
    def test_emits_json_on_finding(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Scenario: Compromised version found in lockfile
        Given a blocklist with litellm 1.82.7 and a matching uv.lock
        When main() runs
        Then JSON output with additionalContext is printed.
        """
        # Set up blocklist
        skill_dir = tmp_path / "skills" / "supply-chain-advisory"
        skill_dir.mkdir(parents=True)
        (skill_dir / "known-bad-versions.json").write_text(json.dumps(SAMPLE_BLOCKLIST))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))

        # Set up compromised lockfile in cwd
        project = tmp_path / "project"
        project.mkdir()
        (project / "uv.lock").write_text(COMPROMISED_UV_LOCK)
        monkeypatch.chdir(project)

        _mod.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        hook_output = result["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "SessionStart"
        assert "SUPPLY CHAIN ALERT" in hook_output["additionalContext"]
        assert "litellm" in hook_output["additionalContext"]

    @pytest.mark.unit
    def test_silent_when_no_findings(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Scenario: Blocklist exists but no matches in lockfiles
        Given a blocklist and a clean uv.lock
        When main() runs
        Then no output is produced.
        """
        skill_dir = tmp_path / "skills" / "supply-chain-advisory"
        skill_dir.mkdir(parents=True)
        (skill_dir / "known-bad-versions.json").write_text(json.dumps(SAMPLE_BLOCKLIST))
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))

        project = tmp_path / "project"
        project.mkdir()
        (project / "uv.lock").write_text(SAFE_UV_LOCK)
        monkeypatch.chdir(project)

        _mod.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    @pytest.mark.unit
    def test_graceful_on_malformed_blocklist(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Scenario: Blocklist file contains invalid JSON
        Given a blocklist file with corrupted JSON
        When main() runs
        Then no output is produced and hook does not crash.
        """
        skill_dir = tmp_path / "skills" / "supply-chain-advisory"
        skill_dir.mkdir(parents=True)
        (skill_dir / "known-bad-versions.json").write_text("{not valid json!!!")
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))

        _mod.main()
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "supply_chain_check: failed to parse blocklist" in captured.err

    @pytest.mark.unit
    def test_never_crashes(self, tmp_path: Path) -> None:
        """Scenario: Hook must never crash the session
        Given malformed stdin and an undecodable uv.lock in the project
        When the hook runs as a process
        Then it exits 0 and writes nothing to stdout.
        """
        (tmp_path / "uv.lock").write_bytes(b"\xff\xfe not utf-8 [[package]")
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            input="{not json",
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env={"CLAUDE_PLUGIN_ROOT": str(_HOOK_PATH.parents[1])},
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_crash_handler_logs_to_stderr(self, tmp_path: Path) -> None:
        """Scenario: Top-level crash handler writes traceback to stderr.

        Given a blocklist and a uv.lock that is not valid UTF-8
        When the hook runs as a process and main() raises while reading it
        Then the __main__ guard names the hook and the error on stderr
        And the process still exits 0 with nothing on stdout.
        """
        (tmp_path / "uv.lock").write_bytes(b"\xff\xfe not utf-8 [[package]")
        result = subprocess.run(
            [sys.executable, str(_HOOK_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env={"CLAUDE_PLUGIN_ROOT": str(_HOOK_PATH.parents[1])},
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout == ""
        assert "supply_chain_check: unexpected error" in result.stderr
        assert "UnicodeDecodeError" in result.stderr

    @staticmethod
    def _install_blocklist(root: Path, blocklist: dict) -> None:
        skill_dir = root / "skills" / "supply-chain-advisory"
        skill_dir.mkdir(parents=True)
        (skill_dir / "known-bad-versions.json").write_text(json.dumps(blocklist))

    @pytest.mark.unit
    def test_meta_only_blocklist_is_silent(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A blocklist holding only ``_meta`` has no packages to match."""
        self._install_blocklist(tmp_path, {"_meta": {"updated": "2026-03-24"}})
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        project = tmp_path / "project"
        project.mkdir()
        (project / "uv.lock").write_text(COMPROMISED_UV_LOCK)
        monkeypatch.chdir(project)

        _mod.main()

        assert capsys.readouterr().out == ""

    @pytest.mark.unit
    def test_lockfile_inside_a_virtualenv_is_not_scanned(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A uv.lock under .venv belongs to an installed package, not the project."""
        self._install_blocklist(tmp_path, SAMPLE_BLOCKLIST)
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        project = tmp_path / "project"
        vendored = project / ".venv" / "lib" / "pkg"
        vendored.mkdir(parents=True)
        (vendored / "uv.lock").write_text(COMPROMISED_UV_LOCK)
        monkeypatch.chdir(project)

        _mod.main()

        assert capsys.readouterr().out == ""

    @pytest.mark.unit
    def test_compromised_pin_in_requirements_file_is_reported(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A requirements-dev.txt pin is scanned alongside uv.lock."""
        self._install_blocklist(tmp_path, SAMPLE_BLOCKLIST)
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        project = tmp_path / "project"
        project.mkdir()
        (project / "requirements-dev.txt").write_text("litellm==1.82.8\n")
        monkeypatch.chdir(project)

        _mod.main()

        context = json.loads(capsys.readouterr().out)["hookSpecificOutput"][
            "additionalContext"
        ]
        assert "SUPPLY CHAIN ALERT: litellm==1.82.8 (CRITICAL)" in context
        assert "Scan for: litellm_init.pth" in context


class TestRequirementLineForms:
    """Every pip-accepted spelling of a pin is read as that pin."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "body",
        [
            "litellm==1.82.7 \\\n    --hash=sha256:abc\n",
            "litellm[proxy]==1.82.7\n",
            "LiteLLM == 1.82.7\n",
            "litellm==1.82.7  # pinned for the proxy\n",
        ],
    )
    def test_a_compromised_pin_is_found_in_every_form(
        self, tmp_path: Path, body: str
    ) -> None:
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text(body)
        findings = _scan_requirements(reqfile, SAMPLE_BLOCKLIST)
        assert [f["version"] for f in findings] == ["1.82.7"]

    @pytest.mark.unit
    def test_names_compare_under_pep_503(self, tmp_path: Path) -> None:
        blocklist = {
            "foo-bar": [dict(SAMPLE_BLOCKLIST["litellm"][0], versions=["1.0"])]
        }
        reqfile = tmp_path / "requirements.txt"
        reqfile.write_text("Foo_Bar==1.0\n")
        assert len(_scan_requirements(reqfile, blocklist)) == 1


class TestLockfileWalk:
    """The SessionStart walk skips trees that are not the project's own."""

    @pytest.mark.unit
    def test_vendored_trees_are_not_walked(self, tmp_path: Path) -> None:
        for skipped in (".venv", "node_modules", ".git"):
            (tmp_path / skipped / "pkg").mkdir(parents=True)
            (tmp_path / skipped / "pkg" / "uv.lock").write_text("")
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "uv.lock").write_text("")

        found = list(_mod._project_lockfiles(tmp_path))

        assert found == [tmp_path / "app" / "uv.lock"]
