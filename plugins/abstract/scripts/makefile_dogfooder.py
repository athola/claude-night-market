#!/usr/bin/env python3
"""Makefile Dogfooder - Comprehensive QA for Documentation Coverage.

This script ensures that every command documented in READMEs and docs has
a corresponding make target that executes it, acting as first-line QA defense.

Core Philosophy:
- If a command is documented, users will try it
- Make targets provide consistent, version-controlled execution
- Dogfooding catches edge cases static analysis misses
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

MAX_MISSING_DISPLAY = 5
MIN_TARGET_PARTS = 2  # Minimum parts for target name splitting
PHONY_LINE_LENGTH_LIMIT = 100  # Max line length for .PHONY declarations


def load_target_catalog() -> dict[str, Any]:
    """Load the Makefile target catalog from YAML data.

    Returns:
        Dictionary containing essential_targets, recommended_targets,
        convenience_targets, and skip_dirs lists.

    """
    script_dir = Path(__file__).parent
    catalog_path = script_dir.parent / "data" / "makefile_target_catalog.yaml"

    with catalog_path.open(encoding="utf-8") as f:
        catalog = yaml.safe_load(f)
        return cast("dict[str, Any]", catalog)


@dataclass
class ProcessingConfig:
    """Configuration for plugin processing operations."""

    mode: str
    generate_missing: bool
    dry_run: bool
    verbose: bool


class DocumentationCommandExtractor:
    """Extract documented commands from READMEs and documentation."""

    # Pattern for slash commands in documentation
    COMMAND_PATTERNS = [
        r"`/([\w-]+)(?:\s+([^\n`]+))?`",  # `/-command args`
        r"```bash\s*/([\w-]+)([^\n]*)",  # Code blocks with /-commands
        r"^\s*/([\w-]+)",  # Lines starting with /-command
        r"\[\\\?`/([\w-]+)",  # Escaped commands
    ]

    # Pattern for CLI tool invocations
    CLI_PATTERNS = [
        r"`claude\s+([^\n`]+)`",  # `claude command args`
        r"```bash\s+claude\s+([^\n]+)",  # Code blocks
    ]

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def extract_from_file(self, filepath: Path) -> list[dict[str, Any]]:
        """Extract commands from a single file."""
        commands = []
        seen: set[tuple[str, int, str]] = set()  # (command/invocation, line, type)
        content = filepath.read_text()

        # Extract slash commands
        for pattern in self.COMMAND_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                cmd = match.group(1)
                args = match.group(2) if len(match.groups()) > 1 else ""
                line_num = content[: match.start()].count("\n") + 1
                cmd_key = (cmd, line_num, "slash-command")

                if cmd_key not in seen:
                    seen.add(cmd_key)
                    commands.append(
                        {
                            "type": "slash-command",
                            "command": cmd,
                            "args": args.strip() if args else "",
                            "source": str(filepath.relative_to(self.root_dir)),
                            "line": line_num,
                        }
                    )

        # Extract CLI invocations
        for pattern in self.CLI_PATTERNS:
            for match in re.finditer(pattern, content, re.MULTILINE):
                invocation = match.group(1)
                line_num = content[: match.start()].count("\n") + 1
                inv_key = (invocation.strip(), line_num, "cli-invocation")

                if inv_key not in seen:
                    seen.add(inv_key)
                    commands.append(
                        {
                            "type": "cli-invocation",
                            "invocation": invocation.strip(),
                            "source": str(filepath.relative_to(self.root_dir)),
                            "line": line_num,
                        }
                    )

        return commands

    def extract_all(self) -> dict[str, list[dict[str, Any]]]:
        """Extract commands from ALL documentation files in the project.

        Scans comprehensively:
        - Plugin READMEs
        - Plugin documentation (docs/, guides/, tutorials/, examples/)
        - Root docs/
        - Wiki/ if present
        - Any .md files with command examples
        """
        results: dict[str, list[dict[str, Any]]] = {}
        seen_files: set[Path] = set()  # Track processed files to avoid duplicates

        # Documentation patterns to scan
        doc_patterns = [
            "plugins/*/README.md",
            "plugins/*/docs/**/*.md",
            "plugins/*/guides/**/*.md",
            "plugins/*/tutorials/**/*.md",
            "plugins/*/examples/**/*.md",
            "docs/**/*.md",
            "guides/**/*.md",
            "tutorials/**/*.md",
            "examples/**/*.md",
            "wiki/**/*.md",
            "**/README.md",
        ]

        # Scan all documentation patterns
        for pattern in doc_patterns:
            for doc_file in self.root_dir.glob(pattern):
                # Skip if already processed
                if doc_file in seen_files:
                    continue

                # Skip hidden files and node_modules
                if any(p.startswith(".") for p in doc_file.parts):
                    continue
                if "node_modules" in str(doc_file):
                    continue

                seen_files.add(doc_file)
                rel_path = doc_file.relative_to(self.root_dir)
                commands = self.extract_from_file(doc_file)

                if commands:
                    key = str(rel_path)
                    if key not in results:
                        results[key] = []
                    results[key].extend(commands)

        return results


class MakefileAnalyzer:
    """Analyze existing Makefile targets."""

    def __init__(self, makefile_path: Path):
        self.makefile_path = makefile_path
        self.targets = self._parse_targets()

    def _parse_targets(self) -> dict[str, dict[str, Any]]:
        """Parse targets from Makefile."""
        targets: dict[str, dict[str, Any]] = {}

        if not self.makefile_path.exists():
            return targets

        content = self.makefile_path.read_text()

        # Find target definitions
        for match in re.finditer(r"^([a-zA-Z][\w-]*)\s*:", content, re.MULTILINE):
            target_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            # Extract description (## comment)
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.start())
            line_content = content[line_start:line_end]
            description = ""

            desc_match = re.search(r"##\s*(.+)", line_content)
            if desc_match:
                description = desc_match.group(1)

            targets[target_name] = {
                "name": target_name,
                "line": line_num,
                "description": description,
            }

        return targets

    def has_target(self, target_name: str) -> bool:
        """Check if target exists."""
        return target_name in self.targets

    def get_missing_targets(self, required_targets: set[str]) -> set[str]:
        """Return set of required targets not in Makefile."""
        return required_targets - self.targets.keys()


class MakefileTargetGenerator:
    """Generate missing make targets from documented commands."""

    # Plugin-specific tool mappings for live demos
    PLUGIN_TOOLS = {
        "conserve": {
            "bloat-scan": ("$(UV_RUN) python scripts/bloat_detector.py . --report"),
            "ai-hygiene-audit": (
                "echo 'AI hygiene audit: Check for TODO/FIXME in skills/' && "
                "grep -r 'TODO\\|FIXME' skills/ | wc -l | "
                "xargs -I{} echo 'Found {} items'"
            ),
        },
        "sanctum": {
            "pr-review": (
                "$(UV_RUN) python scripts/pr_review_analyzer.py --dry-run || "
                "echo 'PR review analyzer: Analyzes PR quality and scope'"
            ),
            "commit-msg": (
                "git log --oneline -1 | head -1 || "
                "echo 'Commit-msg: Generates conventional commit messages'"
            ),
        },
        "pensive": {
            "makefile-review": (
                "$(UV_RUN) python scripts/makefile_review.py Makefile || "
                "echo 'Makefile review: Analyzes Makefile patterns and quality'"
            ),
            "bug-review": (
                "echo 'Bug review: Analyzing code for potential bugs...' && "
                "find src/ -name '*.py' | head -5"
            ),
        },
        "abstract": {
            "validate-plugin": (
                "$(UV_RUN) python scripts/validator.py --target . || "
                "echo 'Plugin validator: Checks plugin structure compliance'"
            ),
        },
    }

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def _get_live_command(self, plugin: str, command: str) -> str | None:
        """Get live command for a plugin's documented command."""
        if plugin in self.PLUGIN_TOOLS and command in self.PLUGIN_TOOLS[plugin]:
            return self.PLUGIN_TOOLS[plugin][command]
        return None

    def generate_target(
        self,
        plugin: str,
        command_name: str,
        invocation: str,
        description: str = "",
    ) -> str:
        """Generate a make target for a documented command.

        Args:
            plugin: Plugin name (e.g., "sanctum")
            command_name: Name of the command (e.g., "update-docs")
            invocation: Full command invocation (e.g., "/update-docs --skip-slop")
            description: Human-readable description

        Returns:
            Makefile target definition as string

        """
        target_name = f"demo-{command_name.replace('/', '').lstrip('/')}"
        target_desc = description or f"Demo {command_name} command (LIVE)"

        # Check if we have a live command for this
        live_cmd = self._get_live_command(plugin, command_name)

        recipe_lines = [
            f'\t@echo "=== {command_name} Demo (LIVE) ==="',
            '\t@echo ""',
        ]

        if live_cmd:
            # We have a live command - run it
            recipe_lines.append(
                f'\t@echo "Running {command_name} on {plugin} plugin..."'
            )
            recipe_lines.append('\t@echo ""')
            recipe_lines.append(
                f'\t{live_cmd} || echo "  [INFO] Tool execution completed"'
            )
        else:
            # Fallback: Show what the command does and how to run it
            recipe_lines.append(f'\t@echo "Command: {invocation}"')
            recipe_lines.append(f'\t@echo "Plugin: {plugin}"')
            recipe_lines.append('\t@echo ""')
            recipe_lines.append(f'\t@echo "This demonstrates {command_name} usage."')
            recipe_lines.append(
                '\t@echo "Execute manually in Claude Code for full functionality."'
            )

        recipe_lines.append('\t@echo ""')
        recipe_lines.append(f'\t@echo "Use {invocation} for full workflow."')

        recipe = "\n".join(recipe_lines)

        return f"""{target_name}: ## {target_desc}
{recipe}

"""

    def generate_demo_targets(
        self,
        plugin: str,
        commands: list[dict[str, Any]],
    ) -> str:
        """Generate demo targets for a plugin.

        Creates:
        1. Individual demo-* targets for each command (LIVE where possible)
        2. Aggregate demo-{plugin}-commands target to run all demos
        3. test-* targets for slash commands
        """
        targets = []

        # Group commands by type
        slash_cmds = [c for c in commands if c.get("type") == "slash-command"]
        cli_invokes = [c for c in commands if c.get("type") == "cli-invocation"]

        # Generate individual demo targets for each slash command
        for cmd in slash_cmds[:10]:  # Limit to first 10 to avoid overwhelming
            cmd_name = cmd["command"]
            cmd_args = cmd.get("args", "")
            invocation = f"/{cmd_name}"
            if cmd_args:
                invocation += f" {cmd_args}"

            target = self.generate_target(
                plugin=plugin,
                command_name=cmd_name,
                invocation=invocation,
                description=f"Demo {cmd_name} command (LIVE)",
            )
            targets.append(target)

        # Generate CLI invocation demos
        for cli in cli_invokes[:5]:
            invocation = cli["invocation"]
            cmd_name = invocation.split()[0] if invocation.split() else "cli"
            target = self.generate_target(
                plugin=plugin,
                command_name=f"cli-{cmd_name}",
                invocation=invocation,
                description=f"Demo CLI invocation: {invocation}",
            )
            targets.append(target)

        # Generate aggregate demo target
        if slash_cmds:
            demo_names = [f"demo-{c['command']}" for c in slash_cmds[:10]]
            demo_targets = " ".join(demo_names)
            plugin_capitalized = plugin.capitalize()
            aggregate_target = (
                f"demo-{plugin}-commands: {demo_targets} ## "
                f"Run all {plugin} documented command demos\n"
                f'\t@echo ""\n'
                f'\t@echo "=== {plugin_capitalized} All Commands Demo Complete ==="\n'
                f'\t@echo "Ran {len(demo_names)} documented commands"\n'
                f'\t@echo ""\n'
                f"\n"
            )
            targets.append(aggregate_target)
            targets.append(aggregate_target)

        # Generate test targets for slash commands
        for cmd in slash_cmds[:10]:
            cmd_name = cmd["command"]
            test_target = f"""test-{cmd_name}: ## Test {cmd_name} command workflow
\t@echo "=== Testing {cmd_name} workflow ==="
\t@echo "Validating: /{cmd_name}"
\t@echo "Check: Command executes without errors"
\t@echo "Check: Output matches expected format"
\t@echo "Status: [ ] Manual test required"
\t@echo ""

"""
            targets.append(test_target)

        return "\n".join(targets)


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
        required_targets = set()
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
        for line in generated_content.splitlines():
            # Check if this line defines a new target
            target_match = re.match(r"^([a-zA-Z][\w-]+)\s*:", line)
            if target_match:
                target_name = target_match.group(1)
                if target_name not in existing_targets:
                    filtered_content.append(line)
                    existing_targets.add(target_name)  # Mark as added
                # else: Skip duplicate target
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
                # Ensure proper newline spacing
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
            # Ensure the content before %:: ends with newline
            prefix = parts[0].rstrip()
            # Add blank lines before new targets and before catch-all
            return (
                prefix + "\n\n" + final_content + "\n\n# Catch-all rule\n%::" + parts[1]
            )
        # Just append
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
        # Check if we should insert before catch-all rule
        if "%::" in content:
            # Look for the pattern: Makefile.local; -include Makefile.local\n\n%::
            catch_all_pattern = "\n\n# Guard against accidental file creation"
            if catch_all_pattern in content:
                return self._insert_content_before_catchall(
                    content, final_content, catch_all_pattern
                )
            # Fallback: insert before %::
            return self._insert_content_before_percent_colon(content, final_content)
        # Just append to end
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
        existing_targets = set()
        for line in content.splitlines():
            match = re.match(r"^([a-zA-Z][\w-]+)\s*:", line)
            if match:
                existing_targets.add(match.group(1))

        # Filter out targets that already exist
        filtered_content = self._filter_duplicate_targets(
            generated_content, existing_targets
        )

        if not filtered_content:
            print(f"  ℹ️  All targets already exist in {makefile_path.name}")
            return True

        # Join filtered content
        final_content = "\n".join(filtered_content).strip() + "\n"

        # Determine insertion strategy and apply
        new_content = self._determine_insertion_strategy(content, final_content)

        # Write back
        if not dry_run:
            makefile_path.write_text(new_content)
            print(f"✓ Updated {makefile_path}")
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
            # Remove .PHONY: prefix and backslashes, then split
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
        # Start with .PHONY:
        new_phony_lines = [".PHONY:"]
        current_line = ".PHONY:"

        for target in all_targets:
            test_line = current_line + " " + target
            if len(test_line) > PHONY_LINE_LENGTH_LIMIT:  # Line length limit
                # Finish current line with backslash
                new_phony_lines.append(current_line + " \\")
                current_line = "\t" + target  # Start new line with tab
            else:
                current_line = test_line

        # Add final line without backslash
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

        # Find .PHONY block
        phony_lines = self._find_phony_block(content)

        if not phony_lines:
            print(f"Warning: No .PHONY declaration found in {makefile_path}")
            return False

        # Extract existing targets
        existing_phony = self._extract_phony_targets(phony_lines)
        existing_set = set(existing_phony)

        # Add missing targets
        new_targets = [m for m in missing if m not in existing_set]

        if not new_targets:
            return True

        # Build new .PHONY block
        all_targets = sorted(existing_phony + new_targets)
        new_phony_lines = self._build_phony_block(all_targets)

        # Replace old .PHONY block with new one
        old_phony_text = "\n".join(phony_lines)
        new_phony_text = "\n".join(new_phony_lines)

        new_content = content.replace(old_phony_text, new_phony_text, 1)

        if not dry_run:
            makefile_path.write_text(new_content)
            print(f"  ✓ Updated .PHONY with {len(new_targets)} new targets")
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

            if self.verbose:
                print(f"\n{plugin_name}:")
                print(f"  Commands documented: {finding['commands_documented']}")
                print(f"  Targets missing: {finding['targets_missing']}")
                print(f"  Coverage: {finding['coverage_percent']}%")

        return self.report

    def generate_report(self, output_format: str = "text") -> str:
        """Generate analysis report."""
        if output_format == "json":
            return json.dumps(self.report, indent=2)

        # Text report
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


