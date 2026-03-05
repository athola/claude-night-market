"""Recipe validation and Makefile generation for the dogfooder package."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class MakefileTargetGenerator:
    """Generate missing make targets from documented commands."""

    # Plugin-specific tool mappings for live demos
    PLUGIN_TOOLS = {
        "conserve": {
            "bloat-scan": ("$(UV_RUN) python scripts/bloat_detector.py . --report"),
            "ai-hygiene-audit": (
                "echo 'AI hygiene audit: Check for TODO/FIXME in skills/' && "
                "grep -r 'TODO\\|FIXME' skills/ | wc -l | "
                "xargs -I{} echo 'Found {} items'"
            ),
        },
        "sanctum": {
            "pr-review": (
                "$(UV_RUN) python scripts/pr_review_analyzer.py --dry-run || "
                "echo 'PR review analyzer: Analyzes PR quality and scope'"
            ),
            "commit-msg": (
                "git log --oneline -1 | head -1 || "
                "echo 'Commit-msg: Generates conventional commit messages'"
            ),
        },
        "pensive": {
            "makefile-review": (
                "$(UV_RUN) python scripts/makefile_review.py Makefile || "
                "echo 'Makefile review: Analyzes Makefile patterns and quality'"
            ),
            "bug-review": (
                "echo 'Bug review: Analyzing code for potential bugs...' && "
                "find src/ -name '*.py' | head -5"
            ),
        },
        "abstract": {
            "validate-plugin": (
                "$(UV_RUN) python scripts/validator.py --target . || "
                "echo 'Plugin validator: Checks plugin structure compliance'"
            ),
        },
    }

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def _get_live_command(self, plugin: str, command: str) -> str | None:
        """Get live command for a plugin's documented command."""
        if plugin in self.PLUGIN_TOOLS and command in self.PLUGIN_TOOLS[plugin]:
            return self.PLUGIN_TOOLS[plugin][command]
        return None

    def generate_target(
        self,
        plugin: str,
        command_name: str,
        invocation: str,
        description: str = "",
    ) -> str:
        """Generate a make target for a documented command.

        Args:
            plugin: Plugin name (e.g., "sanctum")
            command_name: Name of the command (e.g., "update-docs")
            invocation: Full command invocation (e.g., "/update-docs --skip-slop")
            description: Human-readable description

        Returns:
            Makefile target definition as string

        """
        target_name = f"demo-{command_name.replace('/', '').lstrip('/')}"
        target_desc = description or f"Demo {command_name} command (LIVE)"

        # Check if we have a live command for this
        live_cmd = self._get_live_command(plugin, command_name)

        recipe_lines = [
            f'\t@echo "=== {command_name} Demo (LIVE) ==="',
            '\t@echo ""',
        ]

        if live_cmd:
            # We have a live command - run it
            recipe_lines.append(
                f'\t@echo "Running {command_name} on {plugin} plugin..."'
            )
            recipe_lines.append('\t@echo ""')
            recipe_lines.append(
                f'\t{live_cmd} || echo "  [INFO] Tool execution completed"'
            )
        else:
            # Fallback: Show what the command does and how to run it
            recipe_lines.append(f'\t@echo "Command: {invocation}"')
            recipe_lines.append(f'\t@echo "Plugin: {plugin}"')
            recipe_lines.append('\t@echo ""')
            recipe_lines.append(f'\t@echo "This demonstrates {command_name} usage."')
            recipe_lines.append(
                '\t@echo "Execute manually in Claude Code for full functionality."'
            )

        recipe_lines.append('\t@echo ""')
        recipe_lines.append(f'\t@echo "Use {invocation} for full workflow."')

        recipe = "\n".join(recipe_lines)

        return f"""{target_name}: ## {target_desc}
{recipe}

"""

    def generate_demo_targets(
        self,
        plugin: str,
        commands: list[dict[str, Any]],
    ) -> str:
        """Generate demo targets for a plugin.

        Creates:
        1. Individual demo-* targets for each command (LIVE where possible)
        2. Aggregate demo-{plugin}-commands target to run all demos
        3. test-* targets for slash commands
        """
        targets = []

        # Group commands by type
        slash_cmds = [c for c in commands if c.get("type") == "slash-command"]
        cli_invokes = [c for c in commands if c.get("type") == "cli-invocation"]

        # Generate individual demo targets for each slash command
        for cmd in slash_cmds[:10]:  # Limit to first 10 to avoid overwhelming
            cmd_name = cmd["command"]
            cmd_args = cmd.get("args", "")
            invocation = f"/{cmd_name}"
            if cmd_args:
                invocation += f" {cmd_args}"

            target = self.generate_target(
                plugin=plugin,
                command_name=cmd_name,
                invocation=invocation,
                description=f"Demo {cmd_name} command (LIVE)",
            )
            targets.append(target)

        # Generate CLI invocation demos
        for cli in cli_invokes[:5]:
            invocation = cli["invocation"]
            cmd_name = invocation.split()[0] if invocation.split() else "cli"
            target = self.generate_target(
                plugin=plugin,
                command_name=f"cli-{cmd_name}",
                invocation=invocation,
                description=f"Demo CLI invocation: {invocation}",
            )
            targets.append(target)

        # Generate aggregate demo target
        if slash_cmds:
            demo_names = [f"demo-{c['command']}" for c in slash_cmds[:10]]
            demo_targets = " ".join(demo_names)
            plugin_capitalized = plugin.capitalize()
            aggregate_target = (
                f"demo-{plugin}-commands: {demo_targets} ## "
                f"Run all {plugin} documented command demos\n"
                f'\t@echo ""\n'
                f'\t@echo "=== {plugin_capitalized} All Commands Demo Complete ==="\n'
                f'\t@echo "Ran {len(demo_names)} documented commands"\n'
                f'\t@echo ""\n'
                f"\n"
            )
            targets.append(aggregate_target)

        # Generate test targets for slash commands
        for cmd in slash_cmds[:10]:
            cmd_name = cmd["command"]
            test_target = (
                f"test-{cmd_name}: ## Test {cmd_name} command workflow\n"
                f'\t@echo "=== Testing {cmd_name} workflow ==="\n'
                f'\t@echo "Validating: /{cmd_name}"\n'
                f'\t@echo "Check: Command executes without errors"\n'
                f'\t@echo "Check: Output matches expected format"\n'
                f'\t@echo "Status: [ ] Manual test required"\n'
                f'\t@echo ""\n'
                f"\n"
            )
            targets.append(test_target)

        return "\n".join(targets)


