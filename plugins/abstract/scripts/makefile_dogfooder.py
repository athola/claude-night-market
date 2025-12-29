#!/usr/bin/env python3
"""Makefile Dogfooder - Analyze and enhance Makefiles for complete user functionality.

This script orchestrates the makefile-dogfooder skill workflow:
1. Discovery - Find and inventory Makefiles
2. Analysis - Identify gaps and anti-patterns
3. Testing - Safely validate existing targets
4. Generation - Create missing targets with templates
"""

import argparse
import re
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Constants for magic numbers
TARGET_PARTS_COUNT = 2
MIN_HELP_COMMANDS = 3


class Scope(Enum):
    """Enumeration for analysis scope levels."""

    ROOT = "root"
    PLUGINS = "plugins"
    ALL = "all"


class Mode(Enum):
    """Enumeration for operation modes."""

    ANALYZE = "analyze"
    TEST = "test"
    FULL = "full"


class TargetType(Enum):
    """Enumeration for Makefile target safety levels."""

    SAFE = "safe"  # Always safe to run (help, status)
    CONDITIONAL = "conditional"  # Requires inspection (test, lint)
    RISKY = "risky"  # Never run in CI (clean, install)


@dataclass
class Target:
    """Represents a Makefile target with its metadata."""

    name: str
    description: str
    phony: bool
    dependencies: list[str]
    commands: list[str]
    file_path: str
    line_number: int


@dataclass
class MakefileInventory:
    """Inventory of a Makefile's contents and structure."""

    file_path: str
    targets: dict[str, Target]
    variables: dict[str, str]
    includes: list[str]
    plugin_type: str  # "leaf" or "aggregator"


@dataclass
class AnalysisResult:
    """Results from analyzing a Makefile for completeness."""

    makefile: str
    score: int
    missing_essential: list[str]
    missing_recommended: list[str]
    anti_patterns: list[str]
    inconsistencies: list[str]
    recommendations: list[str]


