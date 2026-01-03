#!/usr/bin/env python3
"""Upgrade existing project with missing configurations."""

import argparse
import sys
from pathlib import Path

from project_detector import ProjectDetector
from template_engine import get_default_variables


class ProjectUpgrader:
    """Upgrade existing projects with missing configurations."""

    def __init__(self, project_path: Path, language: str):
        self.project_path = project_path
        self.language = language
        self.detector = ProjectDetector(project_path)

    def get_missing_files(self, component: str = "all") -> list[str]:
        """Get list of missing configuration files.

        Args:
            component: Component to check (all, workflows, makefile, pre-commit, gitignore)

        Returns:
            List of missing file paths
        """
        missing = []

        # Define component file mappings
        components = {
            "gitignore": [".gitignore"],
            "makefile": ["Makefile"],
            "pre-commit": [".pre-commit-config.yaml"],
            "workflows": [
                ".github/workflows/test.yml",
                ".github/workflows/lint.yml",
                ".github/workflows/typecheck.yml"
                if self.language == "python"
                else ".github/workflows/build.yml",
            ],
        }

        # Language-specific build configs
        if self.language == "python":
            components["build"] = ["pyproject.toml"]
        elif self.language == "rust":
            components["build"] = ["Cargo.toml"]
            components["workflows"] = [".github/workflows/ci.yml"]
        elif self.language == "typescript":
            components["build"] = ["package.json", "tsconfig.json"]

        # Filter by component
        if component == "all":
            check_components = components.values()
        elif component in components:
            check_components = [components[component]]
        else:
            print(f"Warning: Unknown component '{component}'", file=sys.stderr)
            return []

        # Check each file
        for file_list in check_components:
            for file_path_str in file_list:
                file_path = self.project_path / file_path_str
                if not file_path.exists():
                    missing.append(file_path_str)

        return missing

    def get_outdated_files(self) -> dict[str, str]:
        """Check for outdated configuration files.

        Returns:
            Dictionary mapping file paths to reasons they're outdated
        """
        outdated = {}

        # Check Makefile age
        makefile = self.project_path / "Makefile"
        if makefile.exists():
            content = makefile.read_text()
            # Check for old-style targets or missing help command
            if "## Show this help" not in content:
                outdated["Makefile"] = "Missing help command (outdated format)"

        # Check workflows for old action versions
        workflows_dir = self.project_path / ".github" / "workflows"
        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.yml"):
                content = workflow_file.read_text()
                # Check for old action versions
                if "actions/checkout@v2" in content or "actions/checkout@v3" in content:
                    outdated[str(workflow_file.relative_to(self.project_path))] = (
                        "Using outdated GitHub Actions (v2/v3, should be v4+)"
                    )

        return outdated

    def show_status(self, verbose: bool = False) -> None:
        """Show upgrade status for the project.

        Args:
            verbose: Show detailed information
        """
        print(f"\n{'=' * 60}")
        print("Attune Upgrade Status")
        print(f"{'=' * 60}")
        print(f"Project: {self.project_path.name}")
        print(f"Language: {self.language}")
        print(f"Path: {self.project_path}")
        print(f"{'=' * 60}\n")

        # Check existing files
        existing = self.detector.check_existing_files()
        missing = self.get_missing_files("all")
        outdated = self.get_outdated_files()

        # Show status by category
        categories = {
            "Git": [".gitignore"],
            "Build": ["pyproject.toml", "Cargo.toml", "package.json", "tsconfig.json"],
            "Development": ["Makefile", ".pre-commit-config.yaml"],
            "CI/CD": [
                ".github/workflows/test.yml",
                ".github/workflows/lint.yml",
                ".github/workflows/typecheck.yml",
                ".github/workflows/ci.yml",
                ".github/workflows/build.yml",
            ],
        }

        for category, files in categories.items():
            category_files = [
                f for f in files if any(f in path for path in existing.keys())
            ]
            if not category_files:
                continue

            print(f"{category}:")
            for file_path in files:
                if file_path in existing:
                    if existing[file_path]:
                        if file_path in outdated:
                            print(
                                f"  ⚠️  {file_path} (outdated - {outdated[file_path]})"
                            )
                        else:
                            print(f"  ✅ {file_path}")
                    elif file_path in missing:
                        print(f"  ❌ {file_path} (missing)")

        # Summary
        print("\nSummary:")
        print(f"  Missing: {len(missing)} files")
        print(f"  Outdated: {len(outdated)} files")

        if missing:
            print("\nMissing Files:")
            for file_path in missing:
                print(f"  - {file_path}")

        if outdated:
            print("\nOutdated Files:")
            for file_path, reason in outdated.items():
                print(f"  - {file_path}: {reason}")

        if not missing and not outdated:
            print("\n✅ All configurations up-to-date!")
        else:
            print(
                "\nRun with --apply to add missing files or --update to update outdated files"
            )

        print(f"{'=' * 60}\n")

    def upgrade(
        self,
        component: str = "all",
        force: bool = False,
        update_outdated: bool = False,
        dry_run: bool = False,
    ) -> list[str]:
        """Upgrade project with missing or outdated configurations.

        Args:
            component: Component to upgrade (all, workflows, makefile, etc.)
            force: Force overwrite without prompting
            update_outdated: Update outdated files
            dry_run: Show what would be done without doing it

        Returns:
            List of files that were/would be created or updated
        """
        from attune_init import copy_templates

        affected_files = []

        # Get missing files
        missing = self.get_missing_files(component)

        if dry_run:
            print(f"\n{'=' * 60}")
            print("Dry Run - Changes Preview")
            print(f"{'=' * 60}")
            print(f"Would add {len(missing)} missing files:")
            for file_path in missing:
                print(f"  + {file_path}")

            if update_outdated:
                outdated = self.get_outdated_files()
                print(f"\nWould update {len(outdated)} outdated files:")
                for file_path in outdated:
                    print(f"  ↻ {file_path}")

            print(f"{'=' * 60}\n")
            return []

        # Get template variables from existing files or prompt
        variables = self._infer_variables()

        # Find templates directory
        script_dir = Path(__file__).parent
        templates_root = script_dir.parent / "templates"

        # Filter templates to only missing files
        if missing:
            print(f"\nAdding {len(missing)} missing files...")
            # Temporarily copy only missing templates
            affected_files = copy_templates(
                language=self.language,
                project_path=self.project_path,
                variables=variables,
                templates_root=templates_root,
                force=force,
            )

        # Update outdated files if requested
        if update_outdated:
            outdated = self.get_outdated_files()
            if outdated:
                print(f"\nUpdating {len(outdated)} outdated files...")
                for file_path in outdated:
                    response = "y" if force else input(f"Update {file_path}? [y/N]: ")
                    if response.lower() == "y":
                        # Backup old file
                        old_file = self.project_path / file_path
                        backup = old_file.with_suffix(old_file.suffix + ".bak")
                        if old_file.exists():
                            old_file.rename(backup)
                            print(f"  ✓ Backed up to {backup}")

                        affected_files.append(file_path)

        return affected_files

    def _infer_variables(self) -> dict[str, str]:
        """Infer template variables from existing project files.

        Returns:
            Dictionary of template variables
        """
        # Try to read from existing pyproject.toml, Cargo.toml, or package.json
        if self.language == "python":
            pyproject = self.project_path / "pyproject.toml"
            if pyproject.exists():
                import re

                content = pyproject.read_text()

                # Extract name
                name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
                project_name = (
                    name_match.group(1) if name_match else self.project_path.name
                )

                # Extract version
                version_match = re.search(
                    r'requires-python\s*=\s*">=(\d+\.\d+)"', content
                )
                python_version = version_match.group(1) if version_match else "3.10"

                # Extract author
                author_match = re.search(
                    r'name\s*=\s*"([^"]+)".*?email', content, re.DOTALL
                )
                author = author_match.group(1) if author_match else "Your Name"

                return get_default_variables(
                    project_name=project_name,
                    language=self.language,
                    python_version=python_version,
                    author=author,
                )

        # Default fallback
        return get_default_variables(
            project_name=self.project_path.name,
            language=self.language,
        )