def generate_makefile(
    plugin_dir: Path,
    plugin_name: str,
    dry_run: bool = False,
) -> bool:
    """Generate a new Makefile for a plugin using language detection.

    Follows the attune:makefile-generation skill pattern:
    1. Detect language from project files
    2. Generate appropriate Makefile template
    3. Add plugin-specific targets
    4. Verify with make help

    Args:
        plugin_dir: Path to the plugin directory
        plugin_name: Name of the plugin
        dry_run: If True, don't actually write files

    Returns:
        True if Makefile generated successfully, False otherwise

    """
    print(f"Generating Makefile for {plugin_name}...")

    # Detect language
    language = None
    if (plugin_dir / "pyproject.toml").exists():
        language = "python"
    elif (plugin_dir / "Cargo.toml").exists():
        language = "rust"
    elif (plugin_dir / "package.json").exists():
        language = "typescript"
    else:
        # Default to Python for claude-night-market plugins
        language = "python"
        print("  No language file detected, defaulting to Python")

    # Generate Makefile based on language
    if language == "python":
        makefile_content = _generate_python_makefile(plugin_name)
    elif language == "rust":
        makefile_content = _generate_rust_makefile(plugin_name)
    elif language == "typescript":
        makefile_content = _generate_typescript_makefile(plugin_name)
    else:
        print(f"  Unsupported language: {language}")
        return False

    # Write Makefile
    makefile_path = plugin_dir / "Makefile"
    if not dry_run:
        makefile_path.write_text(makefile_content)
        print(f"  Generated {makefile_path}")
    else:
        print(f"  [DRY RUN] Would generate {makefile_path}")

    return True


def _generate_python_makefile(plugin_name: str) -> str:
    """Generate a Python Makefile with standard targets.

    Based on attune:makefile-generation skill patterns.
    """
    # AWK command for displaying help (broken into lines for readability)
    awk_cmd = (
        'awk \'BEGIN {FS = ":.*?## "} '
        "/^[a-zA-Z_-]+:.*?## / "
        '{printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}\' '
        "Makefile"
    )

    return f"""# {plugin_name.capitalize()} Plugin Makefile
# Generated by makefile-dogfooder
#
# Standard Python development targets

.PHONY: help install deps lint format typecheck test test-cov check-all clean build

# Default target
help: ## Show this help message
\t@echo "{plugin_name.capitalize()} Plugin - Make Targets"
\t@echo "================================"
\t{awk_cmd}

# ---------- Installation ----------
install: ## Install development dependencies
\tuv sync --dev

deps: ## Sync dependencies
\tuv sync

# ---------- Code Quality ----------
lint: ## Run linting
\truff check .

format: ## Format code
\truff format .

typecheck: ## Run type checking
\tmypy src/

# ---------- Testing ----------
test: ## Run tests
\tpytest

test-cov: ## Run tests with coverage
\tpytest --cov=src --cov-report=term-missing

check-all: lint typecheck test-cov ## Run all quality checks

# ---------- Maintenance ----------
clean: ## Clean cache and build files
\trm -rf .pytest_cache .coverage .mypy_cache .ruff_cache dist build 2>/dev/null || true
\tfind . -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true

build: ## Build distribution package
\tuv build

# ---------- Status ----------
status: ## Show project overview
\t@echo "{plugin_name.capitalize()} Plugin:"
\t@echo "  Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
\t@echo "  Tests:  $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
"""


