"""Tests for change-driven staleness signals.

Feature: A claim goes stale when its source changes, not when time passes
  Elapsed time is a proxy. The signal that matters is whether the world
  the unit describes has changed since the unit was written.

The signal is a content fingerprint rather than a timestamp. Timestamps
lie in both directions: filesystem mtime resets on clone, checkout, and
rebase, and git commit time misses uncommitted work entirely. A digest
of the bytes answers the question directly and needs no subprocess.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory_palace.corpus.staleness_signals import (
    MAX_TRACKED_PATHS,
    Signal,
    capture_digests,
    check_dependencies,
    digest_path,
)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A small file tree standing in for a working copy."""
    (tmp_path / "a.py").write_text("original\n")
    (tmp_path / "b.py").write_text("also original\n")
    return tmp_path


class TestDigest:
    """Feature: fingerprints identify content, not location or time."""

    def test_same_content_same_digest(self, tree: Path) -> None:
        """Scenario: a re-read of unchanged bytes matches."""
        assert digest_path("a.py", root=tree) == digest_path("a.py", root=tree)

    def test_different_content_different_digest(self, tree: Path) -> None:
        """Scenario: distinct files do not collide."""
        assert digest_path("a.py", root=tree) != digest_path("b.py", root=tree)

    def test_touching_without_editing_does_not_change_digest(self, tree: Path) -> None:
        """Scenario: an mtime bump alone is not a change.

        This is the false positive that makes mtime unusable: clone,
        checkout, and rebase all rewrite timestamps without touching
        content.
        """
        before = digest_path("a.py", root=tree)
        (tree / "a.py").touch()
        assert digest_path("a.py", root=tree) == before

    def test_missing_file_has_no_digest(self, tree: Path) -> None:
        """Scenario: an absent path yields None, not an empty-string hash."""
        assert digest_path("nope.py", root=tree) is None

    def test_directory_has_no_digest(self, tree: Path) -> None:
        """Scenario: a directory is not a fingerprintable dependency."""
        (tree / "sub").mkdir()
        assert digest_path("sub", root=tree) is None

    def test_path_escaping_the_root_is_refused(self, tree: Path) -> None:
        """Scenario: a declared path cannot read outside the tree.

        Unit text is model-authored, so the path list is untrusted input.
        """
        assert digest_path("../../etc/passwd", root=tree) is None


class TestCapture:
    """Feature: fingerprints are recorded at capture time, by machine."""

    def test_captures_one_digest_per_readable_path(self, tree: Path) -> None:
        """Scenario: declared paths become a path-to-digest map."""
        captured = capture_digests(["a.py", "b.py"], root=tree)
        assert set(captured) == {"a.py", "b.py"}

    def test_unreadable_paths_are_omitted_not_faked(self, tree: Path) -> None:
        """Scenario: a path with no digest is simply absent."""
        assert "nope.py" not in capture_digests(["a.py", "nope.py"], root=tree)

    def test_capture_is_capped(self, tree: Path) -> None:
        """Scenario: a runaway unit cannot blow the hook's budget.

        The paths are created so the cap is what bounds the result
        rather than the files simply being absent.
        """
        names = [f"f{i}.py" for i in range(500)]
        for name in names:
            (tree / name).write_text(name)
        captured = capture_digests(names, root=tree)
        assert 0 < len(captured) <= MAX_TRACKED_PATHS


class TestThreeOutcomes:
    """Feature: unknown is distinct from unchanged.

    Reporting 'unchanged' for a dependency we could not inspect is the
    failure that makes a staleness check worse than none at all.
    """

    def test_untouched_dependency_is_unchanged(self, tree: Path) -> None:
        """Scenario: identical bytes since capture."""
        digests = capture_digests(["a.py"], root=tree)
        assert check_dependencies(digests, root=tree)["a.py"] is Signal.UNCHANGED

    def test_edited_dependency_is_changed(self, tree: Path) -> None:
        """Scenario: the claim's ground moved."""
        digests = capture_digests(["a.py"], root=tree)
        (tree / "a.py").write_text("edited\n")
        assert check_dependencies(digests, root=tree)["a.py"] is Signal.CHANGED

    def test_deleted_dependency_is_changed(self, tree: Path) -> None:
        """Scenario: deletion is a change, not an absence of evidence."""
        digests = capture_digests(["a.py"], root=tree)
        (tree / "a.py").unlink()
        assert check_dependencies(digests, root=tree)["a.py"] is Signal.CHANGED

    def test_dependency_without_a_stored_digest_is_unknown(self, tree: Path) -> None:
        """Scenario: units captured before fingerprinting existed."""
        assert check_dependencies({"a.py": ""}, root=tree)["a.py"] is Signal.UNKNOWN

    def test_no_declared_dependencies_yields_no_signals(self, tree: Path) -> None:
        """Scenario: a unit declaring nothing cannot be flagged."""
        assert check_dependencies({}, root=tree) == {}
