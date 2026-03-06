"""Report generation and main orchestration for the dogfooder package."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dogfooder.parser import (
    DocumentationCommandExtractor,
    MakefileAnalyzer,
    load_target_catalog,
)
from dogfooder.validator import MakefileTargetGenerator, generate_makefile

MIN_TARGET_PARTS = 2  # Minimum parts for target name splitting
PHONY_LINE_LENGTH_LIMIT = 100  # Max line length for .PHONY declarations
MAX_MISSING_DISPLAY = 5


@dataclass
class ProcessingConfig:
    """Configuration for plugin processing operations."""

    mode: str
    generate_missing: bool
    dry_run: bool
    verbose: bool


class MakefileDogfooder:
    """Main orchestrator for makefile dogfooding."""

    def __init__(
        self,
        root_dir: Path | None = None,
        plugins_dir: str = "plugins",
        verbose: bool = False,
        dry_run: bool = False,
        explain: bool = False,
    ):
        self.root_dir = root_dir or Path.cwd()
        self.plugins_dir = plugins_dir
        self.plugin_base = self.root_dir / plugins_dir
        self.verbose = verbose
        self.dry_run = dry_run
        self.explain = explain

        # Load target catalog
        catalog = load_target_catalog()
        self.essential_targets = catalog["essential_targets"]
        self.recommended_targets = catalog["recommended_targets"]
        self.convenience_targets = catalog["convenience_targets"]
        self.skip_dirs = catalog["skip_dirs"]

        self.extractor = DocumentationCommandExtractor(self.root_dir)
        self.generator = MakefileTargetGenerator(self.root_dir)

        self.report: dict[str, Any] = {
            "plugins_analyzed": 0,
            "commands_found": 0,
            "targets_missing": 0,
            "targets_generated": 0,
            "findings": [],
        }

    def analyze_plugin(
        self, plugin_name: str, generate_missing: bool = False
    ) -> dict[str, Any]:
        """Analyze a single plugin for dogfood coverage.

        Args:
            plugin_name: Name of the plugin to analyze
            generate_missing: If True, generate Makefile if it doesn't exist

        Returns:
            Dictionary with analysis results

        """
        plugin_dir = self.plugin_base / plugin_name
        readme_path = plugin_dir / "README.md"
        makefile_path = plugin_dir / "Makefile"

        if not readme_path.exists():
            return {"plugin": plugin_name, "status": "no-readme"}

        # Generate Makefile if missing and requested
        if not makefile_path.exists():
            if generate_missing:
                print(f"\n{plugin_name}: No Makefile found, generating...")
                success = generate_makefile(
                    plugin_dir,
                    plugin_name,
                    dry_run=self.dry_run,
                )
                if not success:
                    return {
                        "plugin": plugin_name,
                        "status": "makefile-generation-failed",
                    }
            else:
                return {"plugin": plugin_name, "status": "no-makefile"}

        # Extract documented commands
        commands = self.extractor.extract_from_file(readme_path)

        # Analyze existing Makefile
        analyzer = MakefileAnalyzer(makefile_path)

        # Find what's missing
        required_targets: set[str] = set()
        for cmd in commands:
            if cmd.get("type") == "slash-command":
                target_name = cmd["command"].replace("/", "").lstrip("/")
                required_targets.add(f"demo-{target_name}")
                required_targets.add(f"test-{target_name}")

        missing_targets = analyzer.get_missing_targets(required_targets)

        finding = {
            "plugin": plugin_name,
            "readme": str(readme_path.relative_to(self.root_dir)),
            "makefile": str(makefile_path.relative_to(self.root_dir)),
            "commands_documented": len(commands),
            "targets_exist": len(analyzer.targets),
            "targets_missing": len(missing_targets),
            "missing_targets": sorted(missing_targets),
            "coverage_percent": self._calc_coverage(
                len(required_targets),
                len(analyzer.targets),
            ),
        }

        self.report["findings"].append(finding)
        self.report["commands_found"] += len(commands)
        self.report["targets_missing"] += len(missing_targets)

        return finding

    def _calc_coverage(self, required: int, exist: int) -> int:
        """Calculate coverage percentage."""
        if required == 0:
            return 100
        return min(100, int((exist / required) * 100))

    def generate_missing_targets(
        self,
        plugin_name: str,
        finding: dict[str, Any],
    ) -> str:
        """Generate make targets for missing coverage."""
        readme_path = self.root_dir / finding["readme"]
        commands = self.extractor.extract_from_file(readme_path)

        # Generate all demo targets for this plugin
        generated = self.generator.generate_demo_targets(
            plugin_name,
            commands,
        )

        # Count how many targets we generated
        target_count = generated.count("## ")  # Each target has one ## comment
        self.report["targets_generated"] += target_count

        return generated

    def _filter_duplicate_targets(
        self,
        generated_content: str,
        existing_targets: set[str],
    ) -> list[str]:
        """Filter out targets that already exist.

        Args:
            generated_content: Generated Makefile content
            existing_targets: Set of existing target names

        Returns:
            List of non-duplicate content lines

        """
        filtered_content = []
        skip_current_target = False
        for line in generated_content.splitlines():
            # Check if this line defines a new target
            target_match = re.match(r"^([a-zA-Z][\w-]+)\s*:", line)
            if target_match:
                target_name = target_match.group(1)
                if target_name not in existing_targets:
                    skip_current_target = False
                    filtered_content.append(line)
                    existing_targets.add(target_name)  # Mark as added
                else:
                    skip_current_target = True
            elif skip_current_target:
                # Skip recipe lines belonging to a duplicate target
                if not line.startswith("\t") and line.strip():
                    skip_current_target = False
                    filtered_content.append(line)
            # Keep non-target lines (recipes, comments, etc.)
            elif filtered_content or line.strip():  # Don't add leading empty lines
                filtered_content.append(line)

        return filtered_content

    def _insert_content_before_catchall(
        self,
        content: str,
        final_content: str,
        catchall_pattern: str,
    ) -> str:
        """Insert content before catch-all rule.

        Args:
            content: Original Makefile content
            final_content: Content to insert
            catchall_pattern: Pattern identifying catch-all rule

        Returns:
            Updated Makefile content

        """
        if catchall_pattern in content:
            parts = content.split(catchall_pattern, 1)
            if len(parts) == MIN_TARGET_PARTS:
                return (
                    parts[0].rstrip()
                    + "\n\n"
                    + final_content
                    + "\n\n"
                    + catchall_pattern
                    + parts[1]
                )
        return content.rstrip() + "\n\n" + final_content + "\n"

    def _insert_content_before_percent_colon(
        self,
        content: str,
        final_content: str,
    ) -> str:
        """Insert content before %:: rule.

        Args:
            content: Original Makefile content
            final_content: Content to insert

        Returns:
            Updated Makefile content

        """
        parts = content.split("%::", 1)
        if len(parts) == MIN_TARGET_PARTS:
            prefix = parts[0].rstrip()
            return (
                prefix + "\n\n" + final_content + "\n\n# Catch-all rule\n%::" + parts[1]
            )
        return content.rstrip() + "\n\n" + final_content + "\n"

    def _determine_insertion_strategy(
        self,
        content: str,
        final_content: str,
    ) -> str:
        """Determine where to insert new content in Makefile.

        Args:
            content: Original Makefile content
            final_content: Content to insert

        Returns:
            Updated Makefile content

        """
        if "%::" in content:
            catch_all_pattern = "\n\n# Guard against accidental file creation"
            if catch_all_pattern in content:
                return self._insert_content_before_catchall(
                    content, final_content, catch_all_pattern
                )
            return self._insert_content_before_percent_colon(content, final_content)
        return content.rstrip() + "\n\n" + final_content + "\n"

    def apply_targets_to_makefile(
        self,
        plugin_name: str,
        finding: dict[str, Any],
        generated_content: str,
        dry_run: bool = False,
    ) -> bool:
        """Apply generated targets to the plugin's Makefile.

        Args:
            plugin_name: Name of the plugin
            finding: Analysis finding with Makefile path
            generated_content: Generated Makefile content
            dry_run: If True, don't actually write files

        Returns:
            True if successfully applied, False otherwise

        """
        makefile_path = self.root_dir / finding["makefile"]

        if not makefile_path.exists():
            print(f"Warning: Makefile not found for {plugin_name}: {makefile_path}")
            return False

        # Read existing Makefile
        content = makefile_path.read_text()

        # Parse existing targets to check for duplicates
        existing_targets: set[str] = set()
        for line in content.splitlines():
            match = re.match(r"^([a-zA-Z][\w-]+)\s*:", line)
            if match:
                existing_targets.add(match.group(1))

        # Filter out targets that already exist
        filtered_content = self._filter_duplicate_targets(
            generated_content, existing_targets
        )

        if not filtered_content:
            print(f"  All targets already exist in {makefile_path.name}")
            return True

        # Join filtered content
        final_content = "\n".join(filtered_content).strip() + "\n"

        # Determine insertion strategy and apply
        new_content = self._determine_insertion_strategy(content, final_content)

        # Write back
        if not dry_run:
            makefile_path.write_text(new_content)
            print(f"Updated {makefile_path}")
        else:
            print(f"[DRY RUN] Would update {makefile_path}")

        return True

    def _find_phony_block(self, content: str) -> list[str]:
        """Find .PHONY declaration block in Makefile content.

        Args:
            content: Makefile content

        Returns:
            List of lines in the .PHONY block, or empty list if not found

        """
        phony_lines = []
        in_phony = False

        for line in content.splitlines():
            if line.strip().startswith(".PHONY:"):
                in_phony = True
                phony_lines = [line]
            elif in_phony:
                if line.endswith("\\"):
                    phony_lines.append(line)
                else:
                    # End of .PHONY block
                    phony_lines.append(line)
                    break

        return phony_lines

    def _extract_phony_targets(self, phony_lines: list[str]) -> list[str]:
        """Extract .PHONY target names from .PHONY block lines.

        Args:
            phony_lines: List of lines from .PHONY block

        Returns:
            List of target names

        """
        existing_phony = []
        for line in phony_lines:
            cleaned = line.replace(".PHONY:", "").replace("\\", "").strip()
            if cleaned:
                existing_phony.extend(cleaned.split())

        return existing_phony

    def _build_phony_block(self, all_targets: list[str]) -> list[str]:
        """Build formatted .PHONY block with proper line breaks.

        Args:
            all_targets: List of all target names to include

        Returns:
            List of formatted lines for .PHONY block

        """
        new_phony_lines = []
        current_line = ".PHONY:"

        for target in all_targets:
            test_line = current_line + " " + target
            if len(test_line) > PHONY_LINE_LENGTH_LIMIT:
                new_phony_lines.append(current_line + " \\")
                current_line = "\t" + target
            else:
                current_line = test_line

        new_phony_lines.append(current_line)

        return new_phony_lines

    def fix_makefile_pronounce(
        self,
        plugin_name: str,
        finding: dict[str, Any],
        dry_run: bool = False,
    ) -> bool:
        """Update .PHONY declaration to include new targets.

        Preserves multi-line .PHONY format with backslash continuations.

        Args:
            plugin_name: Name of the plugin
            finding: Analysis finding
            dry_run: If True, don't actually write files

        Returns:
            True if successfully updated, False otherwise

        """
        makefile_path = self.root_dir / finding["makefile"]

        if not makefile_path.exists():
            return False

        content = makefile_path.read_text()
        missing = finding["missing_targets"]

        if not missing:
            return True

        phony_lines = self._find_phony_block(content)

        if not phony_lines:
            print(f"Warning: No .PHONY declaration found in {makefile_path}")
            return False

        existing_phony = self._extract_phony_targets(phony_lines)
        existing_set = set(existing_phony)

        new_targets = [m for m in missing if m not in existing_set]

        if not new_targets:
            return True

        all_targets = sorted(existing_phony + new_targets)
        new_phony_lines = self._build_phony_block(all_targets)

        old_phony_text = "\n".join(phony_lines)
        new_phony_text = "\n".join(new_phony_lines)

        new_content = content.replace(old_phony_text, new_phony_text, 1)

        if not dry_run:
            makefile_path.write_text(new_content)
            print(f"  Updated .PHONY with {len(new_targets)} new targets")
        else:
            print(
                f"  [DRY RUN] Would update .PHONY with {len(new_targets)} new targets"
            )

        return True

    def analyze_all(self, generate_missing: bool = False) -> dict[str, Any]:
        """Analyze all plugins.

        Args:
            generate_missing: If True, generate Makefiles for plugins without them

        """
        plugin_dirs = [d for d in self.plugin_base.iterdir() if d.is_dir()]
        self.report["plugins_analyzed"] = len(plugin_dirs)

        for plugin_dir in plugin_dirs:
            plugin_name = plugin_dir.name
            if plugin_name.startswith(".") or plugin_name == "shared":
                continue

            finding = self.analyze_plugin(
                plugin_name, generate_missing=generate_missing
            )

            if self.verbose and "commands_documented" in finding:
                print(f"\n{plugin_name}:")
                print(f"  Commands documented: {finding['commands_documented']}")
                print(f"  Targets missing: {finding['targets_missing']}")
                print(f"  Coverage: {finding['coverage_percent']}%")

        return self.report

    def generate_report(self, output_format: str = "text") -> str:
        """Generate analysis report."""
        if output_format == "json":
            return json.dumps(self.report, indent=2)

        lines = [
            "=" * 60,
            "Makefile Dogfooding Report",
            "=" * 60,
            "",
            f"Plugins analyzed: {self.report['plugins_analyzed']}",
            f"Commands found in docs: {self.report['commands_found']}",
            f"Targets missing: {self.report['targets_missing']}",
            f"Targets generated: {self.report['targets_generated']}",
            "",
            "Findings by Plugin:",
            "-" * 60,
        ]

        for finding in self.report["findings"]:
            lines.append(f"\n{finding['plugin']}:")
            lines.append(f"  Coverage: {finding['coverage_percent']}%")
            lines.append(f"  Commands documented: {finding['commands_documented']}")
            lines.append(f"  Targets missing: {finding['targets_missing']}")

            if finding["missing_targets"]:
                lines.append(
                    "  Missing: {}".format(
                        ", ".join(finding["missing_targets"][:MAX_MISSING_DISPLAY])
                    )
                )
                if len(finding["missing_targets"]) > MAX_MISSING_DISPLAY:
                    lines.append(
                        "    ... and {} more".format(
                            len(finding["missing_targets"]) - MAX_MISSING_DISPLAY
                        )
                    )

        lines.append("\n" + "=" * 60)
        lines.append("Recommendations:")
        lines.append("=" * 60)
        lines.append("1. Generate missing demo targets for each plugin")
        lines.append("2. Add test-* targets for slash commands")
        lines.append("3. Run generated targets as part of CI/CD pipeline")
        lines.append("4. Keep Makefiles in sync with documentation updates")

        return "\n".join(lines)
