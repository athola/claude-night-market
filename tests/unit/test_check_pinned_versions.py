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

import sys
from pathlib import Path

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
        """Given config with two GitHub repos, Then returns both pins."""
        pins = cpv.precommit_pins(PRECOMMIT_SAMPLE)
        assert ("pre-commit/pre-commit-hooks", "v6.0.0") in pins
        assert ("pycqa/bandit", "1.8.3") in pins

    @pytest.mark.unit
    def test_ignores_local_repo(self):
        """Given a ``repo: local`` block, Then it is not returned."""
        pins = cpv.precommit_pins(PRECOMMIT_SAMPLE)
        assert all(not repo.startswith("local") for repo, _ in pins)
        assert len(pins) == 2


class TestWorkflowActionPins:
    """Scenario: parse ``uses: owner/repo@ref`` pins from workflow text."""

    @pytest.mark.unit
    def test_extracts_owner_repo_and_ref(self):
        """Given a workflow step, Then returns (owner/repo, ref)."""
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        assert ("actions/checkout", "v4") in pins
        assert ("astral-sh/setup-uv", "v4") in pins

    @pytest.mark.unit
    def test_strips_subpath_to_repo_root(self):
        """Given owner/repo/subpath@ref, Then repo is owner/repo only."""
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        assert ("github/codeql-action", "v4") in pins
        assert all("/upload-sarif" not in repo for repo, _ in pins)

    @pytest.mark.unit
    def test_skips_local_and_docker_actions(self):
        """Given ./local and docker:// uses, Then they are excluded."""
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        repos = [repo for repo, _ in pins]
        assert not any(r.startswith(".") for r in repos)
        assert not any("docker" in r for r in repos)

    @pytest.mark.unit
    def test_dedupes_repeated_pins(self):
        """Given checkout@v4 listed twice, Then it appears once."""
        pins = cpv.workflow_action_pins(WORKFLOW_SAMPLE)
        assert pins.count(("actions/checkout", "v4")) == 1


class TestIsBehind:
    """Scenario: compare at the granularity of the pinned ref."""

    @pytest.mark.unit
    def test_major_pin_behind_on_new_major(self):
        """Given @v4 and latest v5.0.0, Then behind (major-only compare)."""
        assert cpv.is_behind("v4", "v5.0.0") is True

    @pytest.mark.unit
    def test_major_pin_current_on_same_major(self):
        """Given @v4 and latest v4.2.2, Then NOT behind (patch ignored)."""
        assert cpv.is_behind("v4", "v4.2.2") is False

    @pytest.mark.unit
    def test_full_pin_behind_on_minor_bump(self):
        """Given v6.0.0 and latest v6.1.0, Then behind (full compare)."""
        assert cpv.is_behind("v6.0.0", "v6.1.0") is True

    @pytest.mark.unit
    def test_full_pin_current_when_equal(self):
        """Given 1.8.3 and latest 1.8.3, Then NOT behind."""
        assert cpv.is_behind("1.8.3", "1.8.3") is False

    @pytest.mark.unit
    def test_avoids_string_ordering_trap(self):
        """Given @v9 and latest v10, Then behind (numeric, not lexical)."""
        assert cpv.is_behind("v9", "v10") is True


class TestMain:
    """Scenario: blocking by default; skip cleanly when unresolvable."""

    @pytest.mark.unit
    def test_behind_blocking_exits_one_with_notice(self, monkeypatch, capsys):
        """Given a behind pin and blocking mode, Then exit 1 and name it."""
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
    def test_behind_advisory_exits_zero(self, monkeypatch, capsys):
        """Given a behind pin but advisory mode, Then exit 0 with notice."""
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
        """Given every pin current, Then exit 0 and report current."""
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
        """Given the latest tag cannot be fetched, Then skip (exit 0)."""
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
        """Given one current, one unresolved, one behind, Then exit 1."""
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
        """Given no pins discovered, Then exit 0 cleanly."""
        monkeypatch.setattr(cpv, "collect_pins", lambda: [])
        assert cpv.main() == 0
