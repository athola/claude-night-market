#!/usr/bin/env python3
"""Validate the abstract plugin for meta-skills infrastructure.

Use centralized utilities from abstract.base, abstract.frontmatter and abstract.utils.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import TypedDict

# Set up imports before using abstract package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.frontmatter import FrontmatterProcessor
from abstract.utils import (
    extract_dependencies,
    find_skill_files,
    parse_yaml_frontmatter,
)


class AbstractValidationResult(TypedDict):
    """Represent the result of an abstract plugin validation."""

    skills_found: set[str]
    skills_with_patterns: set[str]
    infrastructure_provided: set[str]
    issues: list[str]


class AbstractValidator:
    """Validate the abstract plugin for meta-skills and infrastructure."""

    def __init__(self, plugin_root: Path) -> None:
        """Initialize the abstract validator.

        Args:
            plugin_root: The root directory of the abstract plugin.

        """
        self.plugin_root = plugin_root
        self.skill_files = find_skill_files(plugin_root)
        self.plugin_config = plugin_root / "plugin.json"

    def scan_infrastructure(self) -> AbstractValidationResult:
        """Scan for infrastructure patterns and meta-skills."""
        skills_found: set[str] = set()
        skills_with_patterns: set[str] = set()
        infrastructure_provided: set[str] = set()
        issues: list[str] = []

        # Load the plugin configuration.
        if self.plugin_config.exists():
            try:
                config = json.loads(self.plugin_config.read_text())
                if "provides" in config:
                    provides = config["provides"]
                    if isinstance(provides, dict):
                        for items in provides.values():
                            if isinstance(items, list):
                                infrastructure_provided.update(items)
            except json.JSONDecodeError:
                issues.append("Invalid plugin.json")

        # Scan the skills for infrastructure patterns.
        for skill_file in self.skill_files:
            skill_name = skill_file.parent.name
            skills_found.add(skill_name)

            content = skill_file.read_text()

            # Check for meta-skill patterns.
            meta_patterns = [
                r"meta-skill",
                r"pattern:",
                r"infrastructure",
                r"framework",
                r"template",
                r"orchestrat",
            ]

            for pattern in meta_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    skills_with_patterns.add(skill_name)
                    break

        return AbstractValidationResult(
            skills_found=skills_found,
            skills_with_patterns=skills_with_patterns,
            infrastructure_provided=infrastructure_provided,
            issues=issues,
        )

    def validate_patterns(self) -> list[str]:
        """Validate that the skills follow the meta-skill patterns."""
        issues: list[str] = []

        # Check if the skills have a proper meta-skill structure.
        for skill_file in self.skill_files:
            content = skill_file.read_text()
            skill_name = skill_file.parent.name

            # Use centralized FrontmatterProcessor for parsing
            required_fields = ["name", "description", "category"]
            result = FrontmatterProcessor.parse(content, required_fields)

            if not result.is_valid:
                if result.parse_error and "Missing frontmatter" in result.parse_error:
                    issues.append(f"{skill_name}: Missing frontmatter")
                    continue
                if result.parse_error and "Incomplete" in result.parse_error:
                    issues.append(f"{skill_name}: Incomplete frontmatter")
                    continue

            # Report missing required fields
            for field in result.missing_fields:
                issues.append(f"{skill_name}: Missing required field '{field}'")

            # Check for meta-skill-specific indicators.
            meta_indicators = ["pattern", "template", "framework", "meta"]
            has_meta_indicator = any(
                indicator in content.lower() for indicator in meta_indicators
            )

            if not has_meta_indicator and skill_name not in ["skills-eval"]:
                issues.append(f"{skill_name}: Should have meta-skill indicators")

            # Check progressive disclosure
            prog_disc_issues = self._check_progressive_disclosure(content, skill_name)
            issues.extend(prog_disc_issues)

        # Check for dependency cycles
        cycle_issues = self._check_dependency_cycles()
        issues.extend(cycle_issues)

        # Check hub-and-spoke patterns
        hub_issues = self._check_hub_spoke_pattern()
        issues.extend(hub_issues)

        return issues

    def _check_progressive_disclosure(self, content: str, skill_name: str) -> list[str]:
        """Check if skill follows progressive disclosure pattern.

        Args:
            content: Full skill content.
            skill_name: Name of the skill.

        Returns:
            List of issues found.

        """
        issues = []

        # Check for essential sections in order
        has_overview = "## Overview" in content or "## What It Is" in content
        has_quick_start = "## Quick Start" in content
        has_detailed = "## Detailed Resources" in content or "## Resources" in content

        if not has_overview:
            issues.append(
                f"{skill_name}: Missing overview section for progressive disclosure",
            )

        # Check that Quick Start comes before Detailed Resources
        if has_quick_start and has_detailed:
            quick_pos = content.find("## Quick Start")
            detailed_pos = content.find("## Detailed Resources") or content.find(
                "## Resources",
            )
            if detailed_pos and quick_pos > detailed_pos:
                issues.append(
                    f"{skill_name}: Quick Start should come before Detailed Resources",
                )

        return issues

    def _check_dependency_cycles(self) -> list[str]:
        """Check for circular dependencies in skills.

        Returns:
            List of cycle issues found.

        """
        issues = []

        # Build dependency graph
        dep_graph: dict[str, list[str]] = {}

        for skill_file in self.skill_files:
            skill_name = skill_file.parent.name
            frontmatter = parse_yaml_frontmatter(skill_file.read_text())
            dependencies = extract_dependencies(frontmatter)
            dep_graph[skill_name] = dependencies

        # Detect cycles using DFS
        def has_cycle(node: str, visited: set[str], rec_stack: set[str]) -> list[str]:
            """Detect cycles in dependency graph using DFS."""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    cycle = has_cycle(neighbor, visited, rec_stack)
                    if cycle:
                        return [node, *cycle]
                elif neighbor in rec_stack:
                    return [node, neighbor]

            rec_stack.remove(node)
            return []

        visited: set[str] = set()
        for skill_name in dep_graph:
            if skill_name not in visited:
                cycle = has_cycle(skill_name, visited, set())
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    issues.append(f"Dependency cycle detected: {cycle_str}")

        return issues

    def _check_hub_spoke_pattern(self) -> list[str]:
        """Check if modular skills follow hub-and-spoke pattern.

        Returns:
            List of pattern violations.

        """
        issues = []

        # Find all skills with modules/ subdirectories
        modular_skills = []
        for skill_file in self.skill_files:
            skill_dir = skill_file.parent
            modules_dir = skill_dir / "modules"
            if modules_dir.exists():
                modular_skills.append((skill_file, modules_dir))

        for skill_file, modules_dir in modular_skills:
            skill_name = skill_file.parent.name
            module_files = list(modules_dir.glob("*.md"))

            if not module_files:
                issues.append(
                    f"{skill_name}: Has modules/ directory but no module files",
                )
                continue

            # Check that main SKILL.md references modules
            main_content = skill_file.read_text()
            referenced_modules = set()

            for module_file in module_files:
                module_name = module_file.stem
                if (
                    module_name in main_content
                    or f"modules/{module_name}" in main_content
                ):
                    referenced_modules.add(module_name)

            unreferenced = len(module_files) - len(referenced_modules)
            if unreferenced > 0:
                issues.append(
                    f"{skill_name}: {unreferenced} module(s) not referenced in "
                    f"main SKILL.md (hub-spoke violation)",
                )

            # Check that modules don't cross-reference each other (spoke-to-spoke)
            for module_file in module_files:
                module_content = module_file.read_text()
                current_module = module_file.stem

                for other_module in module_files:
                    if other_module.stem != current_module:
                        # Check for actual module reference patterns,
                        # not just word occurrences
                        module_ref_patterns = [
                            rf"modules/{other_module.stem}\b",  # modules/integration
                            rf"@include\s+{other_module.stem}\b",  # include integration
                            rf"\[{other_module.stem}\]",  # [integration]
                            rf"\[{other_module.stem}\]\(.*modules/{other_module.stem}.*\)",
                            rf"\b{other_module.stem}\.md\b",  # integration.md
                        ]

                        # Only flag if actual module reference patterns are found
                        if any(
                            re.search(pattern, module_content, re.IGNORECASE)
                            for pattern in module_ref_patterns
                        ):
                            issues.append(
                                f"{skill_name}/{current_module}.md: "
                                f"References another module ({other_module.stem}), "
                                f"violating hub-spoke pattern",
                            )

        return issues

    def generate_report(self) -> str:
        """Generate a detailed validation report."""
        result = self.scan_infrastructure()
        issues = self.validate_patterns()

        report = ["Abstract Plugin Infrastructure Report", "=" * 50]
        report.append(f"\nPlugin Root: {self.plugin_root}")
        report.append(f"Skill Files: {len(self.skill_files)}")

        report.append(
            f"\nInfrastructure Provided: {sorted(result['infrastructure_provided'])}",
        )
        report.append(f"Skills with Patterns: {sorted(result['skills_with_patterns'])}")

        if issues:
            report.append(f"\nIssues Found ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                report.append(f"  {i}. {issue}")
        else:
            report.append("\nAll meta-skill patterns validated successfully!")

        return "\n".join(report)

    def fix_patterns(self, dry_run: bool = True) -> list[str]:
        """Fix common meta-skill issues.

        Args:
            dry_run: If True, report what would be fixed without making changes.

        Returns:
            A list of fixes that were applied.

        """
        fixes_applied: list[str] = []

        # First, validate to find issues
        issues = self.validate_patterns()

        if not issues:
            return ["No fixes needed"]

        for skill_file in self.skill_files:
            skill_name = skill_file.parent.name
            content = skill_file.read_text()

            # Fix missing frontmatter - use centralized check
            if not FrontmatterProcessor.has_frontmatter(content):
                fix = self._fix_missing_frontmatter(
                    skill_file,
                    skill_name,
                    content,
                    dry_run,
                )
                if fix:
                    fixes_applied.append(fix)
                continue

            # Fix missing required fields in frontmatter
            fix = self._fix_frontmatter_fields(skill_file, skill_name, content, dry_run)
            if fix:
                fixes_applied.append(fix)

        return fixes_applied if fixes_applied else ["No fixes needed"]

    def _fix_missing_frontmatter(
        self,
        skill_file: Path,
        skill_name: str,
        content: str,
        dry_run: bool,
    ) -> str:
        """Fix missing frontmatter by adding basic structure."""
        frontmatter = f"""---