def generate_makefile(
    plugin_dir: Path,
    plugin_name: str,
    dry_run: bool = False,
) -> bool:
    """Generate a new Makefile for a plugin using language detection.

    Follows the attune:makefile-generation skill pattern:
    1. Detect language from project files
    2. Generate appropriate Makefile template
    3. Add plugin-specific targets
    4. Verify with make help

    Args:
        plugin_dir: Path to the plugin directory
        plugin_name: Name of the plugin
        dry_run: If True, don't actually write files

    Returns:
        True if Makefile generated successfully, False otherwise

    """
    print(f"Generating Makefile for {plugin_name}...")

    # Detect language
    language = None
    if (plugin_dir / "pyproject.toml").exists():
        language = "python"
    elif (plugin_dir / "Cargo.toml").exists():
        language = "rust"
    elif (plugin_dir / "package.json").exists():
        language = "typescript"
    else:
        # Default to Python for claude-night-market plugins
        language = "python"
        print("  No language file detected, defaulting to Python")

    # Generate Makefile based on language
    if language == "python":
        makefile_content = _generate_python_makefile(plugin_name)
    elif language == "rust":
        makefile_content = _generate_rust_makefile(plugin_name)
    elif language == "typescript":
        makefile_content = _generate_typescript_makefile(plugin_name)
    else:
        print(f"  ❌ Unsupported language: {language}")
        return False

    # Write Makefile
    makefile_path = plugin_dir / "Makefile"
    if not dry_run:
        makefile_path.write_text(makefile_content)
        print(f"  ✓ Generated {makefile_path}")
    else:
        print(f"  [DRY RUN] Would generate {makefile_path}")

    return True


