#!/usr/bin/env python3
"""Reinstall all Claude Code plugins from their respective marketplaces.

This script reads the installed plugins configuration, uninstalls each plugin,
then reinstalls it. Useful for clearing cache corruption or version mismatches.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Plugins excluded from reinstall to prevent breaking the process
EXCLUDED_PLUGINS = {"hookify"}


def read_installed_plugins() -> dict[str, list[dict[str, Any]]]:
    """Read the installed plugins configuration file."""
    # Try v2 format first, fall back to v1
    plugins_file = Path.home() / ".claude" / "plugins" / "installed_plugins_v2.json"
    if not plugins_file.exists():
        plugins_file = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

    if not plugins_file.exists():
        print("[ERROR] Plugins configuration file not found")
        sys.exit(1)

    try:
        with plugins_file.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print("[ERROR] Plugins configuration file is not valid JSON")
        print(f"        {type(e).__name__}: {e}")
        sys.exit(1)
    except OSError as e:
        print("[ERROR] Could not read plugins configuration file")
        print(f"        {type(e).__name__}: {e}")
        sys.exit(1)

    plugins: dict[str, list[dict[str, Any]]] = data.get("plugins", {})
    return plugins


def categorize_plugins(
    plugins: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Categorize plugins into reinstallable and excluded."""
    reinstallable = []
    excluded = []

    for plugin_full_name, plugin_list in plugins.items():
        plugin_name = plugin_full_name.split("@")[0]
        marketplace = (
            plugin_full_name.split("@")[1] if "@" in plugin_full_name else "unknown"
        )

        for plugin_info in plugin_list:
            entry = {
                "full_name": plugin_full_name,
                "name": plugin_name,
                "marketplace": marketplace,
                "scope": plugin_info.get("scope", "user"),
                "version": plugin_info.get("version", "unknown"),
                "is_local": plugin_info.get("isLocal", False),
            }

            if plugin_name.lower() in EXCLUDED_PLUGINS:
                excluded.append(entry)
            else:
                reinstallable.append(entry)

    return reinstallable, excluded


def print_plugin_table(plugins: list[dict[str, Any]], title: str) -> None:
    """Print a formatted table of plugins."""
    if not plugins:
        return

    print(f"\n{title}")
    print("-" * 60)
    print(f"{'Plugin':<25} {'Marketplace':<25} {'Local':<6}")
    print("-" * 60)
    for p in plugins:
        local = "yes" if p["is_local"] else "no"
        print(f"{p['name']:<25} {p['marketplace']:<25} {local:<6}")


def generate_commands(
    reinstallable: list[dict[str, Any]], excluded: list[dict[str, Any]]
) -> None:
    """Generate copy-paste commands for manual execution."""
    print(f"\nFound {len(reinstallable) + len(excluded)} plugins")
    print(f"  - {len(reinstallable)} to reinstall")
    print(f"  - {len(excluded)} excluded (will not be touched)")

    if excluded:
        print("\n**Excluded plugins** (required for operation):")
        for p in excluded:
            print(f"  - {p['full_name']}")

    print_plugin_table(reinstallable, "Plugins to reinstall:")

    print("\n" + "=" * 60)
    print("UNINSTALL PHASE - Run these commands in order:")
    print("=" * 60)
    for p in reinstallable:
        print(f"/plugin uninstall {p['full_name']}")

    print("\n" + "=" * 60)
    print("INSTALL PHASE - Run these commands in order:")
    print("=" * 60)
    for p in reinstallable:
        print(f"/plugin install {p['full_name']}")

    print("\n" + "=" * 60)
    print("After completing all commands, restart Claude Code.")
    print("=" * 60)


