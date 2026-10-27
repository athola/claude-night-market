"""check-json-utils-drift.sh is a CI gate; prove it can fail.

lint.yml runs it on every push, and before this file no test executed
it: a gate whose failing branch has never run cannot be told apart
from one that always passes.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "scripts" / "shared" / "check-json-utils-drift.sh"
VENDORED = (
    "plugins/imbue/hooks/shared/json_utils.sh",
    "plugins/conserve/hooks/shared/json_utils.sh",
    "plugins/memory-palace/hooks/shared/json_utils.sh",
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git checkout holding the gate, its logger, and in-sync copies."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shared = tmp_path / "scripts" / "shared"
    shared.mkdir(parents=True)
    shutil.copy2(GATE, shared / GATE.name)
    shutil.copy2(REPO_ROOT / "scripts" / "logging.sh", tmp_path / "scripts")
    (shared / "json_utils.sh").write_text("escape_for_json() { :; }\n")
    for rel in VENDORED:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared / "json_utils.sh", tmp_path / rel)
    return tmp_path


def _gate(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/shared/check-json-utils-drift.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_in_sync_copies_pass(repo: Path) -> None:
    """GIVEN three copies identical to the canonical file
    WHEN the gate runs
    THEN it exits 0
    """
    run = _gate(repo)
    assert run.returncode == 0, run.stdout + run.stderr


def test_one_byte_of_drift_fails_and_names_the_copy(repo: Path) -> None:
    """GIVEN one copy that differs from the canonical file by one byte
    WHEN the gate runs
    THEN it exits nonzero
    AND it names the drifted copy
    """
    drifted = repo / VENDORED[1]
    drifted.write_text(drifted.read_text() + "#")

    run = _gate(repo)

    assert run.returncode != 0
    assert VENDORED[1] in run.stdout + run.stderr


def test_a_missing_copy_fails(repo: Path) -> None:
    """GIVEN one vendored copy deleted
    WHEN the gate runs
    THEN it exits nonzero and names the missing path
    """
    (repo / VENDORED[0]).unlink()

    run = _gate(repo)

    assert run.returncode != 0
    assert VENDORED[0] in run.stdout + run.stderr


def test_a_missing_canonical_file_fails(repo: Path) -> None:
    """GIVEN no canonical json_utils.sh
    WHEN the gate runs
    THEN it exits nonzero rather than finding nothing to compare
    """
    (repo / "scripts" / "shared" / "json_utils.sh").unlink()

    run = _gate(repo)

    assert run.returncode != 0
