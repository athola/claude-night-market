#!/usr/bin/env python3
"""Synchronize templates from reference projects."""

import argparse
from pathlib import Path
from typing import Any


class TemplateSynchronizer:
    """Synchronize templates from reference projects."""

    def __init__(self, plugin_root: Path):
        self.plugin_root = plugin_root
        self.templates_dir = plugin_root / "templates"

        # Reference projects and their file mappings
        self.references: dict[str, dict[str, Any]] = {
            "python": {
                "project": Path.home() / "simple-resume",
                "files": {
                    ".gitignore": ".gitignore.template",
                    "pyproject.toml": "pyproject.toml.template",
                    "Makefile": "Makefile.template",
                    ".pre-commit-config.yaml": ".pre-commit-config.yaml.template",
                    ".github/workflows/test.yml": "workflows/test.yml.template",
                    ".github/workflows/lint.yml": "workflows/lint.yml.template",
                    ".github/workflows/typecheck.yml": "workflows/typecheck.yml.template",
                },
            },
            "rust": {
                "project": Path.home() / "skrills",
                "files": {
                    ".gitignore": ".gitignore.template",
                    "Cargo.toml": "Cargo.toml.template",
                    "Makefile": "Makefile.template",
                    ".github/workflows/ci.yml": "workflows/ci.yml.template",
                },
            },
        }

    def check_reference_projects(self) -> dict[str, bool]:
        """Check which reference projects are available.

        Returns:
            Dictionary mapping language to availability

        """
        available = {}
        for lang, config in self.references.items():
            project_path = config["project"]
            available[lang] = project_path.exists()

        return available

    def extract_template_variables(self, content: str, language: str) -> str:
        """Convert concrete values to template variables.

        Args:
            content: File content
            language: Programming language

        Returns:
            Content with template variables

        """
        if language == "python":
            # Replace specific project name with template variable
            import re

            # Common project-specific replacements
            replacements = [
                (r'name = "simple-resume"', 'name = "{{PROJECT_NAME}}"'),
                (r'name = "simple_resume"', 'name = "{{PROJECT_MODULE}}"'),
                (r'description = "[^"]+"', 'description = "{{PROJECT_DESCRIPTION}}"'),
                (
                    r'authors = \[\{name = "[^"]+", email = "[^"]+"\}\]',
                    'authors = [\\n    {name = "{{AUTHOR}}", email = "{{EMAIL}}"}\\n]',
                ),
                (
                    r'requires-python = ">=\d+\.\d+"',
                    'requires-python = ">={{PYTHON_VERSION}}"',
                ),
                (
                    r"python-version: \'\d+\.\d+\'",
                    "python-version: '{{PYTHON_VERSION}}'",
                ),
                (r"python_version: \d+", "python_version: {{PYTHON_VERSION_SHORT}}"),
            ]

            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)

        elif language == "rust":
            import re

            replacements = [
                (r'name = "[\w-]+"', 'name = "{{PROJECT_NAME}}"'),
                (r'edition = "\d+"', 'edition = "{{RUST_EDITION}}"'),
                (r'authors = \["[^"]+"\]', 'authors = ["{{AUTHOR}} <{{EMAIL}}>"]'),
                (r'description = "[^"]+"', 'description = "{{PROJECT_DESCRIPTION}}"'),
            ]

            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)

        return content

    def sync_language_templates(
        self, language: str, dry_run: bool = False, force: bool = False
    ) -> list[str]:
        """Synchronize templates for a specific language.

        Args:
            language: Language to sync (python, rust)
            dry_run: Show what would be done without doing it
            force: Overwrite existing templates without prompting

        Returns:
            List of synced file paths

        """
        if language not in self.references:
            print(f"Error: No reference project configured for {language}")
            return []

        config = self.references[language]
        project_path = config["project"]

        if not project_path.exists():
            print(f"Error: Reference project not found: {project_path}")
            print("  Clone it first or update the path in sync_templates.py")
            return []

        synced_files = []
        lang_templates_dir = self.templates_dir / language
        lang_templates_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nSyncing {language} templates from {project_path}...")

        for source_file, template_file in config["files"].items():
            source_path = project_path / source_file
            template_path = lang_templates_dir / template_file

            if not source_path.exists():
                print(f"  ⊘ {source_file} (not found in reference project)")
                continue

            # Read source content
            content = source_path.read_text()

            # Extract template variables
            template_content = self.extract_template_variables(content, language)

            if dry_run:
                print(f"  → Would sync: {source_file} -> {template_file}")
                continue

            # Check if template already exists
            if template_path.exists() and not force:
                response = input(
                    f"  Template exists: {template_file}. Overwrite? [y/N]: "
                )
                if response.lower() != "y":
                    print(f"  ⊘ Skipped: {template_file}")
                    continue

            # Create parent directory
            template_path.parent.mkdir(parents=True, exist_ok=True)

            # Write template
            template_path.write_text(template_content)
            print(f"  ✓ Synced: {template_file}")
            synced_files.append(str(template_path))

        return synced_files

    def sync_all(
        self, dry_run: bool = False, force: bool = False
    ) -> dict[str, list[str]]:
        """Synchronize all language templates.

        Args:
            dry_run: Show what would be done without doing it
            force: Overwrite existing templates without prompting

        Returns:
            Dictionary mapping languages to synced file lists

        """
        available = self.check_reference_projects()
        synced = {}

        for language, is_available in available.items():
            if is_available:
                synced[language] = self.sync_language_templates(
                    language, dry_run, force
                )
            else:
                print(f"\n⊘ Skipping {language}: Reference project not found")

        return synced

    def show_status(self) -> None:
        """Show template synchronization status."""
        print("\n" + "=" * 60)
        print("Template Synchronization Status")
        print("=" * 60)

        available = self.check_reference_projects()

        for language, config in self.references.items():
            project_path = config["project"]
            is_available = available[language]
            status = "✓" if is_available else "✗"

            print(f"\n{language.title()}:")
            print(f"  {status} Reference: {project_path}")

            if is_available:
                # Check template freshness
                lang_templates_dir = self.templates_dir / language

                for source_file, template_file in config["files"].items():
                    template_path = lang_templates_dir / template_file
                    source_path = project_path / source_file

                    if template_path.exists() and source_path.exists():
                        # Compare modification times
                        template_mtime = template_path.stat().st_mtime
                        source_mtime = source_path.stat().st_mtime

                        if source_mtime > template_mtime:
                            print(f"    ⚠️  {template_file} (outdated)")
                        else:
                            print(f"    ✓  {template_file} (up-to-date)")
                    elif not template_path.exists():
                        print(f"    ✗  {template_file} (not synced)")

        print("=" * 60 + "\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Synchronize templates from reference projects"
    )
    parser.add_argument(
        "--language",
        "-l",
        choices=["python", "rust", "all"],
        default="all",
        help="Language to sync (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwrite without prompting",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show synchronization status only",
    )

    args = parser.parse_args()

    # Find plugin root
    script_dir = Path(__file__).parent
    plugin_root = script_dir.parent

    syncer = TemplateSynchronizer(plugin_root)

    if args.status:
        syncer.show_status()
        return

    # Sync templates
    if args.language == "all":
        result = syncer.sync_all(dry_run=args.dry_run, force=args.force)
        if not args.dry_run:
            total_synced = sum(len(files) for files in result.values())
            print(f"\n✓ Synced {total_synced} templates across {len(result)} languages")
    else:
        synced = syncer.sync_language_templates(
            args.language, dry_run=args.dry_run, force=args.force
        )
        if not args.dry_run:
            print(f"\n✓ Synced {len(synced)} {args.language} templates")


if __name__ == "__main__":
    main()