class MakefileDogfooder:
    """Main orchestrator for makefile analysis and enhancement."""

    def __init__(
        self,
        root_dir: Path | None = None,
        verbose: bool = False,
        explain: bool = False,
    ) -> None:
        """Initialize the makefile dogfooder."""
        self.root_dir = root_dir or Path.cwd()
        self.inventory: dict[str, MakefileInventory] = {}
        self.analysis_results: list[AnalysisResult] = []
        self.verbose = verbose
        self.explain = explain

        # Standard target categories
        self.essential_targets = {
            "help": "Show available targets",
            "clean": "Clean build artifacts",
            ".PHONY": "Declare phony targets",
        }

        self.recommended_targets = {
            "test": "Run tests",
            "lint": "Run linting",
            "format": "Format code",
            "install": "Install dependencies",
            "status": "Show project status",
        }

        self.convenience_targets = {
            "demo": "Demonstrate functionality",
            "dogfood": "Test the plugin on itself",
            "check": "Run all validation checks",
            "dev-setup": "Set up development environment",
            "quick-test": "Run tests without coverage",
            "all": "Run default operations (test + lint)",
        }

    # Directories to skip during discovery (venvs, caches, worktrees)
    SKIP_DIRS = {
        ".venv",
        "venv",
        ".uv-cache",
        ".uv-tools",
        "__pycache__",
        ".worktrees",
        "node_modules",
        ".git",
        "build",
        "dist",
        ".tox",
        ".nox",
    }

    def _should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped (contains excluded directories)."""
        return any(skip_dir in path.parts for skip_dir in self.SKIP_DIRS)

    def _has_target_variant(self, target_names: set[str], base_name: str) -> bool:
        """Check if a target or its variants (prefix-*) exist.

        Recognizes patterns like:
        - "demo" matches "demo", "demo-skills", "demo-commit", etc.
        - "dogfood" matches "dogfood", "plugin-check" (common equivalent)
        """
        if base_name in target_names:
            return True

        # Check for prefix variants (demo-*, dogfood-*, etc.)
        prefix = f"{base_name}-"
        if any(t.startswith(prefix) for t in target_names):
            return True

        # Special case: "plugin-check" is equivalent to "dogfood"
        if base_name == "dogfood" and "plugin-check" in target_names:
            return True

        return False

    def discover_makefiles(self, scope: Scope) -> list[Path]:
        """Find all Makefiles based on scope, excluding venvs and caches."""
        makefiles = []

        if scope in [Scope.ROOT, Scope.ALL]:
            root_makefile = self.root_dir / "Makefile"
            if root_makefile.exists():
                makefiles.append(root_makefile)

        if scope in [Scope.PLUGINS, Scope.ALL]:
            plugins_dir = self.root_dir / "plugins"
            if plugins_dir.exists():
                for plugin_dir in plugins_dir.iterdir():
                    if plugin_dir.is_dir():
                        for makefile in plugin_dir.glob("**/Makefile"):
                            if not self._should_skip_path(makefile):
                                makefiles.append(makefile)
                        # Skip .mk files - they're include fragments, not standalone
                        # for mkfile in plugin_dir.glob("**/*.mk"):
                        #     makefiles.append(mkfile)

        return sorted(makefiles)

    def parse_makefile(self, makefile_path: Path) -> MakefileInventory:  # noqa: PLR0912
        """Parse a Makefile and extract targets, variables, and includes."""
        targets: dict[str, Target] = {}
        variables: dict[str, str] = {}
        includes: list[str] = []

        try:
            with open(makefile_path) as f:
                lines = f.readlines()
        except Exception:
            return MakefileInventory(str(makefile_path), {}, {}, [], "unknown")

        current_target: str | None = None
        line_number = 0

        for raw_line in lines:
            line_number += 1
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            # Extract includes (both required "include" and optional "-include")
            if line.startswith("include ") or line.startswith("-include "):
                new_includes = line.split()[1:]
                includes.extend(new_includes)
                if self.verbose:
                    print(f"  [verbose] {makefile_path}: includes: {new_includes}")

            # Extract variable assignments
            elif ":" in line and not line.startswith("\t"):
                # This could be a target or variable
                if line and not line[0].isspace():
                    parts = line.split(":", 1)
                    if len(parts) == TARGET_PARTS_COUNT:
                        potential_target = parts[0].strip()
                        # Check if it looks like a target (no = in name)
                        if "=" not in potential_target:
                            current_target = potential_target
                            desc = ""
                            # Look for description comment on previous line
                            if line_number > 1:
                                prev_line = lines[line_number - 2].strip()
                                if prev_line.startswith("##"):
                                    desc = prev_line[2:].strip()

                            targets[potential_target] = Target(
                                name=potential_target,
                                description=desc,
                                phony=False,  # Will check later
                                dependencies=(
                                    parts[1].strip().split() if parts[1].strip() else []
                                ),
                                commands=[],
                                file_path=str(makefile_path),
                                line_number=line_number,
                            )
                        else:
                            # Variable assignment
                            var_name, var_value = line.split("=", 1)
                            variables[var_name.strip()] = var_value.strip()

            # Extract commands for current target (check raw_line for tab)
            elif raw_line.startswith("\t") and current_target:
                if current_target in targets:
                    targets[current_target].commands.append(line)

        # Check .PHONY declaration - also creates placeholder for targets from includes
        if ".PHONY" in targets:
            phony_targets = targets[".PHONY"].dependencies
            for target_name, target in targets.items():
                if target_name in phony_targets:
                    target.phony = True
            # Create placeholders for targets declared in .PHONY but not defined locally
            # (these come from included .mk files)
            for phony_target in phony_targets:
                if phony_target not in targets:
                    targets[phony_target] = Target(
                        name=phony_target,
                        description="(from include)",
                        phony=True,
                        dependencies=[],
                        commands=[],
                        file_path=str(makefile_path),
                        line_number=0,  # Unknown, from include
                    )
                    if self.verbose:
                        print(f"  [verbose] {makefile_path}: PHONY: {phony_target}")

        # Determine plugin type
        plugin_type = "leaf"
        path_str = str(makefile_path)

        # Check if it's an auxiliary Makefile (in docs/ or tests/ subdirectory)
        # These don't need demo/dogfood targets
        if "/docs/" in path_str or "/tests/" in path_str:
            plugin_type = "auxiliary"
        elif "plugins" in path_str:
            # Check if it's an aggregator (delegates to other Makefiles)
            for target in targets.values():
                if any("$(MAKE) -C" in cmd for cmd in target.commands):
                    plugin_type = "aggregator"
                    break

        return MakefileInventory(
            file_path=str(makefile_path),
            targets=targets,
            variables=variables,
            includes=includes,
            plugin_type=plugin_type,
        )

    def analyze_makefile(self, inventory: MakefileInventory) -> AnalysisResult:  # noqa: PLR0912
        """Analyze a Makefile inventory and identify gaps."""
        score = 0
        score_breakdown: list[str] = []  # For --explain mode
        missing_essential: list[str] = []
        missing_recommended: list[str] = []
        anti_patterns: list[str] = []
        inconsistencies: list[str] = []
        recommendations: list[str] = []

        target_names = set(inventory.targets.keys())

        # Detect markdown-only plugins (no Python code, no test/lint/format needed)
        is_markdown_only = any("markdown-only" in inc for inc in inventory.includes)

        # Auxiliary Makefiles (docs/, tests/) also don't need full Python targets
        is_auxiliary = inventory.plugin_type == "auxiliary"

        # Detect catch-all pattern (e.g., Sphinx docs use %: to handle all targets)
        has_catchall = "%" in target_names

        # Check essential targets
        for essential, desc in self.essential_targets.items():
            # Auxiliary Makefiles with catch-all get credit for clean (handled by %)
            if essential == "clean" and is_auxiliary and has_catchall:
                score += 20
                score_breakdown.append(f"+20 essential '{essential}' (catch-all %)")
            elif essential not in target_names:
                missing_essential.append(f"{essential}: {desc}")
                score_breakdown.append(f"+0  essential '{essential}' MISSING")
            else:
                score += 20
                score_breakdown.append(f"+20 essential '{essential}'")

        # Check recommended targets (skip Python-specific for markdown-only/auxiliary)
        python_targets = {"test", "lint", "format", "install"}
        auxiliary_skip = {"status"}  # Auxiliary Makefiles don't need project overview
        for recommended, desc in self.recommended_targets.items():
            # Markdown-only/auxiliary plugins get auto-credit for Python targets
            if (is_markdown_only or is_auxiliary) and recommended in python_targets:
                score += 10
                reason = "md-only" if is_markdown_only else "aux"
                score_breakdown.append(f"+10 rec '{recommended}' (auto: {reason})")
            # Auxiliary Makefiles get credit for status they don't need
            elif is_auxiliary and recommended in auxiliary_skip:
                score += 10
                score_breakdown.append(f"+10 rec '{recommended}' (auto: aux)")
            elif recommended not in target_names:
                missing_recommended.append(f"{recommended}: {desc}")
                score_breakdown.append(f"+0  recommended '{recommended}' MISSING")
            else:
                score += 10
                score_breakdown.append(f"+10 recommended '{recommended}'")

        # Check convenience targets
        convenience_found = 0
        for convenience in self.convenience_targets:
            if convenience in target_names:
                convenience_found += 1
                score += 5
                score_breakdown.append(f"+5  convenience '{convenience}'")

        # Check for anti-patterns
        for target_name, target in inventory.targets.items():
            # Missing .PHONY declaration
            if not target.phony and not any(
                f in target_name.lower() for f in [".o", ".so", ".a"]
            ):
                anti_patterns.append(
                    f"Target '{target_name}' appears phony but not in .PHONY",
                )

            # Commands without error handling
            for cmd in target.commands:
                if not any(flag in cmd for flag in ["set -e", "-e", "||"]):
                    if not cmd.startswith("@echo") and not cmd.startswith("#"):
                        anti_patterns.append(
                            f"Command in '{target_name}' lacks error handling",
                        )

        # Check for help target quality
        if "help" in target_names:
            help_target = inventory.targets["help"]
            if len(help_target.commands) < MIN_HELP_COMMANDS:
                anti_patterns.append("Help target seems minimal or incomplete")

        # Generate recommendations based on plugin type
        # Skip demo/dogfood recommendations for auxiliary Makefiles (docs/, tests/)
        if inventory.plugin_type == "leaf":
            if not self._has_target_variant(target_names, "demo"):
                recommendations.append(
                    "Add 'demo' target to showcase plugin functionality",
                )
            if not self._has_target_variant(target_names, "dogfood"):
                recommendations.append(
                    "Add 'dogfood' or 'plugin-check' target for self-testing",
                )
        elif inventory.plugin_type == "aggregator":
            if "check-all" not in target_names:
                recommendations.append(
                    "Add 'check-all' target to run all plugin checks",
                )
        # auxiliary type: no demo/dogfood recommendations needed

        # Cap score at 100
        score = min(score, 100)

        # Output detailed scoring breakdown if explain mode is enabled
        if self.explain:
            print(f"\n  [explain] {inventory.file_path}")
            print(f"    Plugin type: {inventory.plugin_type}")
            print(f"    Includes: {inventory.includes or 'none'}")
            print("    Scoring breakdown:")
            for line in score_breakdown:
                print(f"      {line}")
            print(f"    Total: {score}/100 (capped)")

        return AnalysisResult(
            makefile=inventory.file_path,
            score=score,
            missing_essential=missing_essential,
            missing_recommended=missing_recommended,
            anti_patterns=anti_patterns,
            inconsistencies=inconsistencies,
            recommendations=recommendations,
        )

    def test_makefile(
        self,
        inventory: MakefileInventory,
        safe_mode: bool = True,
    ) -> dict[str, Any]:
        """Safely test a Makefile."""
        results: dict[str, Any] = {
            "file": inventory.file_path,
            "tests_run": 0,
            "tests_passed": 0,
            "issues": [],
            "warnings": [],
        }

        makefile_dir = Path(inventory.file_path).parent

        # Test 1: Makefile syntax
        try:
            subprocess.run(  # nosec B603
                ["/usr/bin/make", "-n", "help"],
                cwd=makefile_dir,
                capture_output=True,
                check=True,
                timeout=10,
            )
            results["tests_passed"] += 1
            results["tests_run"] += 1
        except subprocess.CalledProcessError as e:
            results["issues"].append(f"Syntax error or help target missing: {e}")
            results["tests_run"] += 1
        except subprocess.TimeoutExpired:
            results["warnings"].append("Help target took too long to dry-run")

        # Test 2: Check if essential targets respond
        for target_name in ["help", "status"]:
            if target_name in inventory.targets:
                try:
                    # nosec: S603 - Using absolute path to /usr/bin/make, target is validated against inventory.targets
                    subprocess.run(  # nosec B603
                        ["/usr/bin/make", "-n", target_name],
                        cwd=makefile_dir,
                        capture_output=True,
                        check=True,
                        timeout=5,
                    )
                    results["tests_passed"] += 1
                    results["tests_run"] += 1
                except subprocess.CalledProcessError:
                    results["issues"].append(
                        f"Target '{target_name}' failed dry-run",
                    )
                    results["tests_run"] += 1
                except subprocess.TimeoutExpired:
                    results["warnings"].append(
                        f"Target '{target_name}' took too long to dry-run",
                    )

        # Test 3: Check for undefined variables in critical targets
        critical_targets = ["help", "clean", "test", "lint"]
        for target_name in critical_targets:
            if target_name in inventory.targets:
                target_entry = inventory.targets[target_name]
                for cmd in target_entry.commands:
                    # Look for variable references
                    vars_in_cmd = re.findall(r"\$\([A-Z_]+\)", cmd)
                    for var_ref in vars_in_cmd:
                        var_name = var_ref[2:-1]  # Remove $() wrapper
                        if var_name not in inventory.variables:
                            msg = (
                                f"Variable '{var_name}' in target '{target_name}' "
                                f"may be undefined"
                            )
                            results["warnings"].append(msg)

        return results

    def generate_missing_targets(
        self,
        inventory: MakefileInventory,
        analysis: AnalysisResult,
    ) -> list[str]:
        """Generate Makefile content for missing targets."""
        generated = []

        if analysis.missing_essential:
            generated.append("\n# Essential targets (auto-generated)")
            for missing in analysis.missing_essential:
                target_name = missing.split(":")[0]
                if target_name == ".PHONY":
                    generated.append(".PHONY: help clean test lint all")
                elif target_name == "help":
                    generated.append(self._generate_help_target(inventory))

        target_names = set(inventory.targets.keys())

        if inventory.plugin_type == "leaf":
            # Add demo target if no demo variant exists
            if not self._has_target_variant(target_names, "demo"):
                generated.append("\n# Demo target (auto-generated)")
                generated.append(self._generate_demo_target(inventory))

            # Add dogfood target if no dogfood/plugin-check variant exists
            if not self._has_target_variant(target_names, "dogfood"):
                generated.append("\n# Dogfood target (auto-generated)")
                generated.append(self._generate_dogfood_target(inventory))

        elif inventory.plugin_type == "aggregator":
            # Add check-all target if missing
            if "check-all" not in inventory.targets:
                generated.append("\n# Check all plugins (auto-generated)")
                generated.append(self._generate_check_all_target(inventory))

        return generated

    def _generate_help_target(self, inventory: MakefileInventory) -> str:
        """Generate a help target."""
        return (
            "help: ## Show this help message\n"
            '\t@echo ""\n'
            '\t@echo "$$(basename $$(pwd)) - Available Targets"\n'
            '\t@echo "=================================="\n'
            "\t@awk -F':.*?## ' '/^[a-zA-Z_-]+:.*?## / "
            '{printf "  %-15s %s\\\\n", $$1, $$2}\' $$(MAKEFILE_LIST)"'
        )

    def _generate_demo_target(self, inventory: MakefileInventory) -> str:
        """Generate a demo target for leaf plugins."""
        plugin_name = Path(inventory.file_path).parent.name
        return f"""demo: ## Demonstrate {plugin_name} plugin functionality
