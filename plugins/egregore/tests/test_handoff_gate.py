"""Tests for the handoff gate.

The gate is the harness's one hard rule: no valid handoff, no run. Every
test below pins one way an item can be refused, because a gate that
passes something it should have caught costs a whole night.

The mutation tests matter most. Each takes a known-good item, breaks one
field, and asserts the gate goes red. If removing a check does not turn
one of these red, that check was not load-bearing.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import handoff_gate as gate
import pytest

GOOD_REQUIREMENTS = """\
---
schema: nightshift/requirements@1
item: NS-001
acceptance:
  - id: AC1
    statement: The failure reason names the provider that timed out.
---

## Why
Timeouts are currently reported without naming a provider.
"""

GOOD_DESIGN = """\
---
schema: nightshift/design@1
item: NS-001
risk: low
traces:
  AC1: [T1, T2]
---

## Approach
Return a distinct reason string from the failure classifier.
"""

GOOD_TASKS = """\
---
schema: nightshift/tasks@1
item: NS-001
tasks:
  - id: T1
    kind: red
    title: Failing test for timeout attribution
    files: [plugins/conjure/tests/test_delegation_error_paths.py]
    change: Add a test asserting the reason is 'timeout'.
    evidence:
      command: uv run pytest tests/test_delegation_error_paths.py -q
      expect: fail
      match: "1 failed"
    depends_on: []
  - id: T2
    kind: green
    title: Attribute timeouts in the failure classifier
    files: [plugins/conjure/scripts/delegation_executor.py]
    change: Return 'timeout' when the launch timed out.
    evidence:
      command: uv run pytest tests/test_delegation_error_paths.py -q
      expect: pass
      match: "1 passed"
    depends_on: [T1]
---
"""

GOOD_HANDOFF = """\
---
schema: nightshift/handoff@1
item: NS-001
title: Name the provider that timed out
base_branch: main
branch: night/NS-001-provider-timeout
scope:
  allow_paths:
    - plugins/conjure/scripts/delegation_executor.py
    - plugins/conjure/tests/test_delegation_error_paths.py
  max_diff_lines: 200
  spec_ref: null
commands:
  setup: uv sync
  test: uv run pytest tests/ -q
  lint: uv run ruff check scripts/
  full_test: uv run pytest tests/ -q
budget:
  max_tasks: 6
  max_attempts_per_task: 3
  implementer_timeout_s: 900
  claude_token_ceiling: 120000
implementer:
  provider: auto
  allow_on_plan_fallback: false
babysitter:
  model: sonnet
---

