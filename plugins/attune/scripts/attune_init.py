#!/usr/bin/env python3
"""Initialize a new project with Attune."""

from __future__ import annotations

import argparse
import importlib
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

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
SUPPORTED_LANGUAGES = frozenset({"python", "rust", "typescript"})


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


def copy_templates(  # noqa: PLR0913 - template copying needs language, path, variables, root, and behavioral flags
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


# Decision-journal templates live in templates/decision_journal/. The canonical
# source is leyline:decision-journal; init prefers it when importable and falls
# back to these files so project-init never hard-depends on leyline being installed.
_JOURNAL_TEMPLATES_DIR = _TEMPLATES_DIR / "decision_journal"


def _journal_scaffold(kind: str) -> str:
    """Return a journal scaffold, preferring leyline's canonical template.

    leyline is an optional dependency; when it is not installed, fall back to
    the file in templates/decision_journal/ so project-init never hard-depends
    on it. A leyline that is present but fails to import (a real bug) is NOT
    masked: the error propagates instead of silently degrading to the template.
    """
    try:
        module = importlib.import_module("leyline.decision_journal")
    except ModuleNotFoundError as exc:
        root = (exc.name or "").split(".")[0]
        if root == "leyline":
            return (_JOURNAL_TEMPLATES_DIR / f"{kind}.md").read_text(encoding="utf-8")
        raise
    return str(module.new_file_content(kind))


def _create_docs_scaffolding(
    project_path: Path,
    dry_run: bool = False,
) -> list[str]:
    """Scaffold the decision-journal docs (tradeoffs + lessons-learned).

    Creates ``docs/tradeoffs.md`` and ``docs/lessons-learned.md`` if missing.
    Existing files are never clobbered. Honors ``dry_run``. Kept separate from
    the template ``created_files`` count so the summary stays template-scoped.

    Returns:
        Paths created (or that would be created in dry-run).

    """
    docs_dir = project_path / "docs"
    targets = {
        "tradeoffs": docs_dir / "tradeoffs.md",
        "lessons": docs_dir / "lessons-learned.md",
    }
    created: list[str] = []
    for kind, path in targets.items():
        if path.exists():
            print(f"⊘ Skipped (exists): {path}")
            continue
        if _write_or_preview(path, _journal_scaffold(kind), dry_run):
            created.append(str(path))
    return created


def _create_structure(
    dirs: list[Path],
    files: list[tuple[Path, str]],
    dry_run: bool,
) -> None:
    """Create directory and file structure from a data-driven spec.

    Each directory in dirs is created with mkdir(parents=True, exist_ok=True).
    Each file in files is written only when it does not already exist.
    Both operations print a dry-run preview instead of writing when
    dry_run is True, so callers do not need to repeat that logic.
    """
    for d in dirs:
        if dry_run:
            print(f"[DRY RUN] Would create directory: {d}")
        else:
            d.mkdir(parents=True, exist_ok=True)
    for file_path, file_content in files:
        if not file_path.exists():
            _write_or_preview(file_path, file_content, dry_run)


def _load_seed(lang: str, filename: str, **kwargs: str) -> str:
    """Load a seed file from the templates directory and format it.

    Reads templates/{lang}/{filename} and applies str.format(**kwargs).
    Template files use {variable_name} for substitution and {{ / }} for
    literal braces required in Rust and TypeScript templates.
    """
    path = _TEMPLATES_DIR / lang / filename
    return path.read_text(encoding="utf-8").format(**kwargs)


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
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language!r}. Supported: {sorted(SUPPORTED_LANGUAGES)}"
        )
    if language == "python":
        src_dir = project_path / "src" / module_name
        tests_dir = project_path / "tests"
        _create_structure(
            [src_dir, tests_dir],
            [
                (
                    src_dir / "__init__.py",
                    _load_seed("python", "__init__.py", module_name=module_name),
                ),
                (tests_dir / "__init__.py", ""),
                (
                    project_path / "README.md",
                    f"# {project_name}\n\nA new Python project.\n\n"
                    "## Installation\n\n```bash\nuv sync\n```\n\n"
                    "## Usage\n\n```bash\nmake help\n```\n",
                ),
            ],
            dry_run,
        )
    elif language == "rust":
        src_dir = project_path / "src"
        _create_structure(
            [src_dir],
            [
                (src_dir / "main.rs", _load_seed("rust", "main.rs")),
                (
                    src_dir / "lib.rs",
                    _load_seed("rust", "lib.rs", project_name=project_name),
                ),
                (
                    project_path / "README.md",
                    f"# {project_name}\n\nA new Rust project.\n\n"
                    "## Build\n\n```bash\ncargo build\n```\n\n"
                    "## Usage\n\n```bash\nmake help\n```\n",
                ),
            ],
            dry_run,
        )
    elif language == "typescript":
        src_dir = project_path / "src"
        _create_structure(
            [src_dir],
            [
                (src_dir / "index.ts", _load_seed("typescript", "index.ts")),
                (
                    src_dir / "App.tsx",
                    _load_seed("typescript", "App.tsx", project_name=project_name),
                ),
                (
                    project_path / "README.md",
                    f"# {project_name}\n\nA new TypeScript/React project.\n\n"
                    "## Development\n\n```bash\nnpm install\nnpm run dev\n```\n\n"
                    "## Usage\n\n```bash\nmake help\n```\n",
                ),
            ],
            dry_run,
        )


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


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``attune init`` argparse parser."""
    parser = argparse.ArgumentParser(description="Initialize a new project with attune")
    parser.add_argument(
        "--lang",
        "--language",
        choices=["python", "rust", "typescript"],
        help="Project language",
    )
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--author", default="Your Name", help="Project author")
    parser.add_argument("--email", default="you@example.com", help="Author email")
    parser.add_argument(
        "--python-version", default="3.9", help="Python version (for Python projects)"
    )
    parser.add_argument(
        "--rust-edition", default="2021", help="Rust edition (for Rust projects)"
    )
    parser.add_argument(
        "--package-manager",
        default="npm",
        choices=["npm", "pnpm", "yarn"],
        help="Package manager (for TypeScript projects)",
    )
    parser.add_argument("--repository", default="", help="Git repository URL")
    parser.add_argument(
        "--description", default="A new project", help="Project description"
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
    parser.add_argument("--no-git", action="store_true", help="Skip git initialization")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing files"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create timestamped backup before overwriting files",
    )
    return parser


def _resolve_language(requested: str | None, detector: ProjectDetector) -> str:
    """Use ``--lang`` if provided, otherwise auto-detect; ``sys.exit(1)`` on failure."""
    language = requested or detector.detect_language()
    if not language:
        print(
            "Could not detect project language. Please specify with --lang",
            file=sys.stderr,
        )
        sys.exit(1)
    return language


def _print_init_banner(project_name: str, language: str, project_path: Path) -> None:
    """Print the standard init banner for ``attune_init``."""
    print(f"\n{'=' * 60}")
    print("Attune Project Initialization")
    print(f"{'=' * 60}")
    print(f"Project: {project_name}")
    print(f"Language: {language}")
    print(f"Path: {project_path}")
    print(f"{'=' * 60}\n")


def main() -> None:
    """Run attune init CLI."""
    args = _build_parser().parse_args()
    project_path = args.path.resolve()

    detector = ProjectDetector(project_path)
    language = _resolve_language(args.lang, detector)
    project_name = args.name or project_path.name

    _print_init_banner(project_name, language, project_path)

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

    templates_root = Path(__file__).parent.parent / "templates"
    created_files = copy_templates(
        language=language,
        project_path=project_path,
        variables=variables,
        templates_root=templates_root,
        force=args.force,
        dry_run=args.dry_run,
        backup=args.backup,
    )

    create_project_structure(
        project_path,
        language,
        variables["PROJECT_MODULE"],
        project_name,
        dry_run=args.dry_run,
    )

    _create_docs_scaffolding(project_path, dry_run=args.dry_run)

    _print_summary(project_path, created_files)


if __name__ == "__main__":
    main()
