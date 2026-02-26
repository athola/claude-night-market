#!/usr/bin/env python3
"""Template loading with custom location support."""

from __future__ import annotations

import os
from pathlib import Path


class TemplateLoader:
    """Load templates with support for custom locations."""

    def __init__(self, language: str):
        """Initialize template loader.

        Args:
            language: Target language (python, rust, typescript)

        """
        self.language = language
        self.search_paths = self._get_search_paths()

    def _get_search_paths(self) -> list[Path]:
        """Get template search paths in priority order.

        Returns:
            List of paths to search for templates

        """
        paths = []

        # 1. User custom templates (highest priority)
        home = Path.home()
        user_templates = home / ".claude" / "attune" / "templates" / self.language
        if user_templates.exists():
            paths.append(user_templates)

        # 2. Project-local templates
        project_templates = Path.cwd() / ".attune" / "templates" / self.language
        if project_templates.exists():
            paths.append(project_templates)

        # 3. Environment variable override
        custom_path = os.environ.get("ATTUNE_TEMPLATES_PATH")
        if custom_path:
            custom = Path(custom_path) / self.language
            if custom.exists():
                paths.append(custom)

        # 4. Default plugin templates (lowest priority)
        script_dir = Path(__file__).parent
        default_templates = script_dir.parent / "templates" / self.language
        if default_templates.exists():
            paths.append(default_templates)

        return paths

    def find_template(self, template_name: str) -> Path | None:
        """Find template file in search paths.

        Args:
            template_name: Name of template file (e.g., "Makefile.template")

        Returns:
            Path to template file, or None if not found

        """
        for search_path in self.search_paths:
            template_path = search_path / template_name
            if template_path.exists():
                return template_path

        return None

    def get_all_templates(self) -> list[Path]:
        """Get all template files from search paths.

        Templates from higher-priority paths override lower-priority ones.

        Returns:
            List of template file paths

        """
        seen_names = set()
        templates = []

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            # Find all .template files
            for template_path in search_path.rglob("*.template"):
                # Get relative name
                rel_name = template_path.relative_to(search_path)

                # Only include if not already seen (higher priority wins)
                if str(rel_name) not in seen_names:
                    seen_names.add(str(rel_name))
                    templates.append(template_path)

        return templates

    def show_template_sources(self) -> None:
        """Show where templates are being loaded from."""
        print("\nTemplate Search Paths:")
        for i, path in enumerate(self.search_paths, 1):
            exists = "✓" if path.exists() else "✗"
            template_count = len(list(path.rglob("*.template"))) if path.exists() else 0
            print(f"  {i}. {exists} {path} ({template_count} templates)")

        print("\nTemplate Resolution:")
        all_templates = self.get_all_templates()
        for template in sorted(all_templates):
            # Find which search path it came from
            for search_path in self.search_paths:
                try:
                    rel_path = template.relative_to(search_path)
                    source = (
                        "custom"
                        if "claude" in str(search_path) or ".attune" in str(search_path)
                        else "default"
                    )
                    print(f"  {rel_path} ({source}: {search_path.name})")
                    break
                except ValueError:
                    continue


def create_custom_template_dir(
    language: str = "python", location: str = "user"
) -> Path:
    """Create custom template directory structure.

    Args:
        language: Language for templates
        location: Where to create templates ("user" or "project")

    Returns:
        Path to created template directory

    """
    if location == "user":
        base_path = Path.home() / ".claude" / "attune" / "templates"
    else:
        base_path = Path.cwd() / ".attune" / "templates"

    template_dir = base_path / language
    template_dir.mkdir(parents=True, exist_ok=True)

    # Create workflows subdirectory
    workflows_dir = template_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)

    print(f"✓ Created custom template directory: {template_dir}")
    print("\nTo customize templates:")
    print("  1. Copy templates from plugin to this directory")
    print("  2. Edit templates as needed")
    print("  3. Templates here will override plugin defaults")

    return template_dir


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: template_loader.py <language> [--create-custom]")
        sys.exit(1)

    language = sys.argv[1]

    if "--create-custom" in sys.argv:
        create_custom_template_dir(language)
    else:
        loader = TemplateLoader(language)
        loader.show_template_sources()