## Definition of done
The failure reason names the provider that timed out.
"""


def write_item(root: Path, **overrides: str) -> Path:
    """Write a known-good item, replacing any named document."""
    item = root / "items" / "NS-001"
    item.mkdir(parents=True, exist_ok=True)
    docs = {
        "requirements.md": GOOD_REQUIREMENTS,
        "design.md": GOOD_DESIGN,
        "tasks.md": GOOD_TASKS,
        "handoff.md": GOOD_HANDOFF,
    }
    docs.update(overrides)
    for name, body in docs.items():
        if body is None:
            continue
        (item / name).write_text(body)
    return item


class TestReady:
    """A well-formed item passes every check."""

    def test_known_good_item_passes(self, tmp_path: Path) -> None:
        result = gate.check_item(write_item(tmp_path))
        assert result.code == gate.READY, result.problems
        assert result.state == "READY"
        assert result.problems == []


class TestMissing:
    """Each of the four documents is required."""

    @pytest.mark.parametrize(
        "absent", ["requirements.md", "design.md", "tasks.md", "handoff.md"]
    )
    def test_each_required_document_is_required(
        self, tmp_path: Path, absent: str
    ) -> None:
        item = write_item(tmp_path)
        (item / absent).unlink()
        result = gate.check_item(item)
        assert result.code == gate.MISSING
        assert any(absent in p for p in result.problems)

    def test_absent_directory_is_missing_not_a_crash(self, tmp_path: Path) -> None:
        result = gate.check_item(tmp_path / "items" / "NS-404")
        assert result.code == gate.MISSING


class TestMalformed:
    """Structural problems are reported before semantic ones."""

    def test_unparseable_frontmatter(self, tmp_path: Path) -> None:
        item = write_item(tmp_path, **{"handoff.md": "---\n:\n  - [unclosed\n---\n"})
        assert gate.check_item(item).code == gate.MALFORMED

    def test_absent_frontmatter(self, tmp_path: Path) -> None:
        item = write_item(tmp_path, **{"handoff.md": "# Just prose\n"})
        assert gate.check_item(item).code == gate.MALFORMED

    def test_unknown_schema_version(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace(
            "schema: nightshift/handoff@1", "schema: nightshift/handoff@7"
        )
        assert gate.check_item(write_item(tmp_path, **{"handoff.md": body})).code == (
            gate.MALFORMED
        )

    def test_required_key_absent(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace("branch: night/NS-001-provider-timeout\n", "")
        assert gate.check_item(write_item(tmp_path, **{"handoff.md": body})).code == (
            gate.MALFORMED
        )

    def test_item_id_mismatch_across_documents(self, tmp_path: Path) -> None:
        body = GOOD_TASKS.replace("item: NS-001", "item: NS-999")
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": body}))
        assert result.code == gate.MALFORMED
        assert any("NS-999" in p for p in result.problems)


class TestUnsafe:
    """Some things no handoff may ask for, whatever its author wrote."""

    def test_empty_allowlist(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace(
            "  allow_paths:\n"
            "    - plugins/conjure/scripts/delegation_executor.py\n"
            "    - plugins/conjure/tests/test_delegation_error_paths.py\n",
            "  allow_paths: []\n",
        )
        assert gate.check_item(write_item(tmp_path, **{"handoff.md": body})).code == (
            gate.UNSAFE
        )

    def test_allowlist_naming_a_denied_path(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace(
            "    - plugins/conjure/scripts/delegation_executor.py",
            "    - .github/workflows/ci.yml",
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": body}))
        assert result.code == gate.UNSAFE
        assert any(".github" in p for p in result.problems)

    def test_repo_root_allowlist(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace(
            "    - plugins/conjure/scripts/delegation_executor.py", "    - ."
        )
        assert gate.check_item(write_item(tmp_path, **{"handoff.md": body})).code == (
            gate.UNSAFE
        )

    def test_diff_cap_above_limit_without_spec_ref(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace("max_diff_lines: 200", "max_diff_lines: 900")
        assert gate.check_item(write_item(tmp_path, **{"handoff.md": body})).code == (
            gate.UNSAFE
        )

    def test_diff_cap_above_limit_with_spec_ref_is_allowed(
        self, tmp_path: Path
    ) -> None:
        body = GOOD_HANDOFF.replace("max_diff_lines: 200", "max_diff_lines: 900")
        body = body.replace("spec_ref: null", "spec_ref: docs/specs/NS-001.md")
        assert gate.check_item(write_item(tmp_path, **{"handoff.md": body})).code == (
            gate.READY
        )

    @pytest.mark.parametrize(
        "bad",
        [
            "git commit --no-verify",
            "git push --force origin main",
            "rm -rf build",
            "SKIP=ruff git commit -m x",
        ],
    )
    def test_quality_gate_bypasses_are_refused(self, tmp_path: Path, bad: str) -> None:
        body = GOOD_HANDOFF.replace(
            "  lint: uv run ruff check scripts/", f"  lint: {bad}"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": body}))
        assert result.code == gate.UNSAFE


class TestIncoherent:
    """The four documents must agree with each other."""

    def test_task_touching_a_file_outside_the_allowlist(self, tmp_path: Path) -> None:
        body = GOOD_TASKS.replace(
            "files: [plugins/conjure/scripts/delegation_executor.py]",
            "files: [plugins/conjure/scripts/quota_tracker.py]",
        )
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": body}))
        assert result.code == gate.INCOHERENT
        assert any("quota_tracker" in p for p in result.problems)

    def test_acceptance_criterion_with_no_tracing_task(self, tmp_path: Path) -> None:
        body = GOOD_REQUIREMENTS.replace(
            "  - id: AC1\n    statement: The failure reason names the provider"
            " that timed out.\n",
            "  - id: AC1\n    statement: One.\n  - id: AC2\n    statement: Two.\n",
        )
        result = gate.check_item(write_item(tmp_path, **{"requirements.md": body}))
        assert result.code == gate.INCOHERENT
        assert any("AC2" in p for p in result.problems)

    def test_task_with_no_evidence_command(self, tmp_path: Path) -> None:
        body = GOOD_TASKS.replace(
            "      command: uv run pytest tests/test_delegation_error_paths.py -q\n"
            "      expect: pass\n",
            "      expect: pass\n",
        )
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": body}))
        assert result.code == gate.INCOHERENT

    def test_no_red_task_means_no_failing_test_first(self, tmp_path: Path) -> None:
        """The Iron Law, made machine-checkable."""
        body = GOOD_TASKS.replace("expect: fail", "expect: pass").replace(
            "kind: red", "kind: green"
        )
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": body}))
        assert result.code == gate.INCOHERENT
        assert any("expect: fail" in p or "failing" in p for p in result.problems)

    def test_dependency_cycle(self, tmp_path: Path) -> None:
        body = GOOD_TASKS.replace("depends_on: []", "depends_on: [T2]")
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": body}))
        assert result.code == gate.INCOHERENT
        assert any("cycle" in p.lower() for p in result.problems)

    def test_dependency_on_an_unknown_task(self, tmp_path: Path) -> None:
        body = GOOD_TASKS.replace("depends_on: [T1]", "depends_on: [T9]")
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": body}))
        assert result.code == gate.INCOHERENT

    def test_more_tasks_than_the_budget_allows(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace("max_tasks: 6", "max_tasks: 1")
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": body}))
        assert result.code == gate.INCOHERENT


class TestPrecedence:
    """Worse news outranks lesser news."""

    def test_missing_outranks_malformed(self, tmp_path: Path) -> None:
        """A missing file is reported as MISSING even if another is broken."""
        item = write_item(tmp_path, **{"handoff.md": "# no frontmatter\n"})
        (item / "design.md").unlink()
        assert gate.check_item(item).code == gate.MISSING

    def test_unsafe_outranks_incoherent(self, tmp_path: Path) -> None:
        """Safety is judged before coherence, so the worst news comes first."""
        body = GOOD_HANDOFF.replace("max_diff_lines: 200", "max_diff_lines: 900")
        tasks = GOOD_TASKS.replace("depends_on: [T1]", "depends_on: [T9]")
        item = write_item(tmp_path, **{"handoff.md": body, "tasks.md": tasks})
        assert gate.check_item(item).code == gate.UNSAFE


class TestCli:
    """The CLI is what the driver and the watchdog actually call."""

    def test_exit_code_is_the_gate_code(self, tmp_path: Path, capsys) -> None:
        item = write_item(tmp_path)
        code = gate.main(["--item-dir", str(item), "--json"])
        assert code == gate.READY
        assert '"state": "READY"' in capsys.readouterr().out

    def test_cli_reports_problems_on_failure(self, tmp_path: Path, capsys) -> None:
        item = write_item(tmp_path)
        (item / "tasks.md").unlink()
        code = gate.main(["--item-dir", str(item), "--json"])
        assert code == gate.MISSING
        assert "tasks.md" in capsys.readouterr().out


def test_module_docstring_names_the_hard_rule() -> None:
    """The refusal rule must stay stated where a reader will find it."""
    assert "no run" in textwrap.dedent(gate.__doc__ or "").lower()


class TestShellMetacharacters:
    """Commands are executed as argv, never through a shell.

    The gate refuses metacharacters so that the driver never has to
    decide whether a given string is safe to hand to ``sh``. An
    allowlist of shapes beats a denylist of fragments.
    """

    @pytest.mark.parametrize(
        "bad",
        [
            "cd plugins/conjure && uv run pytest -q",
            "pytest -q; curl http://example.com",
            "pytest -q | tee /tmp/out",
            "pytest -q > /tmp/out",
            "echo $(whoami)",
            "echo `whoami`",
        ],
    )
    def test_shell_metacharacters_are_refused(self, tmp_path: Path, bad: str) -> None:
        body = GOOD_HANDOFF.replace("  test: uv run pytest tests/ -q", f"  test: {bad}")
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": body}))
        assert result.code == gate.UNSAFE
        assert any("shell" in p.lower() for p in result.problems)

    def test_a_plain_command_is_accepted(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace(
            "  test: uv run pytest tests/ -q",
            "  test: uv run --directory plugins/conjure pytest tests/ -q",
        )
        assert gate.check_item(write_item(tmp_path, **{"handoff.md": body})).code == (
            gate.READY
        )

    def test_unparseable_command_is_refused(self, tmp_path: Path) -> None:
        body = GOOD_HANDOFF.replace(
            "  test: uv run pytest tests/ -q", '  test: pytest "unclosed'
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": body}))
        assert result.code == gate.UNSAFE


class TestEveryExecutedStringPassesTheCommandGate:
    """A command the driver runs must have been judged before it runs."""

    def test_a_task_evidence_command_is_refused_like_a_handoff_command(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: A task's evidence.command names a forbidden command
        Given the identical string is refused in handoff.commands
        When the gate reads the item
        Then it is refused there too

        _check_command was reached from one call site, over
        handoff["commands"]. A task's evidence.command was checked for
        non-emptiness and nothing else, then executed by the driver as
        plain argv -- which is all `rm -rf`, `git reset --hard` and
        `git push --force` need. The gate refused a string on one path
        and ran it on the other.
        """
        tasks = GOOD_TASKS.replace(
            "command: uv run pytest tests/test_delegation_error_paths.py -q\n"
            "      expect: fail",
            "command: git commit --no-verify\n      expect: fail",
        )
        item = write_item(tmp_path, **{"tasks.md": tasks})

        result = gate.check_item(item)

        assert result.state == "UNSAFE"
        assert any("--no-verify" in p for p in result.problems)

    def test_the_control_string_is_still_refused_in_handoff_commands(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: The same string in handoff.commands
        When the gate reads the item
        Then it is refused

        The control the finding used. Kept so the test above is evidence
        that both paths agree rather than that one path fires.
        """
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", "test: git commit --no-verify"
        )
        item = write_item(tmp_path, **{"handoff.md": handoff})

        result = gate.check_item(item)

        assert result.state == "UNSAFE"


class TestNumericBudgetsAreParsedNotSniffed:
    """A cap that is not a number is a malformed cap, not an absent one."""

    def test_a_quoted_max_diff_lines_does_not_bypass_the_cap(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: max_diff_lines is written as a quoted string
        Given no scope.spec_ref to justify going over the cap
        When the gate reads the item
        Then it is refused

        The guard was `isinstance(cap, int) and cap > DEFAULT_DIFF_CAP`,
        so a non-int skipped the check rather than failing it, while the
        driver read the same field through `int(...)` and accepted the
        string. Two quote characters therefore lifted the surgical-edit
        ceiling on an unattended run with no spec reference.
        """
        handoff = GOOD_HANDOFF.replace("max_diff_lines: 200", 'max_diff_lines: "900"')
        item = write_item(tmp_path, **{"handoff.md": handoff})

        result = gate.check_item(item)

        assert result.state == "UNSAFE"

    def test_a_boolean_max_diff_lines_is_refused(self, tmp_path: Path) -> None:
        """
        Scenario: max_diff_lines is written as YAML true
        When the gate reads the item
        Then it is refused

        bool is a subclass of int, so an isinstance check admits it and
        the downstream cap becomes 1. Excluded explicitly rather than
        left to the reader.
        """
        handoff = GOOD_HANDOFF.replace("max_diff_lines: 200", "max_diff_lines: true")
        item = write_item(tmp_path, **{"handoff.md": handoff})

        result = gate.check_item(item)

        assert result.state == "UNSAFE"

    def test_a_quoted_max_tasks_is_refused(self, tmp_path: Path) -> None:
        """
        Scenario: budget.max_tasks is written as a quoted string
        When the gate reads the item
        Then it is refused

        Same shape as max_diff_lines, same bypass: the isinstance guard
        skipped the budget check on anything that was not an int.
        """
        handoff = GOOD_HANDOFF.replace("max_tasks: 6", 'max_tasks: "6"')
        item = write_item(tmp_path, **{"handoff.md": handoff})

        result = gate.check_item(item)

        assert result.state in {"UNSAFE", "INCOHERENT"}


class TestExpectIsBinary:
    """``expect`` has two legal values and no third meaning."""

    def test_a_mistyped_expect_is_refused_by_the_gate(self, tmp_path: Path) -> None:
        """
        Scenario: A task declares `expect: Pass`
        When the gate reads the item
        Then it is refused

        objective_check compared against the exact strings "fail" and
        "pass", so any other value fell through both branches and
        returned ok=True whatever the exit code. A task written
        `expect: Pass` whose command exits 1 produced a proof row reading
        "exit 1, expect Pass, verdict PASS". Nothing validated the field.
        """
        tasks = GOOD_TASKS.replace("expect: pass", "expect: Pass")
        item = write_item(tmp_path, **{"tasks.md": tasks})

        result = gate.check_item(item)

        assert result.state in {"UNSAFE", "INCOHERENT"}
        assert any("expect" in p for p in result.problems)

    def test_yaml_parsing_expect_no_as_a_boolean_is_refused(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: A task declares `expect: no`
        When the gate reads the item
        Then it is refused

        YAML reads an unquoted `no` as the boolean False, which is
        neither legal value and would have fallen through the same way.
        """
        tasks = GOOD_TASKS.replace("expect: pass", "expect: no")
        item = write_item(tmp_path, **{"tasks.md": tasks})

        result = gate.check_item(item)

        assert result.state in {"UNSAFE", "INCOHERENT"}
