"""The clawhub publish scripts report what happened, on any checkout path.

Shell review S0-15, S1-2, S1-3, S1-4, S1-10 and S1-11.
- clawhub-batch-publish exited 0 when every publish in a batch failed.
- Its "0 ok" check also matched "10 ok".
- A progress file from a previous release was reused, so a new release
  published nothing.
- clawhub-submit pasted the repo path into Python source, which broke
  on an apostrophe.
- It used `grep -P`, which macOS grep lacks.
- clawhub-cron never reclaimed a lock left by a killed run, so it skipped
  every hour forever.

Every run happens in a sandbox copy with npx, clawhub and crontab shimmed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ("clawhub-batch-publish.sh", "clawhub-submit.sh", "clawhub-cron.sh")


def _sandbox(tmp_path: Path, name: str = "repo") -> Path:
    repo = tmp_path / name
    (repo / "scripts").mkdir(parents=True)
    for script in SCRIPTS:
        shutil.copy2(ROOT / "scripts" / script, repo / "scripts" / script)
    plugin_json = repo / "plugins" / "abstract" / ".claude-plugin" / "plugin.json"
    plugin_json.parent.mkdir(parents=True)
    plugin_json.write_text(json.dumps({"version": "1.10.0"}))
    return repo


def _skills(repo: Path, count: int) -> None:
    export = repo / "clawhub"
    export.mkdir(exist_ok=True)
    slugs = [f"skill-{i}" for i in range(count)]
    for slug in slugs:
        (export / slug).mkdir()
    (export / "manifest.json").write_text(
        json.dumps({"total_exported": count, "skills": [{"slug": s} for s in slugs]})
    )


def _shims(tmp_path: Path, **scripts: str) -> Path:
    shim_dir = tmp_path / "shims"
    shim_dir.mkdir(exist_ok=True)
    for name, body in scripts.items():
        shim = shim_dir / name
        shim.write_text(f"#!/bin/sh\n{body}\n")
        shim.chmod(0o755)
    return shim_dir


def _run(repo: Path, script: str, shim_dir: Path, *args: str, **env: str):
    return subprocess.run(
        ["/bin/bash", str(repo / "scripts" / script), *args],
        cwd=repo,
        env={
            **os.environ,
            "PATH": f"{shim_dir}:{os.environ['PATH']}",
            "HOME": str(repo.parent),
            **env,
        },
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_a_batch_where_every_publish_fails_exits_nonzero(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    _skills(repo, 2)
    shims = _shims(tmp_path, npx="echo auth error >&2; exit 1")
    result = _run(repo, "clawhub-batch-publish.sh", shims)
    assert "0 ok, 2 fail" in result.stdout
    assert result.returncode != 0


def test_ten_published_is_not_read_as_zero(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    _skills(repo, 10)
    shims = _shims(tmp_path, npx="exit 0")
    result = _run(repo, "clawhub-batch-publish.sh", shims, "--batch-size", "10")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "10 ok, 0 fail" in result.stdout
    assert "No skills published" not in result.stdout


def test_a_progress_file_from_another_release_is_restarted(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    _skills(repo, 2)
    progress = repo / ".egregore" / "clawhub-progress.json"
    progress.parent.mkdir()
    progress.write_text(
        json.dumps(
            {
                "version": "1.9.0",
                "total": 2,
                "published": ["skill-0", "skill-1"],
                "failed": [],
                "pending": [],
                "batches_completed": 1,
            }
        )
    )
    shims = _shims(tmp_path, npx="exit 0")
    result = _run(repo, "clawhub-batch-publish.sh", shims)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 ok, 0 fail" in result.stdout
    assert json.loads(progress.read_text())["version"] == "1.10.0"


def test_submit_handles_an_apostrophe_path_and_bsd_grep(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path, "o'brien repo")
    _skills(repo, 0)
    shims = _shims(tmp_path, clawhub='[ "$1" = whoami ] && echo "✔ alice"')
    result = _run(repo, "clawhub-submit.sh", shims)
    assert "Auto-detected version: v1.10.0" in result.stdout, result.stderr
    assert "Authenticated as: alice\n" in result.stdout
    assert "Skills to publish: 0" in result.stdout


def test_cron_reclaims_a_lock_left_by_a_killed_run(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    (repo / "scripts" / "clawhub-submit.sh").write_text("exit 1\n")
    lock = repo / ".clawhub-sync.lock"
    lock.mkdir()
    three_hours_ago = time.time() - 3 * 3600
    os.utime(lock, (three_hours_ago, three_hours_ago))
    log = tmp_path / "sync.log"
    shims = _shims(tmp_path, crontab="exit 0")
    result = _run(repo, "clawhub-cron.sh", shims, CLAWHUB_SYNC_LOG=str(log))
    assert result.returncode == 0, result.stderr
    text = log.read_text()
    assert "skipping" not in text
    assert "Will retry next hour" in text
    assert not lock.exists()


def test_cron_still_skips_while_a_recent_run_holds_the_lock(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path)
    (repo / ".clawhub-sync.lock").mkdir()
    log = tmp_path / "sync.log"
    shims = _shims(tmp_path, crontab="exit 0")
    _run(repo, "clawhub-cron.sh", shims, CLAWHUB_SYNC_LOG=str(log))
    assert "skipping" in log.read_text()