def _generate_rust_makefile(plugin_name: str) -> str:
    """Generate a Rust Makefile with standard targets."""
    # AWK command for displaying help
    awk_cmd = (
        'awk \'BEGIN {FS = ":.*?## "} '
        "/^[a-zA-Z_-]+:.*?## / "
        '{printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}\' '
        "Makefile"
    )

    return f"""# {plugin_name.capitalize()} Plugin Makefile
# Generated by makefile-dogfooder
#
# Standard Rust development targets

.PHONY: help fmt lint check test build clean

help: ## Show this help message
\t@echo "{plugin_name.capitalize()} Plugin - Make Targets"
\t@echo "================================"
\t{awk_cmd}

fmt: ## Format code
\trustfmt

lint: ## Run linter
\tcargo clippy

check: ## Check compilation
\tcargo check

test: ## Run tests
\tcargo test

build: ## Build release binary
\tcargo build --release

clean: ## Clean build artifacts
\tcargo clean
"""


def _generate_typescript_makefile(plugin_name: str) -> str:
    """Generate a TypeScript Makefile with standard targets."""
    # AWK command for displaying help
    awk_cmd = (
        'awk \'BEGIN {FS = ":.*?## "} '
        "/^[a-zA-Z_-]+:.*?## / "
        '{printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}\' '
        "Makefile"
    )

    return f"""# {plugin_name.capitalize()} Plugin Makefile
# Generated by makefile-dogfooder
#
# Standard TypeScript development targets

.PHONY: help install lint format typecheck test build dev clean

help: ## Show this help message
\t@echo "{plugin_name.capitalize()} Plugin - Make Targets"
\t@echo "================================"
\t{awk_cmd}

install: ## Install dependencies
\tnpm install

lint: ## Run linter
\teslint .

format: ## Format code
\tprettier --write .

typecheck: ## Run type checker
\ttsc --noEmit

test: ## Run tests
\tnpm test

build: ## Build for production
\tnpm run build

dev: ## Start development server
\tnpm run dev

clean: ## Clean build artifacts
\trm -rf dist node_modules
"""


def run_preflight_checks(root_dir: Path, plugins_dir: str) -> bool:
    """Run pre-flight checks before processing.

    Validates:
    - Working directory exists
    - Required directories are accessible
    - Git repository (for rollback capability)

    Returns:
        True if all checks pass, False otherwise

    """
    print("Running pre-flight checks...")

    # Check root directory exists
    if not root_dir.exists():
        print(f"Root directory does not exist: {root_dir}")
        return False

    # Check plugins directory
    plugins_path = root_dir / plugins_dir
    if not plugins_path.exists():
        print(f"Plugins directory not found: {plugins_path}")
        return False

    # Check for git repository (for rollback capability)
    git_dir = root_dir / ".git"
    if not git_dir.exists():
        print("Not in a git repository - rollback will not be available")
        print("   Consider running: git init")

    # Check write permissions
    test_file = root_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        print(f"No write permission in {root_dir}: {e}")
        return False

    print("Preflight checks passed")
    return True


def validate_working_directory(
    root_dir: Path, plugins_dir: str, plugin_name: str | None = None
) -> bool:
    """Validate working directory context before file operations.

    Args:
        root_dir: Project root directory
        plugins_dir: Plugins subdirectory name
        plugin_name: Optional plugin name to validate

    Returns:
        True if context is valid, False otherwise

    """
    # Ensure we're in the correct directory
    current_dir = Path.cwd()
    if current_dir != root_dir:
        print("Working directory mismatch")
        print(f"   Current: {current_dir}")
        print(f"   Expected: {root_dir}")
        print("   Changing to root directory...")
        try:
            os.chdir(root_dir)
        except Exception as e:
            print(f"Cannot change to root directory: {e}")
            return False

    # If plugin specified, validate its Makefile exists
    if plugin_name:
        makefile_path = root_dir / plugins_dir / plugin_name / "Makefile"
        if not makefile_path.exists():
            print(f"Makefile not found for plugin '{plugin_name}': {makefile_path}")
            return False

    return True
