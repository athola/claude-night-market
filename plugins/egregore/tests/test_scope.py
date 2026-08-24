"""Tests for the scope allowlist and the un-overridable denylist.

The denylist is the one part of the harness a handoff author cannot
relax. Every test here that asserts a denial is asserting that
property, not just a path match.
"""

from __future__ import annotations

import dataclasses
import io

import pytest
import scope


class TestDenylist:
    """The builtin denylist refuses paths no handoff may authorize."""

    @pytest.mark.parametrize(
        "path",
        [
            ".github/workflows/ci.yml",
            "uv.lock",
            "plugins/conjure/uv.lock",
            "package-lock.json",
            "CONSTITUTION.md",
            ".claude/settings.json",
            ".claude/settings.local.json",
            "plugins/egregore/hooks/stop_hook.py",
            "plugins/nightshift/hooks/anything.py",
        ],
    )
    def test_denied_paths(self, path: str) -> None:
        assert scope.is_denied(path), f"{path} must be denied"

    @pytest.mark.parametrize(
        "path",
        [
            "plugins/conjure/scripts/delegation_executor.py",
            "plugins/conjure/tests/test_delegation.py",
            "README.md",
            "docs/nightshift/NS-001/tasks.md",
        ],
    )
    def test_allowed_paths(self, path: str) -> None:
        assert not scope.is_denied(path), f"{path} must not be denied"

    def test_allowlist_cannot_override_denylist(self) -> None:
        """A handoff naming a denied path is rejected, not obeyed."""
        result = scope.check(
            allow_paths=[".github/workflows/ci.yml"],
            changed=[".github/workflows/ci.yml"],
        )
        assert not result.ok
        assert ".github/workflows/ci.yml" in result.violating
        assert result.reason == "denylist"


class TestAllowlist:
    """Changed files must fall inside the handoff's allow_paths."""

    def test_all_inside_allowlist_passes(self) -> None:
        result = scope.check(
            allow_paths=["plugins/conjure/scripts/delegation_executor.py"],
            changed=["plugins/conjure/scripts/delegation_executor.py"],
        )
        assert result.ok
        assert result.violating == ()

    def test_file_outside_allowlist_violates(self) -> None:
        result = scope.check(
            allow_paths=["plugins/conjure/scripts/delegation_executor.py"],
            changed=[
                "plugins/conjure/scripts/delegation_executor.py",
                "plugins/conjure/scripts/quota_tracker.py",
            ],
        )
        assert not result.ok
        assert result.violating == ("plugins/conjure/scripts/quota_tracker.py",)
        assert result.reason == "outside_allowlist"

    def test_directory_prefix_allows_children(self) -> None:
        result = scope.check(
            allow_paths=["plugins/conjure/tests/"],
            changed=["plugins/conjure/tests/test_new.py"],
        )
        assert result.ok

    def test_prefix_does_not_leak_to_sibling_directory(self) -> None:
        """`plugins/conjure` must not authorize `plugins/conjure-extra`."""
        result = scope.check(
            allow_paths=["plugins/conjure"],
            changed=["plugins/conjure-extra/evil.py"],
        )
        assert not result.ok

    def test_empty_allowlist_denies_everything(self) -> None:
        result = scope.check(allow_paths=[], changed=["README.md"])
        assert not result.ok

    def test_no_changes_is_not_a_scope_violation(self) -> None:
        """An empty diff is a task failure, handled elsewhere, not a breach."""
        result = scope.check(allow_paths=["README.md"], changed=[])
        assert result.ok


class TestCli:
    """The CLI is what the driver and the watchdog actually call."""

    def test_clean_paths_exit_zero(self, capsys, monkeypatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("plugins/a/b.py\n"))
        code = scope.main(["--allow", "plugins/a"])
        assert code == 0
        assert '"ok": true' in capsys.readouterr().out

    def test_violation_exits_nonzero_and_names_the_file(
        self, capsys, monkeypatch
    ) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("plugins/a/b.py\nother/c.py\n"))
        code = scope.main(["--allow", "plugins/a"])
        assert code == 1
        assert "other/c.py" in capsys.readouterr().out

    def test_denied_path_exits_nonzero(self, capsys, monkeypatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO(".github/workflows/x.yml\n"))
        code = scope.main(["--allow", ".github"])
        assert code == 1
        assert "denylist" in capsys.readouterr().out


class TestScopeResultCannotContradictItself:
    """The two halves of a result must agree, and neither can be edited.

    A pass carrying violations and a failure carrying no reason both
    read as the opposite of what happened, and the night run consults
    this type before deciding whether to revert a working tree.
    """

    def test_a_passing_result_cannot_name_violations(self) -> None:
        with pytest.raises(ValueError, match="cannot name violations"):
            scope.ScopeResult(ok=True, violating=("a/b.py",))

    def test_a_passing_result_cannot_carry_a_reason(self) -> None:
        with pytest.raises(ValueError, match="cannot name violations"):
            scope.ScopeResult(ok=True, reason="denylist")

    def test_a_failing_result_must_say_why(self) -> None:
        with pytest.raises(ValueError, match="must carry a reason"):
            scope.ScopeResult(ok=False, violating=("a/b.py",))

    def test_a_result_cannot_be_edited_after_the_check(self) -> None:
        result = scope.ScopeResult(ok=True)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.ok = False  # type: ignore[misc]  # illegal is the assertion


class TestAnAllowlistEntryCannotReachOutsideItsScope:
    """A `..` segment in an allowlist entry is not a narrower scope.

    `within` compares segments without resolving one, so
    `plugins/conjure/..` authorized every sibling of conjure while
    reading as narrower than `plugins`. Such an entry is dropped rather
    than honored: an allowlist that cannot be trusted should narrow the
    scope, not widen it.
    """

    def test_a_parent_segment_does_not_authorize_a_sibling(self) -> None:
        result = scope.check(
            allow_paths=["plugins/conjure/.."],
            changed=["plugins/conjure/../pensive/x.py"],
        )
        assert not result.ok
        assert result.reason == "outside_allowlist"

    def test_an_absolute_entry_is_not_an_allowlist_entry(self) -> None:
        result = scope.check(allow_paths=["/"], changed=["plugins/conjure/x.py"])
        assert not result.ok

    def test_an_ordinary_entry_still_authorizes_its_own_tree(self) -> None:
        result = scope.check(
            allow_paths=["plugins/conjure"], changed=["plugins/conjure/x.py"]
        )
        assert result.ok
