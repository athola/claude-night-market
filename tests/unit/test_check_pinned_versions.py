"""Tests for the check_pinned_versions pre-commit script.

Feature: Block when a pinned CI action or pre-commit hook lags upstream

As a maintainer
I want pre-commit to fail when our GitHub-sourced tooling pins fall behind
So that CI actions and pre-commit hooks stay current deliberately

Companion to check_ruff_version (PyPI-sourced). This script covers the
GitHub-sourced pins: ``uses: owner/repo@ref`` in .github/workflows and
external ``rev:`` pins in .pre-commit-config.yaml.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_pinned_versions as cpv

PRECOMMIT_SAMPLE = """repos:
  - repo: local
    hooks:
      - id: noop
        name: noop
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
  - repo: https://github.com/pycqa/bandit
    rev: 1.8.3
    hooks:
      - id: bandit
"""

WORKFLOW_SAMPLE = """jobs:
  build:
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: github/codeql-action/upload-sarif@v4
      - uses: ./.github/actions/local-thing
      - uses: docker://alpine:3.20
      - uses: actions/checkout@v4
"""


class TestPrecommitPins:
    """Scenario: parse external GitHub repo rev pins from config text."""

    @pytest.mark.unit
    def test_extracts_github_repo_and_rev(self):
        """
        GIVEN config text listing two external GitHub repos
        WHEN precommit_pins parses it
        THEN both repo/rev pairs are returned
        AND each pair carries the rev declared in the config
        """
        pins = cpv.precommit_pins(PRECOMMIT_SAMPLE)
        assert ("pre-commit/pre-commit-hooks", "v6.0.0") in pins
        assert ("pycqa/bandit", "1.8.3") in pins

    @pytest.mark.unit
    def test_ignores_local_repo(self):
        """
        GIVEN a config containing a ``repo: local`` block
        WHEN precommit_pins parses it
        THEN no local repo is returned
        AND only the two external pins remain
        """
        pins = cpv.precommit_pins(PRECOMMIT_SAMPLE)
        assert all(not repo.startswith("local") for repo, _ in pins)
        assert len(pins) == 2


class TestWorkflowActionPins:
    """Scenario: parse ``uses: owner/repo@ref`` pins from workflow text."""

    @pytest.mark.unit
    def test_extracts_owner_repo_and_ref(self):
        """
        GIVEN a workflow step using owner/repo@ref
        WHEN workflow_action_pins parses it
        THEN the owner/repo and ref are returned
        AND both sampled actions are present
        """
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        assert ("actions/checkout", "v4") in pins
        assert ("astral-sh/setup-uv", "v4") in pins

    @pytest.mark.unit
    def test_strips_subpath_to_repo_root(self):
        """
        GIVEN a step using owner/repo/subpath@ref
        WHEN workflow_action_pins parses it
        THEN the repo is reduced to owner/repo
        AND no subpath segment survives in any repo
        """
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        assert ("github/codeql-action", "v4") in pins
        assert all("/upload-sarif" not in repo for repo, _ in pins)

    @pytest.mark.unit
    def test_skips_local_and_docker_actions(self):
        """
        GIVEN steps using ./local and docker:// references
        WHEN workflow_action_pins parses them
        THEN neither local nor docker actions are returned
        AND no remaining repo starts with a path or docker prefix
        """
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        repos = [repo for repo, _ in pins]
        assert not any(r.startswith(".") for r in repos)
        assert not any("docker" in r for r in repos)

    @pytest.mark.unit
    def test_dedupes_repeated_pins(self):
        """
        GIVEN checkout@v4 listed twice in the workflow
        WHEN workflow_action_pins parses it
        THEN the pin appears exactly once
        AND duplicate entries collapse into a single pair
        """
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        assert pins.count(("actions/checkout", "v4")) == 1


class TestIsBehind:
    """Scenario: compare at the granularity of the pinned ref."""

    @pytest.mark.unit
    def test_major_pin_behind_on_new_major(self):
        """
        GIVEN a major-only pin @v4 and latest release v5.0.0
        WHEN is_behind compares them
        THEN the pin is reported behind
        AND only the major component drives the verdict
        """
        assert cpv.is_behind("v4", "v5.0.0") is True

    @pytest.mark.unit
    def test_major_pin_current_on_same_major(self):
        """
        GIVEN a major-only pin @v4 and latest release v4.2.2
        WHEN is_behind compares them
        THEN the pin is reported current
        AND the trailing patch version is ignored
        """
        assert cpv.is_behind("v4", "v4.2.2") is False

    @pytest.mark.unit
    def test_full_pin_behind_on_minor_bump(self):
        """
        GIVEN a full pin v6.0.0 and latest release v6.1.0
        WHEN is_behind compares them
        THEN the pin is reported behind
        AND the minor component is compared, not just the major
        """
        assert cpv.is_behind("v6.0.0", "v6.1.0") is True

    @pytest.mark.unit
    def test_full_pin_current_when_equal(self):
        """
        GIVEN a full pin 1.8.3 and an identical latest release
        WHEN is_behind compares them
        THEN the pin is reported current
        AND equal versions are never flagged behind
        """
        assert cpv.is_behind("1.8.3", "1.8.3") is False

    @pytest.mark.unit
    def test_non_numeric_pin_is_never_behind(self):
        """
        GIVEN a pin with no numeric components such as ``main``
        WHEN is_behind compares it against any release
        THEN it is reported current rather than behind
        AND an unversioned ref can never trigger a block
        """
        assert cpv.is_behind("main", "v5.0.0") is False
        assert cpv.is_behind("latest", "v9.9.9") is False

    @pytest.mark.unit
    def test_avoids_string_ordering_trap(self):
        """
        GIVEN a pin @v9 and latest release v10
        WHEN is_behind compares them
        THEN the pin is reported behind
        AND the compare is numeric rather than lexical
        """
        assert cpv.is_behind("v9", "v10") is True

    @pytest.mark.unit
    def test_sha_pin_is_never_behind(self):
        """
        GIVEN a commit-SHA action pin (the GitHub-recommended secure form)
        WHEN is_behind compares it against a dotted release tag
        THEN it is reported current, not behind
        AND a SHA whose leading hex run is below the upstream major cannot
            wedge a commit under blocking mode
        """
        assert (
            cpv.is_behind("0a1b2c3d4e5f60718293a4b5c6d7e8f901234567", "v4.2.2") is False
        )
        assert cpv.is_behind("abc1234", "v9.9.9") is False
        # A real dotted tag is still compared normally.
        assert cpv.is_behind("v3.0.0", "v4.0.0") is True


class TestMain:
    """Scenario: blocking by default; skip cleanly when unresolvable."""

    @pytest.mark.unit
    def test_behind_blocking_exits_one_with_notice(self, monkeypatch, capsys):
        """
        GIVEN a behind pin while blocking mode is enabled
        WHEN main runs
        THEN it exits 1
        AND the stderr notice names the repo and both versions
        """
        monkeypatch.setattr(
            cpv,
            "collect_pins",
            lambda: [("actions/checkout", "v4", "ci")],
        )
        monkeypatch.setattr(cpv, "latest_github_tag", lambda _repo: "v5.0.0")
        monkeypatch.setattr(cpv, "OUTDATED_IS_BLOCKING", True)
        assert cpv.main() == 1
        err = capsys.readouterr().err
        assert "actions/checkout" in err
        assert "v4" in err and "v5.0.0" in err

    @pytest.mark.unit
    def test_held_back_pin_does_not_block(self, monkeypatch, capsys):
        """
        GIVEN a behind pin listed in HELD_BACK while blocking mode is on
        WHEN main runs
        THEN it exits 0 (the deliberate hold is honored, not blocked)
        AND stdout records the hold with both versions
        """
        monkeypatch.setattr(
            cpv,
            "collect_pins",
            lambda: [("pycqa/bandit", "1.8.6", "pre-commit")],
        )
        monkeypatch.setattr(cpv, "latest_github_tag", lambda _repo: "1.9.4")
        monkeypatch.setattr(cpv, "OUTDATED_IS_BLOCKING", True)
        monkeypatch.setattr(cpv, "HELD_BACK", {"pycqa/bandit": "py3.9 floor"})
        assert cpv.main() == 0
        out = capsys.readouterr().out
        assert "holding pycqa/bandit" in out
        assert "1.8.6" in out and "1.9.4" in out

    @pytest.mark.unit
    def test_hold_does_not_mask_other_behind_pins(self, monkeypatch, capsys):
        """
        GIVEN one held-back pin and one ordinary pin, both behind upstream
        WHEN main runs in blocking mode
        THEN it still exits 1 for the ordinary pin
        AND only the ordinary pin appears in the blocking notice
        """
        monkeypatch.setattr(
            cpv,
            "collect_pins",
            lambda: [
                ("pycqa/bandit", "1.8.6", "pre-commit"),
                ("actions/checkout", "v4", "ci"),
            ],
        )
        monkeypatch.setattr(
            cpv,
            "latest_github_tag",
            lambda repo: "1.9.4" if repo == "pycqa/bandit" else "v5.0.0",
        )
        monkeypatch.setattr(cpv, "OUTDATED_IS_BLOCKING", True)
        monkeypatch.setattr(cpv, "HELD_BACK", {"pycqa/bandit": "py3.9 floor"})
        assert cpv.main() == 1
        err = capsys.readouterr().err
        assert "actions/checkout" in err
        assert "pycqa/bandit" not in err

    @pytest.mark.unit
    def test_behind_advisory_exits_zero(self, monkeypatch, capsys):
        """
        GIVEN a behind pin while advisory (non-blocking) mode is set
        WHEN main runs
        THEN it exits 0
        AND the behind repo is still named on stderr
        """
        monkeypatch.setattr(
            cpv,
            "collect_pins",
            lambda: [("actions/checkout", "v4", "ci")],
        )
        monkeypatch.setattr(cpv, "latest_github_tag", lambda _repo: "v5.0.0")
        monkeypatch.setattr(cpv, "OUTDATED_IS_BLOCKING", False)
        assert cpv.main() == 0
        assert "actions/checkout" in capsys.readouterr().err

    @pytest.mark.unit
    def test_all_current_exits_zero(self, monkeypatch, capsys):
        """
        GIVEN every discovered pin is at its latest release
        WHEN main runs
        THEN it exits 0
        AND the report states the pins are current
        """
        monkeypatch.setattr(
            cpv,
            "collect_pins",
            lambda: [("pycqa/bandit", "1.8.3", "pre-commit")],
        )
        monkeypatch.setattr(cpv, "latest_github_tag", lambda _repo: "1.8.3")
        assert cpv.main() == 0
        assert "current" in capsys.readouterr().out.lower()

    @pytest.mark.unit
    def test_unresolvable_pin_does_not_block(self, monkeypatch, capsys):
        """
        GIVEN the latest tag for a pin cannot be fetched
        WHEN main runs in blocking mode
        THEN it exits 0 rather than blocking on missing data
        AND the unresolved pin is reported as skipped
        """
        monkeypatch.setattr(
            cpv,
            "collect_pins",
            lambda: [("actions/checkout", "v4", "ci")],
        )
        monkeypatch.setattr(cpv, "latest_github_tag", lambda _repo: None)
        monkeypatch.setattr(cpv, "OUTDATED_IS_BLOCKING", True)
        assert cpv.main() == 0
        assert "skip" in capsys.readouterr().out.lower()

    @pytest.mark.unit
    def test_mixed_one_behind_blocks(self, monkeypatch):
        """
        GIVEN one current pin, one unresolved, and one behind
        WHEN main runs in blocking mode
        THEN it exits 1
        AND a single behind pin is enough to block
        """
        monkeypatch.setattr(
            cpv,
            "collect_pins",
            lambda: [
                ("pycqa/bandit", "1.8.3", "pre-commit"),
                ("actions/setup-python", "v5", "ci"),
                ("actions/checkout", "v4", "ci"),
            ],
        )
        tags = {
            "pycqa/bandit": "1.8.3",
            "actions/setup-python": None,
            "actions/checkout": "v5.1.0",
        }
        monkeypatch.setattr(cpv, "latest_github_tag", lambda repo: tags[repo])
        monkeypatch.setattr(cpv, "OUTDATED_IS_BLOCKING", True)
        assert cpv.main() == 1

    @pytest.mark.unit
    def test_no_pins_exits_zero(self, monkeypatch):
        """
        GIVEN no pins are discovered at all
        WHEN main runs
        THEN it exits 0 cleanly
        AND an empty pin set is treated as success
        """
        monkeypatch.setattr(cpv, "collect_pins", lambda: [])
        assert cpv.main() == 0


class TestCollectPinsErrorHandling:
    """Scenario: unreadable config or workflow files degrade gracefully.

    collect_pins reads real files off disk, so an OSError (permission
    denied, vanished symlink, transient I/O) must not crash the hook.
    The contract is warn-to-stderr-and-continue: skip the unreadable
    file, keep collecting from every readable one.
    """

    @pytest.mark.unit
    def test_unreadable_precommit_config_skips_without_crash(
        self, tmp_path, monkeypatch, capsys
    ):
        """
        GIVEN a pre-commit config whose read raises OSError
        WHEN collect_pins runs with no workflows to scan
        THEN it returns no pins instead of raising
        AND it writes a skip notice naming the config to stderr
        """
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text(PRECOMMIT_SAMPLE, encoding="utf-8")
        empty_workflows = tmp_path / "workflows"
        empty_workflows.mkdir()
        monkeypatch.setattr(cpv, "PRECOMMIT_CONFIG", str(config))
        monkeypatch.setattr(cpv, "WORKFLOWS_DIR", str(empty_workflows))

        real_read_text = Path.read_text

        def boom(self, *args, **kwargs):
            if self.name == ".pre-commit-config.yaml":
                raise OSError("permission denied")
            return real_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", boom)

        pins = cpv.collect_pins()

        assert pins == []
        err = capsys.readouterr().err
        assert "skip" in err.lower()
        assert ".pre-commit-config.yaml" in err

    @pytest.mark.unit
    def test_unreadable_workflow_is_skipped_readable_one_collected(
        self, tmp_path, monkeypatch, capsys
    ):
        """
        GIVEN two workflow files where exactly one raises OSError on read
        WHEN collect_pins scans the workflows directory
        THEN the readable workflow's pins are still collected
        AND the unreadable workflow is named in a stderr skip notice
        """
        missing_config = tmp_path / "absent.yaml"
        workflows = tmp_path / "workflows"
        workflows.mkdir()
        (workflows / "good.yml").write_text(WORKFLOW_SAMPLE, encoding="utf-8")
        (workflows / "bad.yml").write_text(WORKFLOW_SAMPLE, encoding="utf-8")
        monkeypatch.setattr(cpv, "PRECOMMIT_CONFIG", str(missing_config))
        monkeypatch.setattr(cpv, "WORKFLOWS_DIR", str(workflows))

        real_read_text = Path.read_text

        def boom(self, *args, **kwargs):
            if self.name == "bad.yml":
                raise OSError("input/output error")
            return real_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", boom)

        pins = cpv.collect_pins()

        repos = {repo for repo, _ref, _src in pins}
        assert "actions/checkout" in repos
        assert all(src == "ci" for _repo, _ref, src in pins)
        err = capsys.readouterr().err
        assert "skip" in err.lower()
        assert "bad.yml" in err

    @pytest.mark.unit
    def test_dedupes_pin_shared_by_config_and_workflow(self, tmp_path, monkeypatch):
        """
        GIVEN a repo pinned in both the pre-commit config and a workflow
        WHEN collect_pins gathers from every source
        THEN the shared (repo, ref) pair appears exactly once
        AND the first source seen (pre-commit) wins the label

        Encodes the dedup invariant: a repo used across many files is
        queried once, not once per file.
        """
        shared = (
            "repos:\n"
            "  - repo: https://github.com/actions/checkout\n"
            "    rev: v4\n"
            "    hooks:\n"
            "      - id: noop\n"
        )
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text(shared, encoding="utf-8")
        workflows = tmp_path / "workflows"
        workflows.mkdir()
        (workflows / "ci.yml").write_text(WORKFLOW_SAMPLE, encoding="utf-8")
        monkeypatch.setattr(cpv, "PRECOMMIT_CONFIG", str(config))
        monkeypatch.setattr(cpv, "WORKFLOWS_DIR", str(workflows))

        pins = cpv.collect_pins()

        checkout_v4 = [
            (repo, ref, src)
            for repo, ref, src in pins
            if repo == "actions/checkout" and ref == "v4"
        ]
        assert len(checkout_v4) == 1
        assert checkout_v4[0][2] == "pre-commit"


class _FakeResponse:
    """Minimal urlopen context manager whose read() yields a JSON body."""

    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


@pytest.mark.integration
class TestLatestGithubTagIntegration:
    """Scenario: resolve the latest tag across the gh CLI and REST boundary.

    latest_github_tag dispatches to an authenticated ``gh api`` call when
    the CLI is on PATH and falls back to the unauthenticated REST API
    otherwise. These tests drive the real dispatch and parsing logic,
    faking only the external boundary (PATH lookup, subprocess, HTTP).
    """

    def test_uses_gh_cli_when_available(self, monkeypatch):
        """
        GIVEN the gh CLI is on PATH and returns a tag
        WHEN latest_github_tag resolves the repo
        THEN the gh-reported tag is returned
        AND the REST API is never queried as a fallback
        """
        monkeypatch.setattr(cpv.shutil, "which", lambda _name: "/usr/bin/gh")
        monkeypatch.setattr(
            cpv.subprocess,
            "run",
            lambda *_a, **_k: SimpleNamespace(stdout="v5.1.0\n"),
        )

        def _no_rest(*_a, **_k):
            raise AssertionError("REST fallback must not run when gh succeeds")

        monkeypatch.setattr("urllib.request.urlopen", _no_rest)

        assert cpv.latest_github_tag("actions/checkout") == "v5.1.0"

    def test_falls_back_to_rest_when_gh_absent(self, monkeypatch):
        """
        GIVEN the gh CLI is not installed
        WHEN latest_github_tag resolves the repo
        THEN the REST API is queried instead
        AND the parsed tag_name is returned
        """
        monkeypatch.setattr(cpv.shutil, "which", lambda _name: None)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *_a, **_k: _FakeResponse({"tag_name": "v6.1.0"}),
        )

        assert cpv.latest_github_tag("pycqa/bandit") == "v6.1.0"

    def test_gh_empty_result_falls_back_to_rest(self, monkeypatch):
        """
        GIVEN gh is present but reports no release tag
        WHEN latest_github_tag resolves the repo
        THEN it falls back to the REST API
        AND returns the tag the REST API provides
        """
        monkeypatch.setattr(cpv.shutil, "which", lambda _name: "/usr/bin/gh")
        monkeypatch.setattr(
            cpv.subprocess,
            "run",
            lambda *_a, **_k: SimpleNamespace(stdout="\n"),
        )
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *_a, **_k: _FakeResponse({"tag_name": "v2.0.0"}),
        )

        assert cpv.latest_github_tag("owner/repo") == "v2.0.0"

    def test_gh_subprocess_error_falls_back_to_rest(self, monkeypatch):
        """
        GIVEN gh is present but the subprocess raises an OSError
        WHEN latest_github_tag resolves the repo
        THEN the gh failure is swallowed
        AND the REST API result is returned instead
        """
        monkeypatch.setattr(cpv.shutil, "which", lambda _name: "/usr/bin/gh")

        def _boom(*_a, **_k):
            raise OSError("gh not executable")

        monkeypatch.setattr(cpv.subprocess, "run", _boom)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *_a, **_k: _FakeResponse({"tag_name": "v3.3.3"}),
        )

        assert cpv.latest_github_tag("owner/repo") == "v3.3.3"

    def test_returns_none_when_every_source_fails(self, monkeypatch):
        """
        GIVEN gh is absent and the REST request raises
        WHEN latest_github_tag resolves the repo
        THEN it returns None so the caller skips cleanly
        AND no exception escapes the resolver
        """
        monkeypatch.setattr(cpv.shutil, "which", lambda _name: None)

        def _boom(*_a, **_k):
            raise OSError("network unreachable")

        monkeypatch.setattr("urllib.request.urlopen", _boom)

        assert cpv.latest_github_tag("owner/repo") is None

    def test_rest_null_tag_name_returns_none(self, monkeypatch):
        """
        GIVEN gh is absent and the REST payload has a null tag_name
        WHEN latest_github_tag resolves the repo
        THEN the null is normalized to None
        AND the caller receives no spurious tag
        """
        monkeypatch.setattr(cpv.shutil, "which", lambda _name: None)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *_a, **_k: _FakeResponse({"tag_name": None}),
        )

        assert cpv.latest_github_tag("owner/repo") is None