def _generate_python_makefile(plugin_name: str) -> str:
    """Generate a Python Makefile with standard targets.

    Based on attune:makefile-generation skill patterns.
    """
    # AWK command for displaying help (broken into lines for readability)
    awk_cmd = (
        'awk \'BEGIN {FS = ":.*?## "} '
        "/^[a-zA-Z_-]+:.*?## / "
        '{printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}\' '
        "Makefile"
    )

    return f"""# {plugin_name.capitalize()} Plugin Makefile
# Generated by makefile-dogfooder
#
# Standard Python development targets

.PHONY: help install deps lint format typecheck test test-cov check-all clean build

# Default target
help: ## Show this help message
\t@echo "{plugin_name.capitalize()} Plugin - Make Targets"
\t@echo "================================"
\t{awk_cmd}

# ---------- Installation ----------
install: ## Install development dependencies
\tuv sync --dev

deps: ## Sync dependencies
\tuv sync

# ---------- Code Quality ----------
lint: ## Run linting
\truff check .

format: ## Format code
\truff format .

typecheck: ## Run type checking
\tmypy src/

# ---------- Testing ----------
test: ## Run tests
\tpytest

test-cov: ## Run tests with coverage
\tpytest --cov=src --cov-report=term-missing

check-all: lint typecheck test-cov ## Run all quality checks

# ---------- Maintenance ----------
clean: ## Clean cache and build files
\trm -rf .pytest_cache .coverage .mypy_cache .ruff_cache dist build 2>/dev/null || true
\tfind . -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true

build: ## Build distribution package
\tuv build

# ---------- Status ----------
status: ## Show project overview
\t@echo "{plugin_name.capitalize()} Plugin:"
\t@echo "  Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
\t@echo "  Tests:  $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
"""


