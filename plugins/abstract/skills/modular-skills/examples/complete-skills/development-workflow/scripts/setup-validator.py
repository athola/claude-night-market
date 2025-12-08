#!/usr/bin/env python3
"""Setup validator for development workflow.

Validates that all required components are properly configured.
"""

import argparse
import shutil
import subprocess  # nosec: B404
import sys
from pathlib import Path


class SetupValidator:
    """Validates development environment setup."""

    def __init__(self, project_path: str = "."):
        """Initialize setup validator.

        Args:
            project_path: Path to project directory

        """
        self.project_path = Path(project_path).resolve()
        self.errors = []
        self.warnings = []
        self.successes = []

    def validate_all(self) -> bool:
        """Run all validations."""
        print("🔍 Validating development workflow setup...")

        validations = [
            self.validate_git_repository,
            self.validate_git_hooks,
            self.validate_python_environment,
            self.validate_node_environment,
            self.validate_testing_setup,
            self.validate_code_quality_tools,
            self.validate_ci_cd_setup,
            self.validate_documentation,
            self.validate_directory_structure,
        ]

        for validation in validations:
            try:
                validation()
            except Exception as e:
                self.errors.append(f"Validation {validation.__name__} failed: {str(e)}")

        self.print_results()
        return len(self.errors) == 0

    def validate_git_repository(self) -> None:
        """Validate Git repository setup."""
        git_dir = self.project_path / ".git"

        if not git_dir.exists():
            self.errors.append("Not a Git repository. Run 'git init'")
            return

        # Check for .gitignore
        gitignore_path = self.project_path / ".gitignore"
        if gitignore_path.exists():
            self.successes.append("✅ .gitignore exists")
        else:
            self.warnings.append("⚠️  .gitignore missing. Recommended for all projects")

        # Check for remotes
        try:
            git_path = shutil.which("git")
            if git_path:
                # nosemgrep: git-subprocess-safe-path - Using shutil.which for trusted
                # git binary
                # with hardcoded args
                result = subprocess.run(  # noqa: S603  # nosec: B603
                    [git_path, "remote", "-v"],
                    check=False,
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    shell=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    self.successes.append("✅ Git remotes configured")
                else:
                    self.warnings.append("⚠️  No Git remotes configured")
            else:
                self.warnings.append("⚠️  Git not found in PATH")
        except FileNotFoundError:
            self.errors.append("❌ Git not installed or not in PATH")

    def validate_git_hooks(self) -> None:
        """Validate Git hooks setup."""
        hooks_dir = self.project_path / ".git" / "hooks"

        if not hooks_dir.exists():
            return

        hooks_to_check = ["pre-commit", "pre-push", "commit-msg"]
        found_hooks = []

        for hook in hooks_to_check:
            hook_path = hooks_dir / hook
            if hook_path.exists() and hook_path.stat().st_size > 0:
                found_hooks.append(hook)

        if found_hooks:
            self.successes.append(f"✅ Git hooks found: {', '.join(found_hooks)}")
        else:
            self.warnings.append("⚠️  No Git hooks configured")

    def validate_python_environment(self) -> None:
        """Validate Python development environment."""
        # Check for Python files
        py_files = list(self.project_path.rglob("*.py"))
        if not py_files:
            return  # Not a Python project

        # Check for virtual environment
        venv_paths = [
            self.project_path / "venv",
            self.project_path / ".venv",
            self.project_path / "env",
        ]

        venv_found = any(path.exists() for path in venv_paths)
        if venv_found:
            self.successes.append("✅ Virtual environment detected")
        else:
            self.warnings.append("⚠️  No virtual environment found")

        # Check for requirements files
        req_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
            "Pipfile",
            "poetry.lock",
        ]

        found_reqs = [f for f in req_files if (self.project_path / f).exists()]
        if found_reqs:
            reqs_str = ", ".join(found_reqs)
            self.successes.append(f"✅ Dependencies configured: {reqs_str}")
        else:
            self.errors.append("❌ No dependency configuration found")

    def validate_node_environment(self) -> None:
        """Validate Node.js development environment."""
        # Check for Node.js files
        node_files = [
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        ]

        node_files_found = [f for f in node_files if (self.project_path / f).exists()]
        if not node_files_found:
            return  # Not a Node.js project

        node_files_str = ", ".join(node_files_found)
        self.successes.append(f"✅ Node.js project detected: {node_files_str}")

        # Check for node_modules
        node_modules = self.project_path / "node_modules"
        if node_modules.exists():
            self.successes.append("✅ Dependencies installed")
        else:
            self.warnings.append(
                "⚠️  Dependencies not installed. Run 'npm install' or equivalent"
            )

    def validate_testing_setup(self) -> None:
        """Validate testing framework setup."""
        # Python testing
        test_dirs = ["tests", "test", "specs"]
        test_dirs_found = [d for d in test_dirs if (self.project_path / d).exists()]

        if test_dirs_found:
            test_dirs_str = ", ".join(test_dirs_found)
            self.successes.append(f"✅ Test directories found: {test_dirs_str}")

        # Check for test configuration
        test_configs = [
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "pyproject.toml",  # Can contain pytest config
            "jest.config.js",
            "jest.config.json",
            "vitest.config.js",
            "cypress.config.js",
            "playwright.config.js",
        ]

        found_configs = [c for c in test_configs if (self.project_path / c).exists()]
        if found_configs:
            configs_str = ", ".join(found_configs)
            self.successes.append(f"✅ Test configuration found: {configs_str}")

        # Check for actual test files
        test_files = list(self.project_path.rglob("test_*.py"))
        test_files.extend(list(self.project_path.rglob("*_test.py")))
        test_files.extend(list(self.project_path.rglob("*.test.js")))
        test_files.extend(list(self.project_path.rglob("*.spec.js")))

        if test_files:
            self.successes.append(f"✅ Test files found: {len(test_files)}")
        else:
            self.warnings.append("⚠️  No test files found")

    def validate_code_quality_tools(self) -> None:
        """Validate code quality and linting setup."""
        linting_tools = {
            ".pre-commit-config.yaml": "Pre-commit hooks",
            ".eslintrc.js": "ESLint (JavaScript)",
            ".eslintrc.json": "ESLint (JavaScript)",
            "pyproject.toml": "Modern Python tools (ruff, black, mypy)",
            ".flake8": "Flake8 (Python)",
            ".pylintrc": "Pylint (Python)",
            ".editorconfig": "Editor configuration",
            ".prettierrc": "Prettier (JavaScript/TypeScript)",
        }

        found_tools = []
        for config_file, description in linting_tools.items():
            if (self.project_path / config_file).exists():
                found_tools.append(description)

        if found_tools:
            tools_str = ", ".join(found_tools)
            self.successes.append(f"✅ Code quality tools configured: {tools_str}")
        else:
            self.warnings.append("⚠️  No code quality tools configured")

    def validate_ci_cd_setup(self) -> None:
        """Validate CI/CD setup."""
        ci_cd_dirs = [
            ".github",
            ".gitlab-ci.yml",
            ".circleci",
            "Jenkinsfile",
            ".azure-pipelines",
            "bitbucket-pipelines.yml",
        ]

        found_ci_cd = []
        for ci_cd in ci_cd_dirs:
            if isinstance(ci_cd, str) and (self.project_path / ci_cd).exists():
                found_ci_cd.append(ci_cd)
            elif (
                isinstance(ci_cd, str)
                and ci_cd.startswith(".")
                and (self.project_path / ci_cd).exists()
            ):
                found_ci_cd.append(ci_cd)

        # Special check for .github directory
        github_dir = self.project_path / ".github"
        if github_dir.exists():
            workflows = list((github_dir / "workflows").glob("*.yml"))
            workflows.extend(list((github_dir / "workflows").glob("*.yaml")))
            if workflows:
                found_ci_cd.append(f".github/workflows ({len(workflows)} workflows)")

        if found_ci_cd:
            self.successes.append(f"✅ CI/CD configured: {', '.join(found_ci_cd)}")
        else:
            self.warnings.append("⚠️  No CI/CD configuration found")

    def validate_documentation(self) -> None:
        """Validate documentation setup."""
        docs_files = [
            "README.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "LICENSE",
            "docs/README.md",
        ]

        found_docs = [d for d in docs_files if (self.project_path / d).exists()]
        if found_docs:
            self.successes.append(f"✅ Documentation found: {', '.join(found_docs)}")

        # Check for advanced documentation
        advanced_docs = [
            "mkdocs.yml",
            "docs/_config.yml",
            "sphinx.conf.py",
            "docusaurus.config.js",
            ".vitepress/config.js",
        ]

        found_advanced = [d for d in advanced_docs if (self.project_path / d).exists()]
        if found_advanced:
            advanced_str = ", ".join(found_advanced)
            self.successes.append(f"✅ Advanced documentation tools: {advanced_str}")

    def validate_directory_structure(self) -> None:
        """Validate project directory structure."""
        # Common source directories
        src_dirs = ["src", "lib", "app", "server"]
        found_src = [d for d in src_dirs if (self.project_path / d).exists()]

        if found_src:
            self.successes.append(f"✅ Source directories: {', '.join(found_src)}")

        # Configuration directories
        config_dirs = [".config", "config", "conf"]
        found_config = [d for d in config_dirs if (self.project_path / d).exists()]

        if found_config:
            config_str = ", ".join(found_config)
            self.successes.append(f"✅ Configuration directories: {config_str}")

        # Build/output directories (should be in .gitignore)
        build_dirs = ["build", "dist", "target", "__pycache__", ".pytest_cache"]
        found_build = [d for d in build_dirs if (self.project_path / d).exists()]

        if found_build:
            gitignore_path = self.project_path / ".gitignore"
            if gitignore_path.exists():
                gitignore_content = gitignore_path.read_text()
                ignored_builds = [d for d in found_build if d in gitignore_content]
                if ignored_builds:
                    ignored_str = ", ".join(ignored_builds)
                    self.successes.append(
                        f"✅ Build directories properly ignored: {ignored_str}"
                    )
                else:
                    builds_str = ", ".join(found_build)
                    self.warnings.append(
                        f"⚠️  Build directories not in .gitignore: {builds_str}"
                    )

    def print_results(self) -> None:
        """Print validation results."""
        print(f"\n📊 Validation Results for {self.project_path.name}")
        print("=" * 50)

        if self.successes:
            print(f"\n✅ {len(self.successes)} Successes:")
            for success in self.successes:
                print(f"  {success}")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print(f"\n❌ {len(self.errors)} Errors:")
            for error in self.errors:
                print(f"  {error}")

        # Summary
        total = len(self.successes) + len(self.warnings) + len(self.errors)
        if total == 0:
            print("\n🔍 No validations completed")
        elif len(self.errors) == 0:
            if len(self.warnings) == 0:
                print(
                    f"\n🎉 Perfect setup! All {len(self.successes)} validations passed."
                )
            else:
                print(
                    f"\n✅ Good setup! {len(self.successes)} passed, "
                    f"{len(self.warnings)} warnings to consider."
                )
        else:
            print(
                f"\n⚠️  Setup needs attention: {len(self.errors)} errors, "
                f"{len(self.warnings)} warnings, {len(self.successes)} successes."
            )

    def generate_setup_script(self) -> str:
        """Generate a setup script based on missing components."""
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated setup script",
            "echo '🚀 Setting up development environment...'",
            "",
        ]

        # Git setup
        if not (self.project_path / ".git").exists():
            script_lines.extend(
                [
                    "# Initialize Git repository",
                    "git init",
                    "echo '# Project Name' > README.md",
                    "git add README.md",
                    "git commit -m 'Initial commit'",
                    "",
                ]
            )

        # Python setup
        py_files = list(self.project_path.rglob("*.py"))
        if py_files and not any(
            (self.project_path / p).exists() for p in ["venv", ".venv", "env"]
        ):
            script_lines.extend(
                [
                    "# Set up Python virtual environment",
                    "python -m venv venv",
                    "source venv/bin/activate",
                    "pip install --upgrade pip",
                    "",
                ]
            )

        # Node.js setup
        if (self.project_path / "package.json").exists() and not (
            self.project_path / "node_modules"
        ).exists():
            script_lines.extend(["# Install Node.js dependencies", "npm install", ""])

        # Pre-commit hooks
        if not (self.project_path / ".pre-commit-config.yaml").exists():
            script_lines.extend(
                [
                    "# Set up pre-commit hooks",
                    "pip install pre-commit",
                    "pre-commit install",
                    "",
                ]
            )

        script_lines.extend(
            [
                "echo '✅ Setup complete!'",
                "echo 'Run this script to complete your development "
                "environment setup.'",
            ]
        )

        return "\n".join(script_lines)


def main():
    """Entry point for setup validator script."""
    parser = argparse.ArgumentParser(description="Validate development workflow setup")
    parser.add_argument(
        "path", nargs="?", default=".", help="Project path (default: current directory)"
    )
    parser.add_argument(
        "--generate-script", action="store_true", help="Generate setup script"
    )
    parser.add_argument("--output", "-o", help="Output file for generated script")

    args = parser.parse_args()

    validator = SetupValidator(args.path)

    if args.generate_script:
        script = validator.generate_setup_script()
        if args.output:
            with open(args.output, "w") as f:
                f.write(script)
            print(f"📝 Setup script generated: {args.output}")
        else:
            print(script)
        return

    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
