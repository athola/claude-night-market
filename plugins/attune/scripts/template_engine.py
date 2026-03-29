"""Substitute variables in template files."""

import re
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

    def render(self, template_content: str) -> str:
        """Render template content with variable substitution.

        Args:
            template_content: Template string with {{VAR}} placeholders

        Returns:
            Rendered string with variables substituted

        """
        # Pattern to match {{VARIABLE_NAME}}
        pattern = r"\{\{([A-Z_][A-Z0-9_]*)\}\}"

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            value = self.variables.get(var_name, match.group(0))
            return str(value)

        return re.sub(pattern, replacer, template_content)

    def render_file(self, template_path: Path, output_path: Path) -> None:
        """Render template file to output location.

        Args:
            template_path: Path to template file
            output_path: Path where rendered file should be written

        """
        content = template_path.read_text()
        rendered = self.render(content)

        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(rendered)


def get_default_variables(
    project_name: str,
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
    # Convert project-name to project_name for module name
    module_name = project_name.replace("-", "_").replace(" ", "_").lower()

    # Short python version (e.g., "310" from "3.10")
    python_short = python_version.replace(".", "")

    # Current year
    from datetime import datetime

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