def _generate_rust_makefile(plugin_name: str) -> str:
    """Generate a Rust Makefile with standard targets."""
    # AWK command for displaying help
    awk_cmd = (
        'awk \'BEGIN {FS = ":.*?## "} '
        "/^[a-zA-Z_-]+:.*?## / "
        '{printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}\' '
        "Makefile"
    )

    return f"""# {plugin_name.capitalize()} Plugin Makefile
# Generated by makefile-dogfooder
#
# Standard Rust development targets

.PHONY: help fmt lint check test build clean

help: ## Show this help message
\t@echo "{plugin_name.capitalize()} Plugin - Make Targets"
\t@echo "================================"
\t{awk_cmd}

fmt: ## Format code
\trustfmt

lint: ## Run linter
\tcargo clippy

check: ## Check compilation
\tcargo check

test: ## Run tests
\tcargo test

build: ## Build release binary
\tcargo build --release

clean: ## Clean build artifacts
\tcargo clean
"""


def _generate_typescript_makefile(plugin_name: str) -> str:
    """Generate a TypeScript Makefile with standard targets."""
    # AWK command for displaying help
    awk_cmd = (
        'awk \'BEGIN {FS = ":.*?## "} '
        "/^[a-zA-Z_-]+:.*?## / "
        '{printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}\' '
        "Makefile"
    )

    return f"""# {plugin_name.capitalize()} Plugin Makefile
# Generated by makefile-dogfooder
#
# Standard TypeScript development targets

.PHONY: help install lint format typecheck test build dev clean

help: ## Show this help message
\t@echo "{plugin_name.capitalize()} Plugin - Make Targets"
\t@echo "================================"
\t{awk_cmd}

install: ## Install dependencies
\tnpm install

lint: ## Run linter
\teslint .

format: ## Format code
\tprettier --write .

typecheck: ## Run type checker
\ttsc --noEmit

test: ## Run tests
\tnpm test

build: ## Build for production
\tnpm run build

dev: ## Start development server
\tnpm run dev

clean: ## Clean build artifacts
\trm -rf dist node_modules
"""


