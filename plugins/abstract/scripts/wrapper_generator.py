#!/usr/bin/env python3
"""Wrapper Generator - Generate wrapper boilerplate for plugin commands.

This script generates wrapper classes that delegate to superpowers with
plugin-specific extensions and parameter mappings.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def generate_wrapper(
    plugin_name: str,
    command_name: str,
    target_superpower: str,
    output_path: Path | None = None,
) -> str:
    """Generate a wrapper class for delegating to a superpower.

    Args:
        plugin_name: Name of the plugin (e.g., "sanctum", "pensive")
        command_name: Name of the command (e.g., "pr-review", "refine-code")
        target_superpower: Name of the superpower to wrap (e.g., "CodeReviewer")
        output_path: Optional path to write the wrapper file

    Returns:
        Generated wrapper code as string

    """
    # Convert names to Python class/module format
    class_name = "".join(word.capitalize() for word in command_name.split("-"))

    wrapper_code = f'''"""Wrapper for {command_name} command.

This module wraps the {target_superpower} superpower with {plugin_name}-specific
parameter mappings and extensions.
"""

from typing import Any

from abstract.superpowers.{target_superpower.lower()} import {target_superpower}


class {class_name}Wrapper:
    """Wrapper for {command_name} command in {plugin_name} plugin.

    This class delegates to {target_superpower} while providing
    plugin-specific parameter mappings and customizations.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize wrapper with plugin-specific configuration.

        Args:
            **kwargs: Plugin-specific parameters to map to superpower

        """
        self.superpower = {target_superpower}()
        self.config = kwargs

    def execute(self, **params: Any) -> Any:
        """Execute the wrapped superpower with parameter mapping.

        Args:
            **params: Command parameters to map to superpower

        Returns:
            Result from superpower execution

        """
        # Map plugin parameters to superpower parameters
        mapped_params = self._map_parameters(params)

        # Delegate to superpower
        return self.superpower.execute(**mapped_params)

    def _map_parameters(self, params: dict[str, Any]) -> dict[str, Any]:
        """Map plugin-specific parameters to superpower parameters.

        Args:
            params: Plugin command parameters

        Returns:
            Mapped parameters for superpower

        """
        # TODO: Implement plugin-specific parameter mapping
        # This is a placeholder - customize based on actual needs
        return params


def main() -> {class_name}Wrapper:
    """Create and return wrapper instance.

    Returns:
        Configured wrapper instance

    """
    return {class_name}Wrapper()
'''

    # Write to file if output_path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(wrapper_code)
        print(f"✓ Generated wrapper: {output_path}")

    return wrapper_code


def auto_detect_wrappers(repo_root: Path) -> list[tuple[str, str, str]]:
    """Scan repository for wrappers that need generation.

    Args:
        repo_root: Root path of the repository

    Returns:
        List of (plugin_name, command_name, target_superpower) tuples

    """
    wrappers_needed = []

    # Scan plugins directory for command files that reference superpowers
    plugins_dir = repo_root / "plugins"

    if not plugins_dir.exists():
        print(f"✗ Plugins directory not found: {plugins_dir}", file=sys.stderr)
        return []

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir() or plugin_dir.name.startswith("."):
            continue

        plugin_name = plugin_dir.name
        commands_dir = plugin_dir / "commands"

        if not commands_dir.exists():
            continue

        # Scan markdown files for superpower references
        for cmd_file in commands_dir.glob("*.md"):
            command_name = cmd_file.stem
            content = cmd_file.read_text()

            # Look for superpower references (simple heuristic)
            if "superpower:" in content.lower() or "delegates to" in content.lower():
                # Extract superpower name (basic pattern matching)
                # This is a placeholder - would need more sophisticated parsing
                wrappers_needed.append((plugin_name, command_name, "BaseSuperpower"))

    return wrappers_needed


def main() -> None:
    """Generate wrapper implementations."""
    parser = argparse.ArgumentParser(
        description="Generate wrapper boilerplate for plugin commands"
    )
    parser.add_argument(
        "--plugin",
        help="Plugin name (e.g., sanctum, pensive)",
    )
    parser.add_argument(
        "--command",
        help="Command name (e.g., pr-review, refine-code)",
    )
    parser.add_argument(
        "--superpower",
        help="Target superpower to wrap (e.g., CodeReviewer)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path for generated wrapper",
    )
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect and generate all needed wrappers",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory)",
    )

    args = parser.parse_args()

    if args.auto_detect:
        # Auto-detect mode
        repo_root = args.repo_root.resolve()
        print(f"Scanning for wrappers in: {repo_root}")

        wrappers = auto_detect_wrappers(repo_root)

        if not wrappers:
            print("No wrappers detected that need generation.")
            return

        print(f"\nFound {len(wrappers)} wrappers to generate:")
        for plugin, command, superpower in wrappers:
            print(f"  - {plugin}/{command} -> {superpower}")

            # Generate wrapper
            output_dir = repo_root / "plugins" / plugin / "wrappers"
            output_file = output_dir / f"{command.replace('-', '_')}_wrapper.py"
            generate_wrapper(plugin, command, superpower, output_file)

    elif args.plugin and args.command and args.superpower:
        # Manual mode
        code = generate_wrapper(args.plugin, args.command, args.superpower, args.output)

        if not args.output:
            # Print to stdout if no output file specified
            print(code)
    else:
        parser.error(
            "Either --auto-detect or all of --plugin, --command, "
            "--superpower are required"
        )


if __name__ == "__main__":
    main()
