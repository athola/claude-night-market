"""The ``index report``, ``index promote`` and ``index retitle`` commands.

``test_index_promoter.py`` covers the corpus functions these commands
call. The commands themselves were unexercised: the reporting branch
that emits JSON for a downstream consumer, the text branch a human
reads, the promote command's dry-run default, which is the only thing
standing between a curation run and an index rewritten without a
backup, and the retitle command's claim to be idempotent.

The CLI is rooted at tmp_path the way ``test_index_prune_cli_guard.py``
roots it, so every read and write lands in the throwaway tree.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _PLUGIN_ROOT / "scripts" / "memory_palace_cli.py"


def _load_cli_module():
    """Import the CLI script by path; it is not an installed module."""
    sys.path.insert(0, str(_PLUGIN_ROOT / "src"))
    if "memory_palace_cli" in sys.modules:
        return sys.modules["memory_palace_cli"]
    spec = importlib.util.spec_from_file_location("memory_palace_cli", _CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["memory_palace_cli"] = module
    spec.loader.exec_module(module)
    return module


def _entry(key: str, **overrides: object) -> dict[str, object]:
    """Build one capture index entry with a fixed timestamp."""
    entry: dict[str, object] = {
        "content_hash": f"sha256:{key}",
        "stored_at": f"data/staging/{key}.md",
        "importance_score": 50,
        "last_updated": "2026-09-01T00:00:00+00:00",
        "title": f"Capture {key}",
        "maturity": "growing",
        "routing_type": "meta",
        "url": f"https://example.com/{key}",
    }
    entry.update(overrides)
    return entry


def _write_index(plugin_dir: Path, entries: dict[str, dict]) -> Path:
    """Write a capture index and return its path."""
    (plugin_dir / "hooks").mkdir(parents=True, exist_ok=True)
    (plugin_dir / "data" / "staging").mkdir(parents=True, exist_ok=True)
    path = plugin_dir / "hooks" / "memory-palace-index.yaml"
    payload = {
        "entries": entries,
        "hashes": {e["content_hash"]: e["stored_at"] for e in entries.values()},
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Build a CLI instance rooted at a throwaway plugin directory.

    Both overrides are cleared because ``persistent_root`` lets either
    of them outrank ``plugin_dir``. With one set, the apply paths below
    would back up and rewrite the operator's real capture index before
    failing their tmp_path assertion.
    """
    monkeypatch.delenv("MEMORY_PALACE_DATA_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    instance = _load_cli_module().MemoryPalaceCLI()
    instance.plugin_dir = tmp_path
    return instance


class TestIndexReportIsReadOnly:
    """Feature: capture index analytics

    As a curator
    I want a report over the capture index in either text or JSON
    So that I can see what is inert before deciding to change it.
    """

    def test_json_report_carries_every_documented_statistic(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN an index with one routed entry and one still at every
              capture default
        WHEN index_report runs with format json
        THEN stdout parses as JSON carrying the totals and the
             promotion candidates

        The JSON branch exists for a consumer that cannot read the text
        layout, so a missing key here is a downstream KeyError rather
        than a cosmetic problem.
        """
        _write_index(
            tmp_path,
            {
                "https://example.com/a": _entry("a"),
                "https://example.com/b": _entry(
                    "b", routing_type="pending", maturity="seedling"
                ),
            },
        )

        assert cli.index_report(output_format="json", top=5) is True

        report = json.loads(capsys.readouterr().out)
        assert report["total"] == 2
        assert report["inert_count"] == 1
        assert report["inert_ratio"] == 0.5
        assert report["by_routing_type"] == {"meta": 1, "pending": 1}
        assert isinstance(report["top_clusters"], list)
        assert isinstance(report["promotion_candidates"], list)

    def test_text_report_names_the_index_it_read(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN an index with two entries
        WHEN index_report runs in its default text format
        THEN the output names the index path and the entry counts

        The command resolves its own path from the persistent root, so
        printing that path is how an operator confirms the report
        describes the tree they meant.
        """
        index_path = _write_index(
            tmp_path,
            {
                "https://example.com/a": _entry("a"),
                "https://example.com/b": _entry("b", routing_type="pending"),
            },
        )

        assert cli.index_report() is True

        printed = capsys.readouterr().out
        assert str(index_path) in printed
        assert "Total entries:   2" in printed
        assert "Largest topic clusters" in printed

    def test_report_writes_nothing(self, cli, tmp_path: Path) -> None:
        """GIVEN an index on disk
        WHEN index_report runs
        THEN the index file is byte for byte what it was

        The docstring calls this command read-only, and the precommit
        maintenance script runs it on trees it must not modify.
        """
        index_path = _write_index(tmp_path, {"https://example.com/a": _entry("a")})
        before = index_path.read_bytes()

        cli.index_report()

        assert index_path.read_bytes() == before


class TestIndexPromoteDefaultsToADryRun:
    """Feature: promote/archive proposals over the capture index

    As a curator
    I want proposals printed and nothing written unless I ask
    So that a curation run cannot rewrite the index by accident.
    """

    def test_dry_run_prints_proposals_and_leaves_the_index_alone(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a pending entry the fetch hook marked as capturing nothing
        WHEN index_promote runs without apply
        THEN the archive proposal is printed and the file is unchanged

        A dry run that wrote would make the default destructive, and the
        printed warning is the only thing telling the operator that a
        second command is needed.
        """
        index_path = _write_index(
            tmp_path,
            {
                "https://example.com/empty": _entry(
                    "empty", routing_type="pending", null_capture="zero-result set"
                )
            },
        )
        before = index_path.read_bytes()

        assert cli.index_promote() is True

        printed = capsys.readouterr().out
        assert "[ARCHIVE] https://example.com/empty" in printed
        assert "DRY RUN" in printed
        assert index_path.read_bytes() == before

    def test_apply_writes_a_backup_before_changing_the_index(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN the same archivable entry
        WHEN index_promote runs with apply
        THEN a timestamped backup holds the pre-change index and the
             entry's routing type has moved

        The backup is the only undo this command offers, so writing the
        change without it would make a bad proposal permanent.
        """
        index_path = _write_index(
            tmp_path,
            {
                "https://example.com/empty": _entry(
                    "empty", routing_type="pending", null_capture="zero-result set"
                )
            },
        )
        before = index_path.read_bytes()

        assert cli.index_promote(apply=True) is True

        backups = list((tmp_path / "data" / "backups").glob("*.yaml"))
        assert len(backups) == 1
        assert backups[0].read_bytes() == before
        entry = yaml.safe_load(index_path.read_text(encoding="utf-8"))["entries"][
            "https://example.com/empty"
        ]
        assert entry["routing_type"] != "pending"
        assert "Backup:" in capsys.readouterr().out

    def test_apply_with_nothing_to_do_writes_no_backup(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN an index whose entries are all routed already
        WHEN index_promote runs with apply
        THEN it reports nothing to apply and creates no backup

        Backing up on every no-op run fills the backup directory with
        copies of an index that never changed, which is what makes the
        real backups hard to find.
        """
        _write_index(tmp_path, {"https://example.com/a": _entry("a")})

        assert cli.index_promote(apply=True) is True

        assert not (tmp_path / "data" / "backups").exists()
        assert "Nothing to apply." in capsys.readouterr().out

    def test_top_limits_how_many_proposals_are_printed(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN five archivable entries
        WHEN index_promote runs with top=2
        THEN two proposals are printed while the count reports all five

        The limit governs the listing only: an operator who sees two
        lines and a count of five knows the run would touch more than
        the screen shows.
        """
        _write_index(
            tmp_path,
            {
                f"https://example.com/{i}": _entry(
                    str(i), routing_type="pending", null_capture="zero-result set"
                )
                for i in range(5)
            },
        )

        cli.index_promote(top=2)

        printed = capsys.readouterr().out
        assert "0 promote, 5 archive" in printed
        assert printed.count("[ARCHIVE]") == 2


class TestIndexRetitleRepairsNonTitles:
    """Feature: repairing titles captured before the shape rules were right

    As a curator
    I want bad titles replaced with the slug the hook would have used
    So that the index reads as a list of pages rather than fragments.
    """

    def test_retitle_dry_run_shows_both_titles_and_writes_nothing(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN an entry whose title is a page fragment rather than a
              title
        WHEN index_retitle runs without apply
        THEN the old and new titles are both printed and the file is
             unchanged

        An operator approving a bulk retitle needs the before value:
        the proposal is only checkable against what it replaces.
        """
        index_path = _write_index(
            tmp_path,
            {
                "https://example.com/some-real-article": _entry(
                    "some-real-article", title="Response"
                )
            },
        )
        before = index_path.read_bytes()

        assert cli.index_retitle() is True

        printed = capsys.readouterr().out
        assert "Titles to repair: 1" in printed
        assert "from: 'Response'" in printed
        assert "DRY RUN" in printed
        assert index_path.read_bytes() == before

    def test_retitle_apply_is_idempotent(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN an entry retitled by a first apply run
        WHEN index_retitle runs with apply a second time
        THEN it reports nothing to retitle

        The docstring claims idempotence, and the maintenance script
        runs this command unattended: a repair that re-proposed itself
        would rewrite and re-back-up the index on every commit.
        """
        _write_index(
            tmp_path,
            {
                "https://example.com/some-real-article": _entry(
                    "some-real-article", title="Response"
                )
            },
        )

        assert cli.index_retitle(apply=True) is True
        capsys.readouterr()

        assert cli.index_retitle(apply=True) is True
        assert "Nothing to retitle." in capsys.readouterr().out
