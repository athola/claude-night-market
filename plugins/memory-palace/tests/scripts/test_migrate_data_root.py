"""Recovering a stranded palace is an operator's decision, not a hook's.

Issue #661 left real trees behind: on the filing machine 200 staged
captures under 1.9.16, and on the machine this was implemented on 1,470
under 1.9.17 and 2,491 under 1.9.18. All of them ``pending_review``, so
each one is an item in somebody's curation queue.

That is why this tool exists instead of a startup migration. Merging one
review queue into another changes what a person is going to be asked to
read. It reports by default, copies only when told to, and never deletes
the tree it read from -- if the merge is wrong, the original is still
there.

Feature: stranded version-scoped data can be found, reported, and merged
into the persistent root without losing anything.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts"))

from migrate_data_root import Plan, apply_plan, plan_migration


def _install(root: Path, version: str, files: dict[str, str]) -> Path:
    """Create a versioned install tree holding the given data files."""
    data = (
        root
        / "plugins"
        / "cache"
        / "claude-night-market"
        / "memory-palace"
        / version
        / "data"
    )
    for rel, body in files.items():
        path = data / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return data


def _dest(root: Path) -> Path:
    """The persistent root. Relative paths under it keep their ``data/``
    prefix, which is the shape ``stored_at`` already records.
    """
    return root / "plugins" / "data" / "memory-palace-claude-night-market"


class TestDiscovery:
    """Finding what is stranded, across every version present."""

    def test_finds_captures_in_every_version_tree(self, tmp_path: Path) -> None:
        """GIVEN two installed versions that each accumulated captures
        WHEN a migration is planned
        THEN files from both are listed.

        A tool that only read the newest tree would leave the older
        strandings exactly as stranded as the bug did.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})
        _install(tmp_path, "1.9.18", {"staging/b.md": "beta"})

        plan = plan_migration(tmp_path / "plugins", "memory-palace")

        assert {c.relative for c in plan.copies} == {
            Path("data/staging/a.md"),
            Path("data/staging/b.md"),
        }

    def test_reports_nothing_when_no_install_trees_exist(self, tmp_path: Path) -> None:
        """GIVEN a plugins directory with no cache tree
        WHEN a migration is planned
        THEN the plan is empty rather than an error.
        """
        (tmp_path / "plugins").mkdir()

        plan = plan_migration(tmp_path / "plugins", "memory-palace")

        assert plan.copies == []
        assert plan.conflicts == []


class TestDryRunIsTheDefault:
    """Nothing moves until an operator says so."""

    def test_planning_does_not_write(self, tmp_path: Path) -> None:
        """GIVEN a stranded capture
        WHEN a migration is planned but not applied
        THEN the destination is untouched.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})

        plan_migration(tmp_path / "plugins", "memory-palace")

        assert not _dest(tmp_path).exists()


class TestApply:
    """The copy itself."""

    def test_copies_into_the_persistent_root(self, tmp_path: Path) -> None:
        """GIVEN a planned migration
        WHEN it is applied
        THEN each file lands under the persistent root at the same
        relative path, so ``stored_at`` in the index still resolves.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})

        applied = apply_plan(plan_migration(tmp_path / "plugins", "memory-palace"))

        assert applied == 1
        assert (_dest(tmp_path) / "data" / "staging" / "a.md").read_text() == "alpha"

    def test_source_survives_the_copy(self, tmp_path: Path) -> None:
        """GIVEN an applied migration
        WHEN the source tree is inspected
        THEN the original file is still there.

        Copy and not move: if the merge turns out wrong, the operator
        needs the tree they started from.
        """
        source = _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})

        apply_plan(plan_migration(tmp_path / "plugins", "memory-palace"))

        assert (source / "staging" / "a.md").read_text() == "alpha"


