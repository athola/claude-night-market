"""FR-5: build the directory one live run executes in.

The eval runner refuses plugin paths outside its target directory and
resolves symlinks before checking (probe L5). It also refuses hard
links: the 2026-11-03 smoke run on Claude Code 2.1.317 failed with "a
file in the plugin has more than one name (a hard link)". Plugins are
therefore copied. Dot-directories other than ``.claude-plugin`` are
skipped, because a stray ``.uv-cache`` made one plugin 94 MB of the
140 MB copy. Mutants still replace host files rather than edit them
(see mutate._replace).
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path

from .generate import write_cases
from .inventory import Item, item_hashes, library_hash
from .labels import Case, case_set_hash

EXCLUDED_DIRS = {"tests", "__pycache__", "data"}
KEPT_DOT_DIRS = {".claude-plugin"}
EXCLUDED_SUFFIXES = (".lock",)


def _kept(dirname: str) -> bool:
    if dirname.startswith("."):
        return dirname in KEPT_DOT_DIRS
    return dirname not in EXCLUDED_DIRS


def copy_tree(source: Path, dest: Path) -> int:
    """Copy every kept file and return the bytes copied."""
    copied = 0
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames[:] = sorted(d for d in dirnames if _kept(d))
        target_dir = dest / Path(dirpath).relative_to(source)
        target_dir.mkdir(parents=True, exist_ok=True)
        for filename in filenames:
            if filename.endswith(EXCLUDED_SUFFIXES):
                continue
            src = Path(dirpath) / filename
            if src.is_symlink():
                continue
            shutil.copy2(src, target_dir / filename)
            copied += src.stat().st_size
    return copied


def build_host(
    root: Path,
    cases: list[Case],
    items: list[Item],
    run_meta: dict,
    *,
    runs_dir: Path | None = None,
) -> Path:
    run_id = run_meta["run_id"]
    host = (runs_dir or root / "evals/activation/.runs") / run_id
    if host.exists():
        raise FileExistsError(f"run host {host} already exists")
    plugins = sorted(p.name for p in (root / "plugins").iterdir() if p.is_dir())
    copied = sum(copy_tree(root / "plugins" / p, host / "plugins" / p) for p in plugins)
    write_cases(cases, host / "evals", plugins=plugins, runs=int(run_meta["runs"]))
    (host / "cases.json").write_text(json.dumps([c.to_dict() for c in cases], indent=1))
    (host / "inventory.json").write_text(
        json.dumps(
            {
                "items": [asdict(i) for i in items],
                "library_hash": library_hash(items),
                "item_hashes": item_hashes(items),
            },
            indent=1,
        )
    )
    run = {
        "plugins": plugins,
        "case_set_hash": case_set_hash(cases),
        "copied_bytes": copied,
        **run_meta,
    }
    (host / "run.json").write_text(json.dumps(run, indent=1, sort_keys=True))
    return host
