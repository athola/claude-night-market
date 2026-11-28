"""The pre-commit maintenance hook runs on a host without md5sum.

hash_of called md5sum, which macOS lacks before 14
and BSD does not ship. With the index present, set -e ended the hook
with 127, and every commit was blocked.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
SCRIPT = PLUGIN / "scripts" / "precommit_palace_maintenance.sh"


def _link_tools_except(dest: Path, system_dirs: tuple[Path, ...], skip: str) -> None:
    """Link every tool in ``system_dirs`` into ``dest`` except ``skip``.

    The guard is ``lexists``: ``exists`` follows the link, so a dangling
    system symlink seen twice (``/bin`` is ``/usr/bin`` on merged-usr
    images) reads as absent and ``symlink_to`` raises ``FileExistsError``.
    """
    for system_dir in system_dirs:
        for tool in system_dir.iterdir():
            link = dest / tool.name
            if tool.name != skip and not os.path.lexists(link):
                link.symlink_to(tool)


def test_tool_linking_survives_a_dangling_symlink_seen_twice(tmp_path: Path) -> None:
    """Ubuntu 26.04 ships a dangling ``/usr/bin/grub-ntldr-img``."""
    system_dirs = (tmp_path / "usr-bin", tmp_path / "bin")
    for system_dir in system_dirs:
        system_dir.mkdir()
        (system_dir / "dangling").symlink_to(tmp_path / "missing-target")
    dest = tmp_path / "linked"
    dest.mkdir()
    _link_tools_except(dest, system_dirs, "md5sum")
    assert os.path.islink(dest / "dangling")


def test_the_hook_runs_without_md5sum(tmp_path: Path) -> None:
    hooks = tmp_path / "plugins" / "memory-palace" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "memory-palace-index.yaml").write_text("entries: {}\n")
    shims = tmp_path / "shims"
    shims.mkdir()
    (shims / "uv").write_text("#!/bin/sh\nexit 0\n")
    (shims / "uv").chmod(0o755)
    git = shutil.which("git", path="/usr/bin:/opt/homebrew/bin:/usr/local/bin")
    assert git is not None
    (shims / "git").symlink_to(git)
    # Linux ships md5sum in /usr/bin, so the system directories cannot be
    # on PATH as they are. Link every tool in them except md5sum instead.
    system = tmp_path / "system"
    system.mkdir()
    _link_tools_except(system, (Path("/usr/bin"), Path("/bin")), "md5sum")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["PATH"] = f"{shims}:{system}"
    assert shutil.which("md5sum", path=env["PATH"]) is None
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=env, check=True)
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_a_drained_ignored_index_does_not_block_the_commit(tmp_path: Path) -> None:
    """The index is gitignored local state (#1067).

    Re-staging it after the drain changed it ran `git add` on an ignored
    path, which exits 1, and under set -e that blocked every commit
    following a capture.
    """
    hooks = tmp_path / "plugins" / "memory-palace" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "memory-palace-index.yaml").write_text("entries: {}\n")
    (tmp_path / ".gitignore").write_text("memory-palace-index.yaml\n")
    shims = tmp_path / "shims"
    shims.mkdir()
    # The drain runs from the plugin directory and rewrites the index.
    (shims / "uv").write_text(
        "#!/bin/sh\n"
        "if [ -f hooks/memory-palace-index.yaml ]; then\n"
        "  printf 'hashes: {}\\n' >> hooks/memory-palace-index.yaml\n"
        "fi\n"
        "exit 0\n"
    )
    (shims / "uv").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["PATH"] = f"{shims}:{env['PATH']}"
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=env, check=True)

    result = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "hashes" in (hooks / "memory-palace-index.yaml").read_text()
