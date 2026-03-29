#!/usr/bin/env python3
"""Initialize a new project with Attune."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from project_detector import ProjectDetector
from template_engine import (
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
    git_dir = project_path / ".git"

    if git_dir.exists() and not force:
        print(f"✓ Git repository already initialized: {git_dir}")
        return True

    try:
        subprocess.run(
            ["git", "init"],
            cwd=project_path,
            check=True,
            capture_output=True,
            timeout=30,
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
    dry_run: bool = False,
    backup: bool = False,
) -> list[str]:
    """Copy and render templates to project.

    Args:
        language: Target language ("python", "rust", "typescript")
        project_path: Destination project path
        variables: Template variables
        templates_root: Root path of templates directory
        force: Overwrite existing files
        dry_run: Preview changes without writing files
        backup: Create backup before overwriting files

    Returns:
        List of created file paths

    """
    engine = TemplateEngine(variables)
    template_dir = templates_root / language

    if not template_dir.exists():
        print(f"✗ Template directory not found: {template_dir}", file=sys.stderr)
        return []

    created_files = []
    backup_dir = None

    # Create backup directory if needed
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = project_path / ".backup" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"📦 Backup directory: {backup_dir}")

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

        # Dry run - just print what would happen
        if dry_run:
            if output_path.exists():
                print(f"[DRY RUN] Would overwrite: {output_path}")
            else:
                print(f"[DRY RUN] Would create: {output_path}")
            created_files.append(str(output_path))
            continue

        # Check if file exists
        if output_path.exists():
            # Backup if requested
            if backup and backup_dir:
                backup_file = backup_dir / output_rel
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output_path, backup_file)
                print(f"📦 Backed up: {output_path} -> {backup_file}")

            if not force:
                response = input(f"File exists: {output_path}. Overwrite? [y/N]: ")
                if response.lower() != "y":
                    print(f"⊘ Skipped: {output_path}")
                    continue

        # Render and write template
        engine.render_file(template_path, output_path)
        print(f"✓ Created: {output_path}")
        created_files.append(str(output_path))

    return created_files


def _write_or_preview(
    path: Path,
    content: str,
    dry_run: bool,
) -> bool:
    """Write a file or preview it in dry-run mode.

    Args:
        path: Destination file path
        content: File content to write
        dry_run: If True, print intent without writing

    Returns:
        True if the file was written (or would be in dry-run)

    """
    if dry_run:
        print(f"[DRY RUN] Would create: {path}")
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"✓ Created: {path}")
    return True


def _create_python_structure(
    project_path: Path,
    module_name: str,
    project_name: str,
    dry_run: bool,
) -> None:
    """Create Python project directory structure.

    Args:
        project_path: Path to the project root
        module_name: Python module name (snake_case)
        project_name: Human-readable project name
        dry_run: Preview changes without writing files

    """
    src_dir = project_path / "src" / module_name
    if dry_run:
        print(f"[DRY RUN] Would create directory: {src_dir}")
    else:
        src_dir.mkdir(parents=True, exist_ok=True)

    init_file = src_dir / "__init__.py"
    if not init_file.exists():
        _write_or_preview(
            init_file,
            f'"""{module_name} package."""\n\n__version__ = "0.1.0"\n',
            dry_run,
        )

    tests_dir = project_path / "tests"
    if dry_run:
        print(f"[DRY RUN] Would create directory: {tests_dir}")
    else:
        tests_dir.mkdir(parents=True, exist_ok=True)

    test_init = tests_dir / "__init__.py"
    if not test_init.exists():
        _write_or_preview(test_init, "", dry_run)

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
        _write_or_preview(readme, readme_content, dry_run)


def _create_rust_structure(
    project_path: Path,
    project_name: str,
    dry_run: bool,
) -> None:
    """Create Rust project directory structure.

    Args:
        project_path: Path to the project root
        project_name: Human-readable project name
        dry_run: Preview changes without writing files

    """
    src_dir = project_path / "src"
    if dry_run:
        print(f"[DRY RUN] Would create directory: {src_dir}")
    else:
        src_dir.mkdir(parents=True, exist_ok=True)

    main_rs = src_dir / "main.rs"
    if not main_rs.exists():
        _write_or_preview(
            main_rs,
            'fn main() {\n    println!("Hello, world!");\n}\n',
            dry_run,
        )

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
        _write_or_preview(lib_rs, lib_content, dry_run)

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
        _write_or_preview(readme, readme_content, dry_run)


def _create_typescript_structure(
    project_path: Path,
    project_name: str,
    dry_run: bool,
) -> None:
    """Create TypeScript project directory structure.

    Args:
        project_path: Path to the project root
        project_name: Human-readable project name
        dry_run: Preview changes without writing files

    """
    src_dir = project_path / "src"
    if dry_run:
        print(f"[DRY RUN] Would create directory: {src_dir}")
    else:
        src_dir.mkdir(parents=True, exist_ok=True)

    index_ts = src_dir / "index.ts"
    if not index_ts.exists():
        index_content = (
            'export function hello(): string {\n  return "Hello from TypeScript!";\n}\n'
        )
        _write_or_preview(index_ts, index_content, dry_run)

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
        _write_or_preview(app_tsx, app_content, dry_run)

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
        _write_or_preview(readme, readme_content, dry_run)


def create_project_structure(
    project_path: Path,
    language: str,
    module_name: str,
    project_name: str,
    dry_run: bool = False,
) -> None:
    """Create basic project directory structure.

    Args:
        project_path: Path to project
        language: Target language
        module_name: Python module name (for Python projects)
        project_name: Project name
        dry_run: Preview changes without writing files

    """
    if language == "python":
        _create_python_structure(project_path, module_name, project_name, dry_run)
    elif language == "rust":
        _create_rust_structure(project_path, project_name, dry_run)
    elif language == "typescript":
        _create_typescript_structure(project_path, project_name, dry_run)


def _run_post_init_git(
    project_path: Path,
    no_git: bool,
    force: bool,
    detector: ProjectDetector,
) -> None:
    """Initialize git repository if needed.

    Args:
        project_path: Path to project root
        no_git: If True, skip git initialization
        force: Force re-initialization if .git already exists
        detector: Project detector instance

    """
    if not no_git and not detector.check_git_initialized():
        initialize_git(project_path, force=force)


def _print_summary(project_path: Path, created_files: list[str]) -> None:
    """Print post-initialization summary to stdout.

    Args:
        project_path: Path to the initialized project
        created_files: Files created during initialization

    """
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create timestamped backup before overwriting files",
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

    _run_post_init_git(project_path, args.no_git, args.force, detector)

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
        dry_run=args.dry_run,
        backup=args.backup,
    )

    # Create project structure
    create_project_structure(
        project_path,
        language,
        variables["PROJECT_MODULE"],
        project_name,
        dry_run=args.dry_run,
    )

    _print_summary(project_path, created_files)


if __name__ == "__main__":
    main()
