#!/usr/bin/env python3
"""Makefile Dogfooder - Comprehensive QA for Documentation Coverage.

This script ensures that every command documented in READMEs and docs has
a corresponding make target that executes it, acting as first-line QA defense.

Core Philosophy:
- If a command is documented, users will try it
- Make targets provide consistent, version-controlled execution
- Dogfooding catches edge cases static analysis misses

This file is a thin CLI wrapper. All logic lives in the dogfooder/ package:
    dogfooder/parser.py    - Makefile parsing and target analysis
    dogfooder/validator.py - Recipe validation and Makefile generation
    dogfooder/reporter.py  - Report generation and main orchestration
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Re-export package symbols for backward compatibility with existing imports
# (e.g. tests that do: from makefile_dogfooder import MakefileDogfooder)
from dogfooder import (  # noqa: F401
    DocumentationCommandExtractor,
    MakefileAnalyzer,
    MakefileDogfooder,
    MakefileTargetGenerator,
    ProcessingConfig,
    generate_makefile,
    load_target_catalog,
    run_preflight_checks,
    validate_working_directory,
)


def _process_single_plugin(
    dogfooder: MakefileDogfooder,
    plugin_name: str,
    config: ProcessingConfig,
) -> int:
    """Process a single plugin for dogfooding.

    Args:
        dogfooder: MakefileDogfooder instance
        plugin_name: Name of the plugin to process
        config: Processing configuration

    Returns:
        Exit code (0 for success, non-zero for failure)

    """
    finding = dogfooder.analyze_plugin(
        plugin_name, generate_missing=config.generate_missing
    )
    if config.verbose:
        print(json.dumps(finding, indent=2))

    if config.mode not in ["generate", "apply"]:
        return 0

    if finding["targets_missing"] == 0:
        return 0

    generated = dogfooder.generate_missing_targets(
        plugin_name,
        finding,
    )

    if config.mode == "generate":
        print("\n" + "=" * 60)
        print(f"Generated targets for {plugin_name}:")
        print("=" * 60)
        print(generated)
        return 0

    # mode == "apply"
    if not config.dry_run:
        print("\nWARNING: Applying changes without --dry-run")
        response = input("Continue? (y/N): ")
        if response.lower() != "y":
            print("Aborted. Use --dry-run to preview changes first.")
            return 0

    dogfooder.apply_targets_to_makefile(
        plugin_name,
        finding,
        generated,
        dry_run=config.dry_run,
    )
    dogfooder.fix_makefile_pronounce(
        plugin_name,
        finding,
        dry_run=config.dry_run,
    )

    if not config.dry_run:
        print(f"\nSuccessfully applied changes to {plugin_name}")
        print(f"   Test with: cd plugins/{plugin_name} && make help")

    return 0


def _process_all_plugins(
    dogfooder: MakefileDogfooder,
    config: ProcessingConfig,
) -> None:
    """Process all plugins for dogfooding.

    Args:
        dogfooder: MakefileDogfooder instance
        config: Processing configuration

    """
    dogfooder.analyze_all(generate_missing=config.generate_missing)

    if config.mode not in ["generate", "apply"]:
        return

    print("\n" + "=" * 60)
    print("Generating targets for all plugins...")
    print("=" * 60)

    for finding in dogfooder.report["findings"]:
        plugin_name = finding["plugin"]
        if finding["targets_missing"] > 0:
            print(f"\n{plugin_name}:")
            generated = dogfooder.generate_missing_targets(
                plugin_name,
                finding,
            )

            if config.mode == "generate":
                print(generated)

            if config.mode == "apply":
                dogfooder.apply_targets_to_makefile(
                    plugin_name,
                    finding,
                    generated,
                    dry_run=config.dry_run,
                )
                dogfooder.fix_makefile_pronounce(
                    plugin_name,
                    finding,
                    dry_run=config.dry_run,
                )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Makefile dogfooding for documentation coverage",
        epilog="Lessons learned: Always test with --dry-run before applying changes.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of project",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed progress"
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview changes without writing files (RECOMMENDED for testing)",
    )
    parser.add_argument("--output", "-o", choices=["text", "json"], default="text")
    parser.add_argument(
        "--plugin",
        help="Analyze specific plugin only (test on one before applying to all)",
    )
    parser.add_argument(
        "--plugins-dir",
        default="plugins",
        help="Subdirectory containing projects (default: plugins)",
    )
    parser.add_argument(
        "--mode",
        choices=["analyze", "generate", "apply"],
        default="analyze",
        help=(
            "Operation mode: analyze (report only), generate (show targets), "
            "apply (write to Makefiles). "
            "RECOMMENDED: Use 'generate' first to preview, then 'apply' with --dry-run."
        ),
    )
    parser.add_argument(
        "--preflight-check",
        action="store_true",
        help=(
            "Run pre-flight checks before processing "
            "(validates directories, files, permissions)"
        ),
    )
    parser.add_argument(
        "--generate-makefiles",
        action="store_true",
        help=(
            "Generate Makefiles for plugins that don't have one "
            "(follows attune:makefile-generation pattern)"
        ),
    )
    args = parser.parse_args()

    # Preflight checks if requested or in apply mode
    if args.preflight_check or args.mode == "apply":
        if not run_preflight_checks(args.root, args.plugins_dir):
            return 1

    dogfooder = MakefileDogfooder(
        root_dir=args.root,
        plugins_dir=args.plugins_dir,
        verbose=args.verbose,
        dry_run=args.dry_run,
    )

    # Validate working directory before processing
    if not validate_working_directory(args.root, args.plugins_dir, args.plugin):
        return 1

    # Create processing configuration
    config = ProcessingConfig(
        mode=args.mode,
        generate_missing=args.generate_makefiles,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    if args.plugin:
        return _process_single_plugin(dogfooder, args.plugin, config)

    # Process all plugins
    _process_all_plugins(dogfooder, config)

    print(dogfooder.generate_report(output_format=args.output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
