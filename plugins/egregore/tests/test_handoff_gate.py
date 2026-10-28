"""Tests for the handoff gate.

The gate is the harness's one hard rule: no valid handoff, no run. Every
test below pins one way an item can be refused, because a gate that
passes something it should have caught costs a whole night.

The mutation tests matter most. Each takes a known-good item, breaks one
field, and asserts the gate goes red. If removing a check does not turn
one of these red, that check was not load-bearing.
"""

from __future__ import annotations

import dataclasses
import textwrap
from pathlib import Path

import handoff_gate as gate
import pytest
import yaml

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
        assert result.problems == ()


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


class TestForbiddenFragmentsSurviveSpacing:
    """A destructive command is not made safe by an extra space."""

    @pytest.mark.parametrize(
        "command",
        [
            "git commit -n -m x",
            "git  reset  --hard",
            "git push  -f",
        ],
    )
    def test_a_spacing_variant_is_still_refused(
        self, tmp_path: Path, command: str
    ) -> None:
        """
        Scenario: A forbidden command written with unusual spacing
        When the gate reads it
        Then it is refused

        The fragments were matched as raw substrings against the command
        text, so these three walked through while their single-spaced
        forms were refused. `git commit -n` is the short spelling of
        --no-verify and is named beside it in .claude/rules; the list
        carried only the long form.
        """
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", f"test: {command}"
        )
        item = write_item(tmp_path, **{"handoff.md": handoff})

        result = gate.check_item(item)

        assert result.state == "UNSAFE"

    def test_a_handoff_command_problem_still_names_it_as_commands_dot_name(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: A handoff command is refused
        When the problem is reported
        Then it is labelled `commands.<name>` exactly as before

        Routing task commands through the same check made the label a
        parameter. This pins that the handoff-side wording did not change
        with it, so an operator reading yesterday's message and today's
        sees the same thing.
        """
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", "test: git commit --no-verify"
        )
        item = write_item(tmp_path, **{"handoff.md": handoff})

        result = gate.check_item(item)

        assert any(p.startswith("commands.test contains") for p in result.problems)


class TestGateResultRejectsAnUnknownCode:
    """An invented code is refused where it is invented.

    ``state`` is reached from the CLI's JSON path. An unrecognized code
    used to survive construction and surface as a ``KeyError`` raised
    inside a property, naming the lookup at the point of formatting
    rather than the caller that supplied the code.
    """

    def test_an_unknown_code_is_refused_at_construction(self) -> None:
        with pytest.raises(ValueError, match="unknown gate code"):
            gate.GateResult(code=999)

    def test_every_declared_state_is_accepted(self) -> None:
        for code in (
            gate.READY,
            gate.MISSING,
            gate.MALFORMED,
            gate.UNSAFE,
            gate.INCOHERENT,
        ):
            assert gate.GateResult(code=code).state

    def test_a_verdict_cannot_be_edited_after_the_gate_ran(self) -> None:
        result = gate.GateResult(code=gate.READY)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.code = gate.UNSAFE  # type: ignore[misc]  # illegal is the assertion


class TestTraceabilityRejectsATaskThatDoesNotExist:
    """The unknown-task branch was pinned by nothing.

    Deleting it left the suite green, so a design tracing an acceptance
    criterion to a task id nobody wrote would have been certified
    READY. An untraced criterion and one traced into thin air are the
    same defect at the gate: nothing performs the criterion.
    """

    CRITERIA = [{"id": "AC1"}]

    def test_a_criterion_tracing_to_an_unknown_task_is_a_problem(self) -> None:
        problems = gate._check_traceability(
            self.CRITERIA, {"AC1": ["T9"]}, {"T1", "T2"}
        )
        assert problems
        assert "unknown tasks" in problems[0]
        assert "T9" in problems[0]

    def test_a_criterion_traced_to_no_task_is_still_a_problem(self) -> None:
        problems = gate._check_traceability(self.CRITERIA, {}, {"T1"})
        assert problems
        assert "traced to no task" in problems[0]

    def test_a_criterion_traced_to_a_real_task_passes(self) -> None:
        assert gate._check_traceability(self.CRITERIA, {"AC1": ["T1"]}, {"T1"}) == []


class TestLoadItem:
    """The runner reads the documents through the same loader the gate uses."""

    def test_an_admitted_item_yields_its_handoff_and_tasks(
        self, tmp_path: Path
    ) -> None:
        handoff, tasks = gate.load_item(write_item(tmp_path))
        assert isinstance(handoff, gate.Handoff)
        assert handoff.item == "NS-001"
        assert handoff.branch == "night/NS-001-provider-timeout"
        assert handoff.budget["max_attempts_per_task"] == 3
        assert [task["id"] for task in tasks] == ["T1", "T2"]

    def test_a_refused_item_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="absent"):
            gate.load_item(write_item(tmp_path, **{"design.md": None}))


def _handoff_doc(**changes: object) -> str:
    """GOOD_HANDOFF with keys replaced, or removed where the value is ``_DROP``."""
    data = yaml.safe_load(GOOD_HANDOFF.split("---")[1])
    for key, value in changes.items():
        if value is _DROP:
            del data[key]
        else:
            data[key] = value
    return "---\n" + yaml.safe_dump(data, sort_keys=False) + "---\n\nbody\n"


_DROP = object()


class TestTheHandoffIsTyped:
    """Feature: the runner reads a parsed Handoff, never a raw mapping.

    Read through ``.get(...) or {}``, a handoff missing its branch reached
    ``git worktree add -b None``. A missing or mistyped key now stops at
    the loader, which names it.
    """

    @pytest.mark.parametrize("key", gate.HANDOFF_REQUIRED_KEYS)
    def test_a_missing_required_key_is_named(self, tmp_path: Path, key: str) -> None:
        item = write_item(tmp_path, **{"handoff.md": _handoff_doc(**{key: _DROP})})

        with pytest.raises(ValueError, match=repr(key)):
            gate.load_item(item)

    @pytest.mark.parametrize(
        ("key", "value"),
        [("branch", 123), ("base_branch", None), ("scope", "a/"), ("budget", [])],
    )
    def test_a_mistyped_key_is_named(
        self, tmp_path: Path, key: str, value: object
    ) -> None:
        item = write_item(tmp_path, **{"handoff.md": _handoff_doc(**{key: value})})

        with pytest.raises(ValueError, match=repr(key)):
            gate.load_item(item)

    def test_the_gate_refuses_a_mistyped_key(self, tmp_path: Path) -> None:
        """Refused as MALFORMED, so ``main`` never reaches ``load_item`` with it."""
        item = write_item(tmp_path, **{"handoff.md": _handoff_doc(branch=123)})

        result = gate.check_item(item)

        assert result.code == gate.MALFORMED
        assert any("'branch'" in problem for problem in result.problems)

    def test_the_gate_requires_exactly_the_handoff_fields(self) -> None:
        required = tuple(
            f.name
            for f in dataclasses.fields(gate.Handoff)
            if f.default is dataclasses.MISSING
        )

        assert gate.REQUIRED_DOCS["handoff.md"][1] == required

    def test_the_handoff_cannot_be_reassigned(self, tmp_path: Path) -> None:
        handoff, _ = gate.load_item(write_item(tmp_path))

        with pytest.raises(dataclasses.FrozenInstanceError):
            handoff.branch = "other"  # type: ignore[misc]  # frozen dataclass: the write must raise


class TestForbiddenCommandsAreReadAsArgv:
    """A bypass is judged by what the command does, not how it is spelled.

    Substring matching on normalized text let reordered flags, split
    short options, git global options and `+refspec` pushes through,
    and night_run executes whatever the gate admits with nobody watching.
    """

    @pytest.mark.parametrize(
        "command",
        [
            # The bypasses the substring match admitted.
            "git push origin main --force",
            "git -C . reset --hard HEAD",
            "rm -fr build",
            "rm -r -f build",
            "git commit -a -n -m x",
            "git push origin +main",
            # Further spellings of the same operations.
            "git push -uf origin main",
            "git push --force-with-lease origin main",
            "git push --force-with-lease=main origin main",
            "git push --forc origin main",
            "git -c user.name=x push -f",
            "git --git-dir=.git --work-tree=. push --force",
            "git push origin +refs/heads/a:refs/heads/b",
            "git commit -an -m x",
            "git commit -anm x",
            "git commit --no-verif -m x",
            "git reset --har HEAD",
            "rm -Rf build",
            "rm --recursive --force build",
            "uv run rm -rf build",
            "env SKIP=ruff git commit -m x",
            "git -c core.hooksPath=/dev/null commit -m x",
            "git -c alias.p=push p --force",
            # The refusals that already held.
            "git commit --no-verify",
            "git push --force origin main",
            "rm -rf build",
            "SKIP=ruff git commit -m x",
            "git commit -n -m x",
            "git  reset  --hard",
            "git push  -f",
            "pre-commit run --no-verify",
        ],
    )
    def test_a_bypass_is_refused(self, tmp_path: Path, command: str) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", f"test: {command}"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE", command
        assert any("bypasses a quality gate" in p for p in result.problems)

    @pytest.mark.parametrize(
        "command",
        [
            "git push origin main",
            "git push -u origin main",
            "rm build.log",
            "rm -f build.log",
            "rm -r build",
            'git commit -m "fix -n handling"',
            "git commit -m fix-no-verify-docs",
            "git commit -mn",
            "git -C plugins/egregore status",
            "git reset --soft HEAD~1",
            "uv run pytest tests/ -q -k force",
        ],
    )
    def test_an_ordinary_command_is_admitted(
        self, tmp_path: Path, command: str
    ) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", f"test: {command}"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "READY", (command, result.problems)

    def test_unbalanced_quotes_are_refused(self, tmp_path: Path) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", "test: git push 'origin main --force"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE"
        assert any("parseable" in p for p in result.problems)

    def test_a_chained_bypass_is_refused_for_both_reasons(self, tmp_path: Path) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q",
            "test: pytest -q && git push origin +main",
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE"
        assert any("bypasses a quality gate" in p for p in result.problems)
        assert any("shell metacharacters" in p for p in result.problems)


class TestDocumentShapesAreCheckedAtLoad:
    """A key of the wrong type is MALFORMED, never an exception.

    Key presence alone admitted `acceptance: []` as READY, and a scalar
    where a list belongs raised AttributeError out of check_item, which
    night_run calls before it walks anything.
    """

    @pytest.mark.parametrize(
        ("doc", "new", "key"),
        [
            ("requirements.md", "acceptance: AC1", "acceptance"),
            ("requirements.md", "acceptance: []", "acceptance"),
            ("requirements.md", "acceptance: [AC1]", "acceptance"),
            ("tasks.md", "tasks: T1", "tasks"),
            ("tasks.md", "tasks: []", "tasks"),
            ("tasks.md", "tasks: [T1]", "tasks"),
            ("design.md", "traces: AC1", "traces"),
            ("design.md", "traces:\n  AC1: T1", "traces"),
        ],
    )
    def test_a_wrong_shape_is_malformed_and_named(
        self, tmp_path: Path, doc: str, new: str, key: str
    ) -> None:
        good = {
            "requirements.md": GOOD_REQUIREMENTS,
            "tasks.md": GOOD_TASKS,
            "design.md": GOOD_DESIGN,
        }[doc]
        body = good.split(f"\n{key}:")[0] + f"\n{new}\n---\n"
        result = gate.check_item(write_item(tmp_path, **{doc: body}))
        assert result.state == "MALFORMED", result.problems
        assert any(repr(key) in p for p in result.problems), result.problems

    def test_a_task_whose_evidence_is_not_a_mapping_is_malformed(
        self, tmp_path: Path
    ) -> None:
        tasks = GOOD_TASKS.replace(
            "    evidence:\n"
            "      command: uv run pytest tests/test_delegation_error_paths.py -q\n"
            "      expect: pass\n"
            '      match: "1 passed"\n',
            "    evidence: uv run pytest -q\n",
        )
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": tasks}))
        assert result.state == "MALFORMED", result.problems
        assert any("evidence" in p for p in result.problems)


class TestExpectFailRequiresMatch:
    """A red check must name the failure it expects.

    pytest exits 4 on a usage error (a typo in the path) and 5 when it
    collects no tests. Both are nonzero, so `expect: fail` alone counts
    a check that never ran as the guard going red. `evidence.match` is
    what ties the red to the failure the task meant.
    """

    def test_expect_fail_without_match_is_refused_naming_the_task(
        self, tmp_path: Path
    ) -> None:
        tasks = GOOD_TASKS.replace('      match: "1 failed"\n', "")
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": tasks}))
        assert result.state == "INCOHERENT", result.problems
        assert any("task T1" in p and "match" in p for p in result.problems)

    def test_expect_fail_with_match_is_admitted(self, tmp_path: Path) -> None:
        assert gate.check_item(write_item(tmp_path)).state == "READY"

    def test_expect_pass_without_match_is_still_admitted(self, tmp_path: Path) -> None:
        tasks = GOOD_TASKS.replace('      match: "1 passed"\n', "")
        assert gate.check_item(write_item(tmp_path, **{"tasks.md": tasks})).state == (
            "READY"
        )

    def test_the_shipped_template_carries_match_on_its_red_task(self) -> None:
        template = Path(__file__).parent.parent / "templates" / "handoff" / "tasks.md"
        data = gate.parse_frontmatter(template.read_text())
        red = [t for t in data["tasks"] if t["evidence"]["expect"] == "fail"]
        assert red
        assert all(t["evidence"].get("match") for t in red)


class TestWorkDestroyingGitCommandsAreRefused:
    """Each git spelling that discards work or deletes a ref is refused.

    `rm -r` without `-f` stays admitted: it is the brief's line, and
    the task files it could touch are already bounded by allow_paths.
    """

    @pytest.mark.parametrize(
        "command",
        [
            "git clean -f",
            "git clean -fd",
            "git clean -fdx",
            "git clean -xf",
            "git clean --force -d",
            "git checkout -- src/app.py",
            "git checkout .",
            "git checkout -f main",
            "git checkout --force main",
            "git checkout main -- .",
            "git restore src/app.py",
            "git restore --worktree src/app.py",
            "git restore --staged --worktree src/app.py",
            "git restore -SW src/app.py",
            "git push --mirror origin",
            "git push --delete origin feature",
            "git push -d origin feature",
            "git push --prune origin",
            "git push origin :feature",
            "git stash drop",
            "git stash clear",
            "git branch -D feature",
            "git branch --delete --force feature",
            "git branch -d -f feature",
            "git branch -df feature",
            "git checkout -B main",
            "git branch -M old main",
            "git branch -C old main",
            "git branch -m -f old main",
            "git branch --move --force old main",
            "git --config-env=alias.p=PUSHF p",
            "git --config-env core.hooksPath=HOOKS commit -m x",
        ],
    )
    def test_a_work_destroying_command_is_refused(
        self, tmp_path: Path, command: str
    ) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", f"test: {command}"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE", command
        assert any("bypasses a quality gate" in p for p in result.problems)

    @pytest.mark.parametrize(
        "command",
        [
            "git checkout -b feature",
            "git checkout main",
            "git restore --staged src/app.py",
            "git restore -S src/app.py",
            "git push origin main",
            "git push origin main:main",
            "git clean -n",
            "git clean -nd",
            "git branch -d merged",
            "git branch -m old new",
            "git stash",
            "git stash list",
            "git --config-env=user.name=GIT_NAME status",
            "rm -r build",
            # After "--" every word is a path, so a file named like a flag
            # does not turn an ordinary command into a bypass.
            "git commit -m x -- -n",
            "git restore --staged -- --worktree",
            "rm -r -- -f",
            # Global options and no subcommand: nothing to judge.
            "git -C .",
        ],
    )
    def test_an_ordinary_git_command_is_admitted(
        self, tmp_path: Path, command: str
    ) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", f"test: {command}"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "READY", (command, result.problems)


class TestFrontmatterAndCommandEdgesAreRefused:
    """Each way a document or command can be structurally empty is named."""

    def test_an_unterminated_frontmatter_block_is_malformed(
        self, tmp_path: Path
    ) -> None:
        body = "---\nschema: nightshift/handoff@1\nitem: NS-001\n"
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": body}))
        assert result.code == gate.MALFORMED
        assert any("unterminated" in p for p in result.problems)

    def test_frontmatter_that_is_a_list_is_malformed(self, tmp_path: Path) -> None:
        body = "---\n- schema\n- item\n---\n"
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": body}))
        assert result.code == gate.MALFORMED
        assert any("not a mapping" in p for p in result.problems)

    def test_an_empty_command_is_refused(self, tmp_path: Path) -> None:
        handoff = GOOD_HANDOFF.replace("test: uv run pytest tests/ -q", 'test: ""')
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE"
        assert "commands.test is empty" in result.problems

    def test_from_frontmatter_names_a_missing_required_key(self) -> None:
        """The type refuses on its own, not only behind check_item."""
        data = gate.parse_frontmatter(GOOD_HANDOFF)
        del data["branch"]
        with pytest.raises(ValueError, match="'branch' is absent"):
            gate.Handoff.from_frontmatter(data)

    def test_the_cli_prints_state_and_problems_without_json(
        self, tmp_path: Path, capsys
    ) -> None:
        item = write_item(tmp_path)
        (item / "design.md").unlink()
        code = gate.main(["--item-dir", str(item)])
        out = capsys.readouterr().out
        assert code == gate.MISSING
        assert out.startswith(f"MISSING ({gate.MISSING})")
        assert "  - " in out
        assert "design.md" in out


class TestInlineCodeIsRefused:
    """A shell or interpreter given code as a string hides it from the gate.

    The bypass checks read argv words. ``sh -c "git push --force"`` is one
    word to them, so the force push went through unread.
    """

    @pytest.mark.parametrize(
        "command",
        [
            'sh -c "git push --force origin main"',
            'bash -c "git commit --no-verify -m x"',
            'env -S "git commit -n"',
            "python3 -c print(1)",
            "node -e 1",
        ],
    )
    def test_inline_code_is_refused(self, tmp_path: Path, command: str) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", f"test: '{command}'"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE"
        assert any("runs code given as a string" in p for p in result.problems)

    def test_a_script_path_is_still_admitted(self, tmp_path: Path) -> None:
        handoff = GOOD_HANDOFF.replace(
            "test: uv run pytest tests/ -q", "test: bash scripts/check.sh"
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "READY", result.problems


class TestIdsAndPathsAreTyped:
    """Shapes the later checks hash or iterate are refused, not raised on."""

    def test_a_list_task_id_is_malformed_not_a_crash(self, tmp_path: Path) -> None:
        tasks = GOOD_TASKS.replace("  - id: T1\n", "  - id: [1]\n", 1)
        result = gate.check_item(write_item(tmp_path, **{"tasks.md": tasks}))
        assert result.state == "MALFORMED"
        assert any("id must be a string" in p for p in result.problems)

    def test_a_list_trace_entry_is_malformed_not_a_crash(self, tmp_path: Path) -> None:
        design = GOOD_DESIGN.replace("AC1: [T1, T2]", "AC1: [[1], T2]")
        result = gate.check_item(write_item(tmp_path, **{"design.md": design}))
        assert result.state == "MALFORMED"

    def test_a_string_allow_paths_is_refused(self, tmp_path: Path) -> None:
        handoff = GOOD_HANDOFF.replace(
            "  allow_paths:\n"
            "    - plugins/conjure/scripts/delegation_executor.py\n"
            "    - plugins/conjure/tests/test_delegation_error_paths.py\n",
            "  allow_paths: plugins/conjure\n",
        )
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE"
        assert any("allow_paths must be a list" in p for p in result.problems)


class TestEveryBudgetNumberIsChecked:
    """The driver reads these through int(); the gate must read them first."""

    @pytest.mark.parametrize(
        ("line", "bad"),
        [
            ("max_attempts_per_task: 3", "max_attempts_per_task: three"),
            ("implementer_timeout_s: 900", "implementer_timeout_s: '900'"),
            ("claude_token_ceiling: 120000", "claude_token_ceiling: 0"),
            ("max_tasks: 6", "max_tasks: -1"),
        ],
    )
    def test_an_unreadable_or_non_positive_budget_is_refused(
        self, tmp_path: Path, line: str, bad: str
    ) -> None:
        handoff = GOOD_HANDOFF.replace(line, bad)
        result = gate.check_item(write_item(tmp_path, **{"handoff.md": handoff}))
        assert result.state == "UNSAFE"
        assert any(bad.split(":", maxsplit=1)[0] in p for p in result.problems)