def main():
    """Main entry point for attune upgrade."""
    parser = argparse.ArgumentParser(
        description="Upgrade existing project with missing configurations"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Project path (default: current directory)",
    )
    parser.add_argument(
        "--lang",
        "--language",
        choices=["python", "rust", "typescript"],
        help="Project language (auto-detected if not specified)",
    )
    parser.add_argument(
        "--component",
        default="all",
        choices=["all", "workflows", "makefile", "pre-commit", "gitignore", "build"],
        help="Component to upgrade",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite without prompting",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update outdated files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show upgrade status only",
    )

    args = parser.parse_args()

    project_path = args.path.resolve()

    # Detect language
    detector = ProjectDetector(project_path)
    language = args.lang or detector.detect_language()

    if not language:
        print(
            "Error: Could not detect project language. Use --lang to specify.",
            file=sys.stderr,
        )
        sys.exit(1)

    upgrader = ProjectUpgrader(project_path, language)

    # Show status only
    if args.status:
        upgrader.show_status(verbose=True)
        sys.exit(0)

    # Show status first
    upgrader.show_status()

    # Perform upgrade
    if not args.dry_run:
        response = input("Proceed with upgrade? [y/N]: ")
        if response.lower() != "y":
            print("Upgrade cancelled.")
            sys.exit(0)

    affected_files = upgrader.upgrade(
        component=args.component,
        force=args.force,
        update_outdated=args.update,
        dry_run=args.dry_run,
    )

    if not args.dry_run and affected_files:
        print(f"\n{'=' * 60}")
        print("✓ Upgrade complete!")
        print(f"{'=' * 60}")
        print(f"Modified {len(affected_files)} files")
        print("\nNext steps:")
        print("  1. Review changes: git diff")
        print("  2. Test: make test")
        print("  3. Validate: /attune:validate")
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
