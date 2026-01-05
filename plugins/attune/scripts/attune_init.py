#!/usr/bin/env python3
"""Initialize a new project with Attune."""

import argparse
import sys
from pathlib import Path

from project_detector import ProjectDetector  # type: ignore[import]
from template_engine import (  # type: ignore[import]
    TemplateEngine,
    get_default_variables,
)


def initialize_git(project_path: Path, force: bool = False) -> bool:
    """Initialize git repository.

    Args:
        project_path: Path to project directory
        force: Force initialization even if .git exists

    Returns:
        True if successful

    """
    import subprocess  # noqa: PLC0415

    git_dir = project_path / ".git"

    if git_dir.exists() and not force:
        print(f"✓ Git repository already initialized: {git_dir}")
        return True

    try:
        subprocess.run(
            ["git", "init"],  # noqa: S607
            cwd=project_path,
            check=True,
            capture_output=True,
        )
        print(f"✓ Git repository initialized: {git_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to initialize git: {e}", file=sys.stderr)
        return False


def copy_templates(
    language: str,
    project_path: Path,
    variables: dict,
    templates_root: Path,
    force: bool = False,
) -> list[str]:
    """Copy and render templates to project.

    Args:
        language: Target language ("python", "rust", "typescript")
        project_path: Destination project path
        variables: Template variables
        templates_root: Root path of templates directory
        force: Overwrite existing files

    Returns:
        List of created file paths

    """
    engine = TemplateEngine(variables)
    template_dir = templates_root / language

    if not template_dir.exists():
        print(f"✗ Template directory not found: {template_dir}", file=sys.stderr)
        return []

    created_files = []

    # Find all template files
    template_files = list(template_dir.rglob("*.template"))

    for template_path in template_files:
        # Calculate relative path from template_dir
        rel_path = template_path.relative_to(template_dir)

        # Remove .template extension for output
        output_rel_str = str(rel_path).replace(".template", "")

        # Fix workflows path to be .github/workflows
        if output_rel_str.startswith("workflows/"):
            output_rel_str = ".github/" + output_rel_str

        output_rel = Path(output_rel_str)
        output_path = project_path / output_rel

        # Check if file exists
        if output_path.exists() and not force:
            response = input(f"File exists: {output_path}. Overwrite? [y/N]: ")
            if response.lower() != "y":
                print(f"⊘ Skipped: {output_path}")
                continue

        # Render and write template
        engine.render_file(template_path, output_path)
        print(f"✓ Created: {output_path}")
        created_files.append(str(output_path))

    return created_files


def create_project_structure(  # noqa: PLR0915
    project_path: Path, language: str, module_name: str, project_name: str
) -> None:
    """Create basic project directory structure.

    Args:
        project_path: Path to project
        language: Target language
        module_name: Python module name (for Python projects)
        project_name: Project name

    """
    if language == "python":
        # Create src/module_name structure
        src_dir = project_path / "src" / module_name
        src_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py
        init_file = src_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                f'"""{module_name} package."""\n\n__version__ = "0.1.0"\n'
            )
            print(f"✓ Created: {init_file}")

        # Create tests directory
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        test_init = tests_dir / "__init__.py"
        if not test_init.exists():
            test_init.write_text("")
            print(f"✓ Created: {test_init}")

        # Create README.md if it doesn't exist
        readme = project_path / "README.md"
        if not readme.exists():
            readme_content = f"""# {project_name}

A new Python project.

## Installation

```bash
uv sync
```

## Usage

```bash
make help
```
"""
            readme.write_text(readme_content)
            print(f"✓ Created: {readme}")

    elif language == "rust":
        # Create src/main.rs
        src_dir = project_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        main_rs = src_dir / "main.rs"
        if not main_rs.exists():
            main_rs.write_text('fn main() {\n    println!("Hello, world!");\n}\n')
            print(f"✓ Created: {main_rs}")

        # Create lib.rs for library
        lib_rs = src_dir / "lib.rs"
        if not lib_rs.exists():
            lib_content = f"""//! {project_name} library

pub fn hello() -> String {{
    "Hello from {project_name}!".to_string()
}}

#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn test_hello() {{
        assert_eq!(hello(), "Hello from {project_name}!");
    }}
}}
"""
            lib_rs.write_text(lib_content)
            print(f"✓ Created: {lib_rs}")

        # Create README.md
        readme = project_path / "README.md"
        if not readme.exists():
            readme_content = f"""# {project_name}

A new Rust project.

## Build

```bash
cargo build
```

## Usage

```bash
make help
```
"""
            readme.write_text(readme_content)
            print(f"✓ Created: {readme}")

    elif language == "typescript":
        # Create src/index.ts
        src_dir = project_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        index_ts = src_dir / "index.ts"
        if not index_ts.exists():
            index_content = (
                "export function hello(): string {\n"
                '  return "Hello from TypeScript!";\n'
                "}\n"
            )
            index_ts.write_text(index_content)
            print(f"✓ Created: {index_ts}")

        # Create src/App.tsx for React
        app_tsx = src_dir / "App.tsx"
        if not app_tsx.exists():
            app_content = f"""import React from "react";

function App() {{
  return (
    <div className="App">
      <h1>Welcome to {project_name}</h1>
    </div>
  );
}}

export default App;
"""
            app_tsx.write_text(app_content)
            print(f"✓ Created: {app_tsx}")

        # Create README.md
        readme = project_path / "README.md"
        if not readme.exists():
            readme_content = f"""# {project_name}

A new TypeScript/React project.

## Development

```bash
npm install
npm run dev
```

## Usage

```bash
make help
```
"""
            readme.write_text(readme_content)
            print(f"✓ Created: {readme}")