\t@echo "=== Demonstrating {plugin_name} Plugin ==="
\t@echo "This plugin provides:"
\t@echo "  - Core functionality for {plugin_name}"
\t@echo "  - Integration with Claude Code"
\t@echo ""
\t@echo "Try these targets:"
\t@echo "  make test    # Run tests"
\t@echo "  make lint    # Check code quality"
\t@echo "  make help    # See all options" """

    def _generate_dogfood_target(self, inventory: MakefileInventory) -> str:
        """Generate a dogfood target for self-testing."""
        plugin_name = Path(inventory.file_path).parent.name
        return f"""dogfood: ## Test {plugin_name} plugin on itself
\t@echo "=== Dogfooding {plugin_name} Plugin ==="
\t@echo "Running self-tests..."
\t$$(MAKE) test
\t@echo ""
\t@echo "Running linting..."
\t$$(MAKE) lint
\t@echo ""
\t@echo "Validating structure..."
\t@if [ -f scripts/validate-plugin.py ]; then \\
\t\tpython3 scripts/validate-plugin.py .; \\
\tfi
\t@echo ""
\t@echo "OK All dogfood tests completed!" """

    def _generate_check_all_target(self, inventory: MakefileInventory) -> str:
        """Generate a check-all target for aggregator Makefiles."""
        return """check-all: ## Run checks across all plugins
