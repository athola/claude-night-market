#!/usr/bin/env python3
"""Customize project templates (REFACTORED with YAML templates)."""

import argparse
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Load templates from YAML
DATA_DIR = Path(__file__).parent.parent / "data"
TEMPLATES_FILE = DATA_DIR / "architecture_templates.yaml"


def load_templates() -> dict[str, dict[str, Any]]:
    """Load architecture templates from YAML file.

    Returns:
        Dictionary mapping paradigm names to template configurations

    """
    if not TEMPLATES_FILE.exists():
        raise FileNotFoundError(
            f"Templates file not found: {TEMPLATES_FILE}\n"
            "Verify architecture_templates.yaml exists"
        )

    with open(TEMPLATES_FILE) as f:
        data: dict[str, Any] = yaml.safe_load(f)
        templates: dict[str, dict[str, Any]] = data["templates"]
        return templates


class TemplateCustomizer:
    """Customize project templates for specific architecture paradigms."""

    def __init__(self, paradigm: str, module: str, language: str = "python"):
        """Initialize template customizer."""
        self.paradigm = paradigm
        self.module = module
        self.language = language

        # Load templates from YAML instead of embedding in code
        self.STRUCTURE_TEMPLATES = load_templates()

    def generate_structure(self) -> list[str]:
        """Generate directory structure for selected paradigm."""
        if self.paradigm not in self.STRUCTURE_TEMPLATES:
            raise ValueError(f"Unknown paradigm: {self.paradigm}")

        paradigm_config = self.STRUCTURE_TEMPLATES[self.paradigm]
        structure_key = f"{self.language}_structure"

        if structure_key not in paradigm_config:
            raise ValueError(
                f"No structure defined for {self.language} in {self.paradigm}"
            )

        paths = paradigm_config[structure_key]
        return [path.format(module=self.module) for path in paths]

    def _title(self) -> str:
        return self.paradigm.replace("-", " ").title()

    def get_paradigm_description(self) -> str:
        """Describe the paradigm, or say that the YAML has no entry for it."""
        config = self.STRUCTURE_TEMPLATES.get(self.paradigm)
        if config is None:
            return f"{self._title()} (no directory template in architecture_templates.yaml)"
        return str(config["description"])

    def create_architecture_directories(self, project_path: Path) -> list[str]:
        """Create the parent directory of every templated path.

        Only three paradigms have a layout in the YAML. For the rest the
        recommender's pick is still documented, and no directories are
        invented for it.
        """
        if self.paradigm not in self.STRUCTURE_TEMPLATES:
            print(f"  No directory template for {self.paradigm}; none created")
            return []
        created: list[str] = []
        for rel in self.generate_structure():
            parent = (project_path / rel).parent
            if not parent.exists():
                parent.mkdir(parents=True)
                created.append(str(parent))
        return created

    def generate_architecture_readme(self) -> str:
        """Render ARCHITECTURE.md for the chosen paradigm."""
        lines = [
            "# Architecture",
            "",
            f"This project uses **{self._title()} Architecture**.",
            "",
            "## Overview",
            "",
            self.get_paradigm_description(),
            "",
        ]
        if self.paradigm in self.STRUCTURE_TEMPLATES:
            lines += ["## Structure", ""]
            lines += [f"- `{rel}`" for rel in self.generate_structure()]
            lines.append("")
        lines += [
            "## Implementation",
            "",
            f"See `Skill(archetypes:architecture-paradigm-{self.paradigm})`.",
            "",
        ]
        return "\n".join(lines)

    def generate_architecture_adr(self) -> str:
        """Render the ADR that records the paradigm decision."""
        return "\n".join(
            [
                f"# Architecture Decision Record: {self._title()}",
                "",
                "## Date",
                date.today().isoformat(),
                "",
                "## Status",
                "Accepted",
                "",
                "## Decision",
                f"Adopted **{self._title()} Architecture**.",
                "",
                "## Rationale",
                self.get_paradigm_description(),
                "",
                "## References",
                f"- `Skill(archetypes:architecture-paradigm-{self.paradigm})`",
                "- ARCHITECTURE.md",
                "",
            ]
        )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Template customizer")
    parser.add_argument("--paradigm", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--language", default="python")
    args = parser.parse_args()

    customizer = TemplateCustomizer(args.paradigm, args.module, args.language)
    structure = customizer.generate_structure()
    print(f"Generated structure for {args.paradigm}:")
    for path in structure:
        print(f"  - {path}")


if __name__ == "__main__":
    main()
