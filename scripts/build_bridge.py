#!/usr/bin/env python3
"""Build the OpenClaw bridge plugin from ClawHub export.

Copies exported skills into bridge/openclaw/skills/ and updates
the plugin manifest with the full skill list.

Usage:
    python scripts/build_bridge.py [--clawhub clawhub/] [--bridge bridge/openclaw/]
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLAWHUB = ROOT / "clawhub"
DEFAULT_BRIDGE = ROOT / "bridge" / "openclaw"


def build_bridge(clawhub_dir: Path, bridge_dir: Path) -> None:
    """Populate bridge plugin skills from ClawHub export."""
    manifest_path = clawhub_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"No manifest.json in {clawhub_dir}. Run 'make clawhub-export' first."
        )

    manifest = json.loads(manifest_path.read_text())
    skills_dir = bridge_dir / "skills"

    # Clean and recreate
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
    skills_dir.mkdir(parents=True)

    copied = 0
    for skill_info in manifest.get("skills", []):
        slug = skill_info["slug"]
        src = clawhub_dir / slug
        if src.is_dir():
            shutil.copytree(src, skills_dir / slug)
            copied += 1

    print(f"Copied {copied} skills to {skills_dir}/")

    # Update plugin manifest version
    plugin_json = bridge_dir / "openclaw.plugin.json"
    if plugin_json.exists():
        pj = json.loads(plugin_json.read_text())
        pj["version"] = manifest.get(
            "version",
            manifest["skills"][0].get("version", "1.0.0")
            if manifest.get("skills")
            else "1.0.0",
        )
        plugin_json.write_text(json.dumps(pj, indent=2) + "\n")
        print(f"Updated {plugin_json} version to {pj['version']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OpenClaw bridge plugin")
    parser.add_argument(
        "--clawhub",
        type=Path,
        default=DEFAULT_CLAWHUB,
        help="ClawHub export directory",
    )
    parser.add_argument(
        "--bridge",
        type=Path,
        default=DEFAULT_BRIDGE,
        help="Bridge plugin directory",
    )
    args = parser.parse_args()
    build_bridge(args.clawhub, args.bridge)


if __name__ == "__main__":
    main()
