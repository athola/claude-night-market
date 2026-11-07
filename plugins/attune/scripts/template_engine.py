"""Substitute variables in template files."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any


class TemplateEngine:
    """Provide a simple template engine supporting {{VAR}} syntax."""

    def __init__(self, variables: dict[str, Any]):
        """Initialize template engine with variables.

        Args:
            variables: Dictionary of template variables

        """
        self.variables = variables

    def render(
        self, template_content: str, escape: Callable[[str], str] | None = None
    ) -> str:
        """Render template content with variable substitution.

        Args:
            template_content: Template string with {{VAR}} placeholders
            escape: Applied to each substituted value, for output formats
                whose strings need it (TOML)

        Returns:
            Rendered string with variables substituted

        """
        # Pattern to match {{VARIABLE_NAME}}
        pattern = r"\{\{([A-Z_][A-Z0-9_]*)\}\}"

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name not in self.variables:
                return match.group(0)
            value = str(self.variables[var_name])
            return escape(value) if escape else value

        return re.sub(pattern, replacer, template_content)

    def render_file(self, template_path: Path, output_path: Path) -> None:
        """Render template file to output location.

        Args:
            template_path: Path to template file
            output_path: Path where rendered file should be written

        """
        content = template_path.read_text()
        # The TOML templates put every variable inside a basic string, where
        # a quote or backslash in an author or description broke the file.
        escape = toml_basic_escape if output_path.suffix == ".toml" else None
        rendered = self.render(content, escape)

        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(rendered)


def toml_basic_escape(value: str) -> str:
    """Escape ``value`` for use inside a TOML basic (double-quoted) string."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return re.sub(
        r"[\x00-\x08\x0a-\x1f\x7f]", lambda m: f"\\u{ord(m.group()):04x}", escaped
    )


def python_module_name(project_name: str) -> str:
    """Turn a project name into a Python import name: my.app becomes my_app.

    Every non-identifier character becomes an underscore, and a leading
    digit gets an underscore prefix, so the result always imports.
    """
    module = re.sub(r"\W", "_", project_name).lower()
    return f"_{module}" if module[:1].isdigit() else module


def get_default_variables(  # noqa: PLR0913 - template variables need all defaults
    project_name: str,
    *,
    language: str = "python",
    author: str = "Your Name",
    email: str = "you@example.com",
    python_version: str = "3.10",
    rust_edition: str = "2021",
    package_manager: str = "npm",
    repository: str = "",
    license_type: str = "MIT",
    description: str = "A new project",
) -> dict[str, str]:
    """Get default template variables for any language.

    Args:
        project_name: Name of the project (e.g., "my-awesome-project")
        language: Project language ("python", "rust", "typescript")
        author: Project author name
        email: Author email
        python_version: Python version (e.g., "3.10")
        rust_edition: Rust edition (e.g., "2021")
        package_manager: NPM package manager (npm, pnpm, yarn)
        repository: Git repository URL
        license_type: License type (e.g., "MIT")
        description: Project description

    Returns:
        Dictionary of template variables

    """
    module_name = python_module_name(project_name)

    # Short python version (e.g., "310" from "3.10")
    python_short = python_version.replace(".", "")

    # Current year
    current_year = datetime.now().year

    # Base variables (common to all languages)
    variables = {
        "PROJECT_NAME": project_name,
        "PROJECT_MODULE": module_name,
        "PROJECT_DESCRIPTION": description,
        "AUTHOR": author,
        "EMAIL": email,
        "LICENSE": license_type,
        "YEAR": str(current_year),
        "REPOSITORY": repository,
    }

    # Language-specific variables
    if language == "python":
        variables.update(
            {
                "PYTHON_VERSION": python_version,
                "PYTHON_VERSION_SHORT": python_short,
            }
        )
    elif language == "rust":
        variables.update(
            {
                "RUST_EDITION": rust_edition,
            }
        )
    elif language == "typescript":
        variables.update(
            {
                "PACKAGE_MANAGER": package_manager,
            }
        )

    return variables
