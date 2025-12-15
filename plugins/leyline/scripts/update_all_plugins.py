#!/usr/bin/env python3
"""Update all Claude Code plugins from their respective marketplaces.

This script reads the installed plugins configuration and updates each plugin.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_installed_plugins() -> dict[str, list[dict[str, Any]]]:
    """Read the installed plugins configuration file."""
    plugins_file = Path.home() / ".claude" / "plugins" / "installed_plugins_v2.json"

    if not plugins_file.exists():
        print(f"[ERROR] Plugins configuration file not found: {plugins_file}")
        sys.exit(1)

    with open(plugins_file) as f:
        data = json.load(f)

    # Ensure we return the expected type structure
    plugins: dict[str, list[dict[str, Any]]] = data.get("plugins", {})
    return plugins


def update_plugin(plugin_full_name: str) -> tuple[bool, str, str]:
    """Update a single plugin and return (success, old_version, new_version)."""
    try:
        # Run the update command
        result = subprocess.run(
            ["claude", "plugin", "update", plugin_full_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # Parse output to determine if plugin was updated
            output = result.stdout

            # Check for "already at latest version" message
            if "already at the latest version" in output:
                # Extract version from output
                version_match = re.search(r"\(([^)]+)\)", output)
                version = version_match.group(1) if version_match else "unknown"
                return True, version, version

            # Check for successful update
            if "updated from" in output:
                # Extract old and new versions
                old_match = re.search(r"updated from ([^ ]+) to", output)
                new_match = re.search(r"to ([^.]+)", output)
                old_version = old_match.group(1) if old_match else "unknown"
                new_version = new_match.group(1) if new_match else "unknown"
                return True, old_version, new_version

            # Assume success but couldn't parse versions
            return True, "unknown", "unknown"

        else:
            return False, "error", "error"

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Timeout updating {plugin_full_name}")
        return False, "timeout", "timeout"

    except Exception as e:
        print(f"[ERROR] Error updating {plugin_full_name}: {e}")
        return False, "error", "error"


# Maximum number of plugins to show in "already latest" list
MAX_SHOW_PLUGINS = 5


def process_plugin(
    plugin_full_name: str, plugin_info: dict[str, Any]
) -> dict[str, Any]:
    """Process a single plugin and return the result."""
    plugin_name = plugin_full_name.split("@")[0]
    if "@" in plugin_full_name:
        marketplace = plugin_full_name.split("@")[1]
    else:
        marketplace = "unknown"
    current_version = plugin_info.get("version", "unknown")

    print(f"Updating {plugin_name} from {marketplace}...")

    success, old_version, new_version = update_plugin(plugin_full_name)

    if success:
        if old_version == new_version:
            print(f"   [OK] Already at latest version ({new_version})")
            return {
                "status": "latest",
                "name": plugin_name,
                "marketplace": marketplace,
                "version": new_version,
            }
        else:
            print(f"   [UPDATED] {old_version} -> {new_version}")
            return {
                "status": "updated",
                "name": plugin_name,
                "marketplace": marketplace,
                "old_version": old_version,
                "new_version": new_version,
            }
    else:
        print("   [FAILED] Could not update")
        return {
            "status": "failed",
            "name": plugin_name,
            "marketplace": marketplace,
            "version": current_version,
        }


def main() -> None:
    """Main update logic."""
    print("Updating all Claude Code plugins...\n")

    # Read installed plugins
    plugins = read_installed_plugins()

    if not plugins:
        print("[ERROR] No plugins found in configuration")
        return

    # Statistics
    total_plugins = 0
    updated_plugins: list[dict[str, Any]] = []
    already_latest: list[dict[str, Any]] = []
    failed_plugins: list[dict[str, Any]] = []

    # Process each plugin
    for plugin_full_name, plugin_list in plugins.items():
        for plugin_info in plugin_list:
            total_plugins += 1
            result = process_plugin(plugin_full_name, plugin_info)

            if result["status"] == "latest":
                already_latest.append(result)
            elif result["status"] == "updated":
                updated_plugins.append(result)
            else:
                failed_plugins.append(result)

    # Print summary
    print_summary(total_plugins, updated_plugins, already_latest, failed_plugins)


def print_summary(
    total_plugins: int,
    updated_plugins: list[dict[str, Any]],
    already_latest: list[dict[str, Any]],
    failed_plugins: list[dict[str, Any]],
) -> None:
    """Print the update summary."""
    print("\n" + "=" * 50)
    print("UPDATE SUMMARY")
    print("=" * 50)
    print(f"Total plugins: {total_plugins}")
    print(f"Updated: {len(updated_plugins)}")
    print(f"Already latest: {len(already_latest)}")
    print(f"Failed: {len(failed_plugins)}")

    if updated_plugins:
        print("\n[UPDATED] PLUGINS:")
        for plugin in updated_plugins:
            print(
                f"  - {plugin['name']}@{plugin['marketplace']}: "
                f"{plugin['old_version']} -> {plugin['new_version']}"
            )

    if already_latest:
        print(f"\n[UP-TO-DATE] ({len(already_latest)} plugins):")
        for plugin in already_latest[:MAX_SHOW_PLUGINS]:  # Show first few
            print(f"  - {plugin['name']}@{plugin['marketplace']} ({plugin['version']})")
        if len(already_latest) > MAX_SHOW_PLUGINS:
            print(f"  ... and {len(already_latest) - MAX_SHOW_PLUGINS} more")

    if failed_plugins:
        print(f"\n[FAILED] ({len(failed_plugins)} plugins):")
        for plugin in failed_plugins:
            print(f"  - {plugin['name']}@{plugin['marketplace']}")

    if updated_plugins:
        print("\n[NOTE] Restart Claude Code to apply the updated plugins.")

    print("\nUpdate process complete!")