def main() -> None:
    """Run attune init CLI."""
    parser = argparse.ArgumentParser(description="Initialize a new project with attune")
    parser.add_argument(
        "--lang",
        "--language",
        choices=["python", "rust", "typescript"],
        help="Project language",
    )
    parser.add_argument(
        "--name",
        help="Project name",
    )
    parser.add_argument(
        "--author",
        default="Your Name",
        help="Project author",
    )
    parser.add_argument(
        "--email",
        default="you@example.com",
        help="Author email",
    )
    parser.add_argument(
        "--python-version",
        default="3.10",
        help="Python version (for Python projects)",
    )
    parser.add_argument(
        "--rust-edition",
        default="2021",
        help="Rust edition (for Rust projects)",
    )
    parser.add_argument(
        "--package-manager",
        default="npm",
        choices=["npm", "pnpm", "yarn"],
        help="Package manager (for TypeScript projects)",
    )
    parser.add_argument(
        "--repository",
        default="",
        help="Git repository URL",
    )
    parser.add_argument(
        "--description",
        default="A new project",
        help="Project description",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Project path (defaults to current directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git initialization",
    )

    args = parser.parse_args()

    project_path = args.path.resolve()

    # Detect or use specified language
    detector = ProjectDetector(project_path)
    language = args.lang or detector.detect_language()

    if not language:
        print(
            "Could not detect project language. Please specify with --lang",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get project name
    project_name = args.name or project_path.name

    print(f"\n{'=' * 60}")
    print("Attune Project Initialization")
    print(f"{'=' * 60}")
    print(f"Project: {project_name}")
    print(f"Language: {language}")
    print(f"Path: {project_path}")
    print(f"{'=' * 60}\n")

    # Get template variables
    variables = get_default_variables(
        project_name=project_name,
        language=language,
        author=args.author,
        email=args.email,
        python_version=args.python_version,
        rust_edition=args.rust_edition,
        package_manager=args.package_manager,
        repository=args.repository,
        description=args.description,
    )

    # Initialize git if needed
    if not args.no_git and not detector.check_git_initialized():
        initialize_git(project_path, force=args.force)

    # Find templates directory (relative to this script)
    script_dir = Path(__file__).parent
    templates_root = script_dir.parent / "templates"

    # Copy templates
    created_files = copy_templates(
        language=language,
        project_path=project_path,
        variables=variables,
        templates_root=templates_root,
        force=args.force,
    )

    # Create project structure
    create_project_structure(
        project_path, language, variables["PROJECT_MODULE"], project_name
    )

    print(f"\n{'=' * 60}")
    print("✓ Project initialized successfully!")
    print(f"{'=' * 60}")
    print(f"Created {len(created_files)} files")
    print("\nNext steps:")
    print(f"  1. cd {project_path}")
    print("  2. make dev-setup     # Install dependencies and hooks")
    print("  3. make test          # Run tests")
    print("  4. make help          # See available commands")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
