"""The prune CLI must survive a tree that lacks the capture corpus.

``scripts/precommit_palace_maintenance.sh`` runs

    memory_palace_cli.py index prune-orphans --apply --top 0

on every commit under ``set -euo pipefail``. Two failure modes both end
badly from a git worktree, where only 15 of the ~1538 files under
``data/staging`` are tracked and the rest were never checked out:

- pruning on that reading deletes the whole index, which is what
  6092ff2d did while its message described a sanctum fix;
- raising an unhandled error aborts the commit, blocking the isolated
  contributor workflow the worktree exists to provide.

The CLI must therefore refuse the prune, say why, leave the index byte
for byte unchanged, and exit successfully.
"""

from __future__ import annotations

import importlib.util
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
    # Register before exec: the module defines dataclasses, whose type
    # resolution looks the defining module up in sys.modules.
    sys.modules["memory_palace_cli"] = module
    spec.loader.exec_module(module)
    return module


def _write_index(plugin_dir: Path, count: int) -> Path:
    """Write a capture index whose backing files are all absent."""
    (plugin_dir / "hooks").mkdir(parents=True, exist_ok=True)
    (plugin_dir / "data" / "staging").mkdir(parents=True, exist_ok=True)
    index = {
        "entries": {
            f"https://example.com/{i}": {
                "content_hash": f"sha256:{i:04d}",
                "stored_at": f"data/staging/never-checked-out-{i}.md",
                "importance_score": 50,
                "last_updated": "2026-07-01T00:00:00+00:00",
                "title": f"Capture {i}",
                "maturity": "growing",
                "routing_type": "meta",
                "url": f"https://example.com/{i}",
            }
            for i in range(count)
        },
        "hashes": {
            f"sha256:{i:04d}": f"data/staging/never-{i}.md" for i in range(count)
        },
    }
    path = plugin_dir / "hooks" / "memory-palace-index.yaml"
    path.write_text(yaml.safe_dump(index, sort_keys=False), encoding="utf-8")
    return path


class TestPruneRefusesWithoutTheCorpus:
    """A corpus-less tree neither empties the index nor breaks the commit."""

    @pytest.fixture
    def cli(self, tmp_path: Path):
        """Build a CLI instance rooted at a throwaway plugin directory."""
        module = _load_cli_module()
        instance = module.MemoryPalaceCLI()
        instance.plugin_dir = tmp_path
        return instance

    def test_leaves_the_index_untouched(self, cli, tmp_path: Path) -> None:
        """Scenario: prune --apply runs where no capture file exists
        Given an index of 20 captures with every backing file absent
        When orphan pruning is applied
        Then the index file is byte for byte what it was
        And the corpus survives a commit made from a worktree
        """
        path = _write_index(tmp_path, 20)
        before = path.read_bytes()
        cli.index_prune_orphans(apply=True, top=0)
        assert path.read_bytes() == before

    def test_reports_success_rather_than_crashing(self, cli, tmp_path: Path) -> None:
        """Scenario: The pre-commit hook runs under set -e
        Given a tree missing the capture corpus
        When orphan pruning is applied
        Then the call reports success
        And an unhandled error cannot abort an unrelated commit
        """
        _write_index(tmp_path, 20)
        assert cli.index_prune_orphans(apply=True, top=0) is True

    def test_explains_the_refusal(
        self, cli, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: A human needs to know the prune was skipped
        Given a tree missing the capture corpus
        When orphan pruning is applied
        Then the output names the refusal and the counts behind it
        And a silent skip cannot be mistaken for a clean run
        """
        _write_index(tmp_path, 20)
        cli.index_prune_orphans(apply=True, top=0)
        output = capsys.readouterr().out + capsys.readouterr().err
        assert "20 of 20" in output

    def test_dry_run_is_also_refused(self, cli, tmp_path: Path) -> None:
        """Scenario: The same tree is inspected without --apply
        Given a tree missing the capture corpus
        When orphan pruning is proposed but not applied
        Then the call still reports success rather than raising
        And the read-only path matches the write path
        """
        path = _write_index(tmp_path, 20)
        before = path.read_bytes()
        assert cli.index_prune_orphans(apply=False, top=0) is True
        assert path.read_bytes() == before

    def test_a_real_orphan_is_still_pruned(self, cli, tmp_path: Path) -> None:
        """Scenario: Ordinary curation runs in a complete checkout
        Given an index of 20 captures with 19 backing files present
        When orphan pruning is applied
        Then the lone orphan is removed
        And the guard has not disabled the feature it protects
        """
        path = _write_index(tmp_path, 20)
        staging = tmp_path / "data" / "staging"
        for i in range(1, 20):
            (staging / f"never-checked-out-{i}.md").write_text("stub", encoding="utf-8")

        cli.index_prune_orphans(apply=True, top=0)

        entries = yaml.safe_load(path.read_text(encoding="utf-8"))["entries"]
        assert "https://example.com/0" not in entries
        assert len(entries) == 19