def generate_script(
    reinstallable: list[dict[str, Any]], excluded: list[dict[str, Any]]
) -> None:
    """Generate a bash script for terminal execution."""
    script_path = Path("/tmp/reinstall-plugins.sh")

    plugin_list = "\n".join(f'  "{p["full_name"]}"' for p in reinstallable)
    excluded_note = ", ".join(p["name"] for p in excluded) if excluded else "none"

    script_content = f"""#!/bin/bash
# Generated reinstall script for Claude Code plugins
# Run from terminal: bash {script_path}
#
# Excluded plugins (not touched): {excluded_note}

set -e

PLUGINS=(
{plugin_list}
)

echo "Reinstalling ${{#PLUGINS[@]}} plugins..."
echo "(Excluded: {excluded_note})"
echo ""

echo "Phase 1: Uninstalling plugins..."
for plugin in "${{PLUGINS[@]}}"; do
  echo "  Uninstalling $plugin..."
  claude plugin uninstall "$plugin" 2>/dev/null || echo "    Warning: uninstall may have failed"
done

echo ""
echo "Phase 2: Installing plugins..."
for plugin in "${{PLUGINS[@]}}"; do
  echo "  Installing $plugin..."
  claude plugin install "$plugin" || echo "    ERROR: Failed to install $plugin"
done

echo ""
echo "Reinstall complete. Restart Claude Code to apply changes."
"""

    script_path.write_text(script_content)
    script_path.chmod(0o755)

    print(f"\nGenerated reinstall script: {script_path}")
    print(f"  - {len(reinstallable)} plugins to reinstall")
    print(f"  - {len(excluded)} excluded")
    print(f"\nRun with: bash {script_path}")


def execute_reinstall(
    reinstallable: list[dict[str, Any]], excluded: list[dict[str, Any]]
) -> None:
    """Execute the reinstall process directly."""
    import subprocess

    print(f"\nReinstalling {len(reinstallable)} plugins...")
    if excluded:
        print(f"Excluded: {', '.join(p['name'] for p in excluded)}")
    print("")

    failed_uninstall = []
    failed_install = []

    # Phase 1: Uninstall
    print("Phase 1: Uninstalling plugins...")
    print("-" * 40)
    for p in reinstallable:
        print(f"  Uninstalling {p['name']}...", end=" ", flush=True)
        try:
            result = subprocess.run(
                ["claude", "plugin", "uninstall", p["full_name"]],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                print("[OK]")
            else:
                print("[WARN]")
                failed_uninstall.append(p)
        except subprocess.TimeoutExpired:
            print("[TIMEOUT]")
            failed_uninstall.append(p)
        except Exception as e:
            print(f"[ERROR: {e}]")
            failed_uninstall.append(p)

    # Phase 2: Install
    print("\nPhase 2: Installing plugins...")
    print("-" * 40)
    for p in reinstallable:
        print(f"  Installing {p['name']}...", end=" ", flush=True)
        try:
            result = subprocess.run(
                ["claude", "plugin", "install", p["full_name"]],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                print("[OK]")
            else:
                print("[FAILED]")
                if result.stderr:
                    print(f"    Error: {result.stderr.strip()}")
                failed_install.append(p)
        except subprocess.TimeoutExpired:
            print("[TIMEOUT]")
            failed_install.append(p)
        except Exception as e:
            print(f"[ERROR: {e}]")
            failed_install.append(p)

    # Summary
    print("\n" + "=" * 50)
    print("REINSTALL SUMMARY")
    print("=" * 50)
    print(f"Total plugins: {len(reinstallable)}")
    print(f"Excluded: {len(excluded)}")
    print(f"Uninstall warnings: {len(failed_uninstall)}")
    print(f"Install failures: {len(failed_install)}")

    if failed_install:
        print("\n[FAILED INSTALLS]:")
        for p in failed_install:
            print(f"  - {p['full_name']}")

    if not failed_install:
        print("\nAll plugins reinstalled successfully!")
    else:
        print(f"\n{len(failed_install)} plugin(s) failed to install.")

    print("\nRestart Claude Code to apply changes.")

    if failed_install:
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reinstall all Claude Code plugins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--generate-script",
        action="store_true",
        help="Generate a bash script instead of executing directly",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list plugins and generate copy-paste commands",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    args = parser.parse_args()

    # Read and categorize plugins
    plugins = read_installed_plugins()
    if not plugins:
        print("[ERROR] No plugins found")
        sys.exit(1)

    reinstallable, excluded = categorize_plugins(plugins)

    if not reinstallable:
        print("[INFO] No plugins to reinstall (all excluded)")
        return

    # Execute based on mode
    if args.list_only:
        generate_commands(reinstallable, excluded)
    elif args.generate_script:
        generate_script(reinstallable, excluded)
    elif args.dry_run:
        print("[DRY RUN] Would reinstall the following plugins:\n")
        print_plugin_table(reinstallable, "Plugins to reinstall:")
        if excluded:
            print_plugin_table(excluded, "Excluded plugins:")
        print(f"\nTotal: {len(reinstallable)} plugins would be reinstalled")
    else:
        execute_reinstall(reinstallable, excluded)


if __name__ == "__main__":
    main()