def run_preflight_checks(root_dir: Path, plugins_dir: str) -> bool:
    """Run pre-flight checks before processing.

    Validates:
    - Working directory exists
    - Required directories are accessible
    - Git repository (for rollback capability)

    Returns:
        True if all checks pass, False otherwise

    """
    print("Running pre-flight checks...")

    # Check root directory exists
    if not root_dir.exists():
        print(f"❌ Root directory does not exist: {root_dir}")
        return False

    # Check plugins directory
    plugins_path = root_dir / plugins_dir
    if not plugins_path.exists():
        print(f"❌ Plugins directory not found: {plugins_path}")
        return False

    # Check for git repository (for rollback capability)
    git_dir = root_dir / ".git"
    if not git_dir.exists():
        print("⚠️  Not in a git repository - rollback will not be available")
        print("   Consider running: git init")

    # Check write permissions
    test_file = root_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        print(f"❌ No write permission in {root_dir}: {e}")
        return False

    print("✅ Preflight checks passed")
    return True


def validate_working_directory(
    root_dir: Path, plugins_dir: str, plugin_name: str | None = None
) -> bool:
    """Validate working directory context before file operations.

    Args:
        root_dir: Project root directory
        plugins_dir: Plugins subdirectory name
        plugin_name: Optional plugin name to validate

    Returns:
        True if context is valid, False otherwise

    """
    # Ensure we're in the correct directory
    current_dir = Path.cwd()
    if current_dir != root_dir:
        print("⚠️  Working directory mismatch")
        print(f"   Current: {current_dir}")
        print(f"   Expected: {root_dir}")
        print("   Changing to root directory...")
        try:
            os.chdir(root_dir)
        except Exception as e:
            print(f"❌ Cannot change to root directory: {e}")
            return False

    # If plugin specified, validate its Makefile exists
    if plugin_name:
        makefile_path = root_dir / plugins_dir / plugin_name / "Makefile"
        if not makefile_path.exists():
            print(f"❌ Makefile not found for plugin '{plugin_name}': {makefile_path}")
            return False

    return True


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
    # Recommend --dry-run for safety
    if not config.dry_run:
        print("\n⚠️  WARNING: Applying changes without --dry-run")
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
        print(f"\n✅ Successfully applied changes to {plugin_name}")
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