\t@echo "=== Running All Plugin Checks ==="
\t@for plugin in $$(PLUGINS); do \\
\t\techo ""; \\
\t\techo ">>> Checking $$plugin"; \\
\t\t$$(MAKE) -C $$plugin plugin-check 2>/dev/null || echo "  (plugin-check failed)"; \\
\tdone
\t@echo ""
\t@echo "=== All Plugin Checks Complete ===" """

    def run(
        self,
        scope: Scope,
        mode: Mode,
        plugin_filter: str | None = None,
    ) -> dict[str, Any]:
        """Orchestrate the makefile analysis process."""
        results: dict[str, Any] = {
            "scope": scope.value,
            "mode": mode.value,
            "makefiles_analyzed": 0,
            "issues_found": 0,
            "recommendations_made": 0,
            "generated_targets": [],
            "details": [],
        }

        # Discovery
        makefiles = self.discover_makefiles(scope)
        if plugin_filter:
            makefiles = [m for m in makefiles if plugin_filter in str(m)]

        # Build inventory
        for makefile in makefiles:
            inventory = self.parse_makefile(makefile)
            self.inventory[inventory.file_path] = inventory

        results["makefiles_analyzed"] = len(self.inventory)

        # Analysis
        if mode in [Mode.ANALYZE, Mode.FULL]:
            for inventory in self.inventory.values():
                analysis = self.analyze_makefile(inventory)
                self.analysis_results.append(analysis)
                results["details"].append(
                    {
                        "file": inventory.file_path,
                        "score": analysis.score,
                        "issues": len(analysis.anti_patterns)
                        + len(analysis.missing_essential),
                        "recommendations": len(analysis.recommendations),
                    },
                )
                results["issues_found"] += len(analysis.anti_patterns) + len(
                    analysis.missing_essential,
                )
                results["recommendations_made"] += len(analysis.recommendations)

        # Testing
        if mode in [Mode.TEST, Mode.FULL]:
            for inventory in self.inventory.values():
                test_results = self.test_makefile(inventory)
                # Add test results to details
                for detail in results["details"]:
                    if detail["file"] == inventory.file_path:
                        detail["test_results"] = test_results
                        break

        # Generation
        if mode == Mode.FULL:
            for inventory in self.inventory.values():
                matched_analysis = next(
                    (
                        a
                        for a in self.analysis_results
                        if a.makefile == inventory.file_path
                    ),
                    None,
                )
                if matched_analysis:
                    generated = self.generate_missing_targets(
                        inventory,
                        matched_analysis,
                    )
                    if generated:
                        results["generated_targets"].append(
                            {
                                "file": inventory.file_path,
                                "content": "\n".join(generated),
                            },
                        )

        return results


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze and enhance Makefiles for complete functionality",
    )
    parser.add_argument(
        "--scope",
        choices=["root", "plugins", "all"],
        default="all",
        help="Scope of analysis",
    )
    parser.add_argument(
        "--mode",
        choices=["analyze", "test", "full"],
        default="full",
        help="Operation mode",
    )
    parser.add_argument("--plugin", help="Restrict to specific plugin")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply generated changes to Makefiles",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output (include discovery, PHONY recognition)",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Show detailed scoring breakdown for each Makefile",
    )

    args = parser.parse_args()

    dogfooder = MakefileDogfooder(verbose=args.verbose, explain=args.explain)
    results = dogfooder.run(
        scope=Scope(args.scope),
        mode=Mode(args.mode),
        plugin_filter=args.plugin,
    )

    if args.output == "json":
        import json

        print(json.dumps(results, indent=2))
    else:
        # Text output
        print("\n=== Makefile Dogfooding Report ===")
        print(f"Scope: {results['scope']}")
        print(f"Mode: {results['mode']}")
        print(f"Makefiles analyzed: {results['makefiles_analyzed']}")
        print(f"Issues found: {results['issues_found']}")
        print(f"Recommendations: {results['recommendations_made']}")

        if results.get("details"):
            print("\n--- Makefile Details ---")
            for detail in results["details"]:
                score = detail.get("score", 0)
                status = "[OK]" if score >= 60 else "[WARN]" if score >= 40 else "[FIX]"
                print(f"\n{status} {detail['file']}")
                print(f"    Score: {score}/100")
                print(f"    Issues: {detail.get('issues', 0)}")
                print(f"    Recommendations: {detail.get('recommendations', 0)}")
                if "test_results" in detail:
                    tr = detail["test_results"]
                    passed = tr.get("tests_passed", 0)
                    total = tr.get("tests_run", 0)
                    print(f"    Tests: {passed}/{total} passed")
                    if tr.get("issues"):
                        for issue in tr["issues"][:3]:
                            print(f"      - {issue}")

        if results.get("generated_targets"):
            print("\n--- Generated Targets ---")
            for gen in results["generated_targets"]:
                print(f"\n{gen['file']}:")
                content = gen["content"]
                preview = content[:200] + "..." if len(content) > 200 else content
                print(preview)

    # Apply changes if requested
    if args.apply and results.get("generated_targets"):
        for gen in results["generated_targets"]:
            with open(gen["file"], "a") as f:
                f.write("\n" + gen["content"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