class TestCollisions:
    """Two versions can hold the same relative path."""

    def test_identical_content_is_not_a_conflict(self, tmp_path: Path) -> None:
        """GIVEN the same capture present in two version trees
        WHEN a migration is planned
        THEN it is copied once and reported as no conflict.

        Captures are content-addressed by the pipeline, so the same path
        holding the same bytes in two trees is the normal case after an
        update, not a problem to escalate.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "same"})
        _install(tmp_path, "1.9.18", {"staging/a.md": "same"})

        plan = plan_migration(tmp_path / "plugins", "memory-palace")

        assert len(plan.copies) == 1
        assert plan.conflicts == []

    def test_differing_content_is_reported_and_not_overwritten(
        self, tmp_path: Path
    ) -> None:
        """GIVEN the same path holding different bytes in two trees
        WHEN the migration is planned and applied
        THEN one copy lands, the other is reported as a conflict, and
        neither silently replaces the other.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "older text"})
        _install(tmp_path, "1.9.18", {"staging/a.md": "newer text"})

        plan = plan_migration(tmp_path / "plugins", "memory-palace")
        apply_plan(plan)

        assert len(plan.conflicts) == 1
        assert plan.conflicts[0].relative == Path("data/staging/a.md")
        assert (
            _dest(tmp_path) / "data" / "staging" / "a.md"
        ).read_text() == "newer text"

    def test_newest_version_wins_a_conflict(self, tmp_path: Path) -> None:
        """GIVEN differing copies where the newer tree is not last
        alphabetically within the same minor
        WHEN the plan is built
        THEN the copy chosen comes from the highest version, compared
        numerically: 1.9.9 must not outrank 1.9.17.
        """
        _install(tmp_path, "1.9.9", {"staging/a.md": "old"})
        _install(tmp_path, "1.9.17", {"staging/a.md": "new"})

        plan = plan_migration(tmp_path / "plugins", "memory-palace")
        apply_plan(plan)

        assert (_dest(tmp_path) / "data" / "staging" / "a.md").read_text() == "new"

    def test_existing_destination_file_is_never_replaced(self, tmp_path: Path) -> None:
        """GIVEN the destination already holds a different file at that path
        WHEN the migration is applied
        THEN the destination copy stands and the source is reported.

        The persistent root is the live palace. A migration that
        overwrote it would be the same data loss in the other direction.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "from cache"})
        dest_file = _dest(tmp_path) / "data" / "staging" / "a.md"
        dest_file.parent.mkdir(parents=True)
        dest_file.write_text("already live", encoding="utf-8")

        plan = plan_migration(tmp_path / "plugins", "memory-palace")
        apply_plan(plan)

        assert dest_file.read_text() == "already live"
        assert len(plan.conflicts) == 1


class TestCaptureIndexTravels:
    """The capture index moves; it is not rebuilt, because nothing rebuilds it."""

    @staticmethod
    def _with_index(root: Path, version: str, body: str) -> Path:
        hooks = (
            root
            / "plugins"
            / "cache"
            / "claude-night-market"
            / "memory-palace"
            / version
            / "hooks"
        )
        hooks.mkdir(parents=True, exist_ok=True)
        index = hooks / "memory-palace-index.yaml"
        index.write_text(body, encoding="utf-8")
        return index

    def test_the_newest_capture_index_is_copied(self, tmp_path: Path) -> None:
        """GIVEN install trees that each carry a capture index
        WHEN the migration is applied
        THEN the newest one lands beside ``data/`` under the persistent
        root, at the path ``deduplication._get_index_path`` resolves.

        It holds per-entry metadata the captures do not: importance
        scores, routing status, null_capture reasons. Excluding it would
        leave every migrated capture unindexed with no way back.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})
        _install(tmp_path, "1.9.18", {"staging/b.md": "beta"})
        self._with_index(tmp_path, "1.9.17", "entries: {old: 1}\n")
        self._with_index(tmp_path, "1.9.18", "entries: {new: 1}\n")

        apply_plan(plan_migration(tmp_path / "plugins", "memory-palace"))

        landed = _dest(tmp_path) / "hooks" / "memory-palace-index.yaml"
        assert landed.read_text() == "entries: {new: 1}\n"

    def test_an_older_differing_index_is_reported_not_merged(
        self, tmp_path: Path
    ) -> None:
        """GIVEN two capture indexes that disagree
        WHEN the migration is planned
        THEN the older is a conflict.

        Two indexes disagreeing about an entry cannot be reconciled by
        choosing bytes, so the tool refuses to guess and names the file
        instead.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})
        _install(tmp_path, "1.9.18", {"staging/b.md": "beta"})
        self._with_index(tmp_path, "1.9.17", "entries: {old: 1}\n")
        self._with_index(tmp_path, "1.9.18", "entries: {new: 1}\n")

        plan = plan_migration(tmp_path / "plugins", "memory-palace")

        assert [c.relative for c in plan.conflicts] == [
            Path("hooks/memory-palace-index.yaml")
        ]

    def test_the_report_names_the_derived_index_not_the_capture_index(
        self, tmp_path: Path
    ) -> None:
        """GIVEN any non-empty plan
        WHEN it is rendered
        THEN the rebuild line points at the keyword index.

        ``build_indexes.py`` writes ``data/indexes/keyword-index.yaml``,
        the derived corpus index. Telling an operator it rebuilds the
        capture index would send them looking for recovery that the
        script does not perform.
        """
        _install(tmp_path, "1.9.18", {"staging/a.md": "alpha"})

        report = plan_migration(tmp_path / "plugins", "memory-palace").render()

        assert "keyword index" in report
        assert "build_indexes.py" in report


class TestRerunAfterApply:
    """Verifying a recovery must not look like a wall of problems."""

    def test_a_second_run_reports_no_conflicts(self, tmp_path: Path) -> None:
        """GIVEN a migration that was applied
        WHEN it is planned again
        THEN the files it just copied are not reported as conflicts.

        Re-running the dry run is how an operator checks the recovery
        worked. If every recovered file came back as a conflict, the
        check would say the opposite of what happened, and the one
        output that matters -- the handful of files that genuinely need
        a person -- would be buried under thousands that do not.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})
        _install(tmp_path, "1.9.18", {"staging/b.md": "beta"})
        apply_plan(plan_migration(tmp_path / "plugins", "memory-palace"))

        second = plan_migration(tmp_path / "plugins", "memory-palace")

        assert second.conflicts == []
        assert second.copies == []

    def test_a_second_run_still_reports_a_genuine_clash(self, tmp_path: Path) -> None:
        """GIVEN an applied migration and a destination file that was
        then edited
        WHEN the migration is planned again
        THEN the differing file is reported.

        Quieting the duplicate case must not quiet the real one: bytes
        that disagree are exactly what the operator has to adjudicate.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})
        apply_plan(plan_migration(tmp_path / "plugins", "memory-palace"))
        (_dest(tmp_path) / "data" / "staging" / "a.md").write_text(
            "curated since", encoding="utf-8"
        )

        second = plan_migration(tmp_path / "plugins", "memory-palace")

        assert [c.relative for c in second.conflicts] == [Path("data/staging/a.md")]

    def test_already_migrated_files_are_counted_for_the_operator(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a fully applied migration
        WHEN the plan is rendered
        THEN it says the work is already done rather than going silent,
        so a re-run reads as confirmation instead of ambiguity.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})
        apply_plan(plan_migration(tmp_path / "plugins", "memory-palace"))

        report = plan_migration(tmp_path / "plugins", "memory-palace").render()

        assert "already" in report.lower()


class TestPlanIsInspectable:
    """An operator has to be able to read the plan before running it."""

    def test_plan_reports_totals_and_sources(self, tmp_path: Path) -> None:
        """GIVEN a plan over two trees
        WHEN it is rendered
        THEN the text names the destination and the file count, because
        a plan an operator cannot check is one they have to trust.
        """
        _install(tmp_path, "1.9.17", {"staging/a.md": "alpha"})
        _install(tmp_path, "1.9.18", {"staging/b.md": "beta"})

        report = plan_migration(tmp_path / "plugins", "memory-palace").render()

        assert "2" in report
        assert "memory-palace-claude-night-market" in report


class TestPlanType:
    """The plan is data, so it can be examined without side effects."""

    def test_plan_is_constructible_empty(self) -> None:
        """GIVEN no arguments beyond a destination
        WHEN a Plan is built
        THEN it reports nothing to do.
        """
        plan = Plan(destination=Path("/nowhere"), copies=[], conflicts=[])

        assert plan.rebuild_index is False
        assert "nothing" in plan.render().lower()