name: {skill_name}
description: Meta-skill for abstract infrastructure
category: infrastructure
---

"""

        fixed_content = frontmatter + content
        if not dry_run:
            skill_file.write_text(fixed_content)
        return f"Fixed missing frontmatter in {skill_name}"

    def _fix_frontmatter_fields(
        self,
        skill_file: Path,
        skill_name: str,
        content: str,
        dry_run: bool,
    ) -> str:
        """Fix missing required fields in existing frontmatter."""
        # Use centralized FrontmatterProcessor for extraction
        raw_frontmatter, body = FrontmatterProcessor.extract_raw(content)
        if not raw_frontmatter:
            return ""

        # Parse to check existing fields
        result = FrontmatterProcessor.parse(content, required_fields=[])
        parsed = result.parsed

        needs_field_fix = False
        updates: list[str] = []

        # Add missing fields
        if "name" not in parsed:
            updates.append(f"name: {skill_name}")
            needs_field_fix = True

        if "description" not in parsed:
            updates.append("description: Meta-skill for abstract infrastructure")
            needs_field_fix = True

        if "category" not in parsed:
            updates.append("category: infrastructure")
            needs_field_fix = True

        # Add meta-skill indicator if missing
        if self._needs_meta_indicator(content, skill_name):
            updates.append("pattern: meta-skill")
            needs_field_fix = True

        if needs_field_fix:
            if not dry_run:
                # Insert new fields before closing ---
                # raw_frontmatter includes ---\n...\n---
                lines = raw_frontmatter.strip().split("\n")
                # Remove closing ---
                if lines[-1] == "---":
                    lines = lines[:-1]
                # Add updates
                lines.extend(updates)
                # Re-add closing ---
                lines.append("---")
                new_frontmatter = "\n".join(lines)
                skill_file.write_text(new_frontmatter + "\n" + body)
            return f"Added missing fields to frontmatter in {skill_name}"

        return ""

    def _needs_meta_indicator(self, content: str, skill_name: str) -> bool:
        """Check if meta-skill indicator is needed."""
        meta_indicators = ["pattern", "template", "framework", "meta"]
        has_meta_indicator = any(
            indicator in content.lower() for indicator in meta_indicators
        )
        return not has_meta_indicator and skill_name not in ["skills-eval"]


def main() -> None:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Validate the abstract plugin infrastructure.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="The root directory of the abstract plugin (default: current directory).",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for infrastructure patterns.",
    )
    parser.add_argument("--report", action="store_true", help="Generate a full report.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix common meta-skill issues.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="A dry run for fix operations.",
    )

    args = parser.parse_args()

    root_path = Path(args.root) if args.root else Path.cwd()
    validator = AbstractValidator(root_path)

    if args.report:
        pass
    elif args.scan:
        issues = validator.validate_patterns()
        if issues:
            for _issue in issues:
                pass
        else:
            pass
    elif args.fix:
        fixes = validator.fix_patterns(dry_run=args.dry_run)
        for _fix in fixes:
            pass
    else:
        pass


if __name__ == "__main__":
    main()
