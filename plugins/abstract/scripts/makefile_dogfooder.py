#!/usr/bin/env python3
"""
Makefile Dogfooder - Analyze and enhance Makefiles for complete user functionality

This script orchestrates the makefile-dogfooder skill workflow:
1. Discovery - Find and inventory Makefiles
2. Analysis - Identify gaps and anti-patterns
3. Testing - Safely validate existing targets
4. Generation - Create missing targets with templates
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class Scope(Enum):
    ROOT = "root"
    PLUGINS = "plugins"
    ALL = "all"


class Mode(Enum):
    ANALYZE = "analyze"
    TEST = "test"
    FULL = "full"


class TargetType(Enum):
    SAFE = "safe"      # Always safe to run (help, status)
    CONDITIONAL = "conditional"  # Requires inspection (test, lint)
    RISKY = "risky"    # Never run in CI (clean, install)


@dataclass
class Target:
    name: str
    description: str
    phony: bool
    dependencies: List[str]
    commands: List[str]
    file_path: str
    line_number: int


@dataclass
class MakefileInventory:
    file_path: str
    targets: Dict[str, Target]
    variables: Dict[str, str]
    includes: List[str]
    plugin_type: str  # "leaf" or "aggregator"


@dataclass
class AnalysisResult:
    makefile: str
    score: int
    missing_essential: List[str]
    missing_recommended: List[str]
    anti_patterns: List[str]
    inconsistencies: List[str]
    recommendations: List[str]


class MakefileDogfooder:
    """Main orchestrator for makefile analysis and enhancement"""

    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir or Path.cwd()
        self.inventory: Dict[str, MakefileInventory] = {}
        self.analysis_results: List[AnalysisResult] = []

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

    def discover_makefiles(self, scope: Scope) -> List[Path]:
        """Find all Makefiles based on scope"""
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
                            makefiles.append(makefile)
                        for mkfile in plugin_dir.glob("**/*.mk"):
                            makefiles.append(mkfile)

        return sorted(makefiles)

    def parse_makefile(self, makefile_path: Path) -> MakefileInventory:
        """Parse a Makefile and extract targets, variables, and includes"""
        targets = {}
        variables = {}
        includes = []

        try:
            with open(makefile_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {makefile_path}: {e}")
            return MakefileInventory(str(makefile_path), {}, {}, [], "unknown")

        current_target = None
        line_number = 0

        for line in lines:
            line_number += 1
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            # Extract includes
            if line.startswith('include '):
                includes.extend(line.split()[1:])

            # Extract variable assignments
            elif ':' in line and not line.startswith('\t'):
                # This could be a target or variable
                if line and not line[0].isspace():
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        potential_target = parts[0].strip()
                        # Check if it looks like a target (no = in name)
                        if '=' not in potential_target:
                            current_target = potential_target
                            desc = ""
                            # Look for description comment on previous line
                            if line_number > 1:
                                prev_line = lines[line_number-2].strip()
                                if prev_line.startswith('##'):
                                    desc = prev_line[2:].strip()

                            targets[potential_target] = Target(
                                name=potential_target,
                                description=desc,
                                phony=False,  # Will check later
                                dependencies=parts[1].strip().split() if parts[1].strip() else [],
                                commands=[],
                                file_path=str(makefile_path),
                                line_number=line_number
                            )
                        else:
                            # Variable assignment
                            var_name, var_value = line.split('=', 1)
                            variables[var_name.strip()] = var_value.strip()

            # Extract commands for current target
            elif line.startswith('\t') and current_target:
                if current_target in targets:
                    targets[current_target].commands.append(line[1:].strip())

        # Check .PHONY declaration
        if '.PHONY' in targets:
            phony_targets = targets['.PHONY'].dependencies
            for target_name in targets:
                if target_name in phony_targets:
                    targets[target_name].phony = True

        # Determine plugin type
        plugin_type = "leaf"
        if "plugins" in str(makefile_path):
            # Check if it's an aggregator (delegates to other Makefiles)
            for target in targets.values():
                if any('$(MAKE) -C' in cmd for cmd in target.commands):
                    plugin_type = "aggregator"
                    break

        return MakefileInventory(
            file_path=str(makefile_path),
            targets=targets,
            variables=variables,
            includes=includes,
            plugin_type=plugin_type
        )

    def analyze_makefile(self, inventory: MakefileInventory) -> AnalysisResult:
        """Analyze a Makefile inventory and identify gaps"""
        score = 0
        missing_essential = []
        missing_recommended = []
        anti_patterns = []
        inconsistencies = []
        recommendations = []

        target_names = set(inventory.targets.keys())

        # Check essential targets
        for essential, desc in self.essential_targets.items():
            if essential not in target_names:
                missing_essential.append(f"{essential}: {desc}")
            else:
                score += 20

        # Check recommended targets
        for recommended, desc in self.recommended_targets.items():
            if recommended not in target_names:
                missing_recommended.append(f"{recommended}: {desc}")
            else:
                score += 10

        # Check convenience targets
        convenience_found = 0
        for convenience, desc in self.convenience_targets.items():
            if convenience in target_names:
                convenience_found += 1
                score += 5

        # Check for anti-patterns
        for target_name, target in inventory.targets.items():
            # Missing .PHONY declaration
            if not target.phony and not any(f in target_name.lower() for f in ['.o', '.so', '.a']):
                anti_patterns.append(f"Target '{target_name}' appears to be phony but not declared in .PHONY")

            # Commands without error handling
            for cmd in target.commands:
                if not any(flag in cmd for flag in ['set -e', '-e', '||']):
                    if not cmd.startswith('@echo') and not cmd.startswith('#'):
                        anti_patterns.append(f"Command in '{target_name}' lacks error handling: {cmd[:50]}...")

        # Check for help target quality
        if 'help' in target_names:
            help_target = inventory.targets['help']
            if len(help_target.commands) < 3:
                anti_patterns.append("Help target seems minimal or incomplete")

        # Generate recommendations
        if inventory.plugin_type == "leaf":
            if "demo" not in target_names:
                recommendations.append("Add 'demo' target to showcase plugin functionality")
            if "dogfood" not in target_names:
                recommendations.append("Add 'dogfood' target for self-testing")
        else:
            if "check-all" not in target_names:
                recommendations.append("Add 'check-all' target to run all plugin checks")

        # Cap score at 100
        score = min(score, 100)

        return AnalysisResult(
            makefile=inventory.file_path,
            score=score,
            missing_essential=missing_essential,
            missing_recommended=missing_recommended,
            anti_patterns=anti_patterns,
            inconsistencies=inconsistencies,
            recommendations=recommendations
        )

    def test_makefile(self, inventory: MakefileInventory, safe_mode: bool = True) -> Dict[str, Any]:
        """Safely test a Makefile"""
        results = {
            "file": inventory.file_path,
            "tests_run": 0,
            "tests_passed": 0,
            "issues": [],
            "warnings": []
        }

        makefile_dir = Path(inventory.file_path).parent

        # Test 1: Makefile syntax
        try:
            subprocess.run(
                ["make", "-n", "help"],
                cwd=makefile_dir,
                capture_output=True,
                check=True,
                timeout=10
            )
            results["tests_passed"] += 1
            results["tests_run"] += 1
        except subprocess.CalledProcessError as e:
            results["issues"].append(f"Syntax error or help target missing: {e}")
            results["tests_run"] += 1
        except subprocess.TimeoutExpired:
            results["warnings"].append("Help target took too long to dry-run")

        # Test 2: Check if essential targets respond
        for target in ["help", "status"]:
            if target in inventory.targets:
                try:
                    subprocess.run(
                        ["make", "-n", target],
                        cwd=makefile_dir,
                        capture_output=True,
                        check=True,
                        timeout=5
                    )
                    results["tests_passed"] += 1
                    results["tests_run"] += 1
                except subprocess.CalledProcessError:
                    results["issues"].append(f"Target '{target}' failed dry-run")
                    results["tests_run"] += 1
                except subprocess.TimeoutExpired:
                    results["warnings"].append(f"Target '{target}' took too long to dry-run")

        # Test 3: Check for undefined variables in critical targets
        critical_targets = ["help", "clean", "test", "lint"]
        for target_name in critical_targets:
            if target_name in inventory.targets:
                target = inventory.targets[target_name]
                for cmd in target.commands:
                    # Look for variable references
                    import re
                    vars_in_cmd = re.findall(r'\$\([A-Z_]+\)', cmd)
                    for var_ref in vars_in_cmd:
                        var_name = var_ref[2:-1]  # Remove $() wrapper
                        if var_name not in inventory.variables:
                            results["warnings"].append(
                                f"Variable '{var_name}' used in target '{target_name}' may be undefined"
                            )

        return results

    def generate_missing_targets(self, inventory: MakefileInventory, analysis: AnalysisResult) -> List[str]:
        """Generate Makefile content for missing targets"""
        generated = []

        if analysis.missing_essential:
            generated.append("\n# Essential targets (auto-generated)")
            for missing in analysis.missing_essential:
                target_name = missing.split(':')[0]
                if target_name == ".PHONY":
                    generated.append(".PHONY: help clean test lint all")
                elif target_name == "help":
                    generated.append(self._generate_help_target(inventory))

        if inventory.plugin_type == "leaf":
            # Add demo target if missing
            if "demo" not in inventory.targets:
                generated.append("\n# Demo target (auto-generated)")
                generated.append(self._generate_demo_target(inventory))

            # Add dogfood target if missing
            if "dogfood" not in inventory.targets:
                generated.append("\n# Dogfood target (auto-generated)")
                generated.append(self._generate_dogfood_target(inventory))

        elif inventory.plugin_type == "aggregator":
            # Add check-all target if missing
            if "check-all" not in inventory.targets:
                generated.append("\n# Check all plugins (auto-generated)")
                generated.append(self._generate_check_all_target(inventory))

        return generated

    def _generate_help_target(self, inventory: MakefileInventory) -> str:
        """Generate a help target"""
        return """help: ## Show this help message
\t@echo ""
\t@echo "$$(basename $$(pwd)) - Available Targets"
\t@echo "=================================="
\t@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\\n", $$1, $$2}' $$(MAKEFILE_LIST)"""

    def _generate_demo_target(self, inventory: MakefileInventory) -> str:
        """Generate a demo target for leaf plugins"""
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
        """Generate a dogfood target for self-testing"""
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
\t@echo "✓ All dogfood tests completed!" """

    def _generate_check_all_target(self, inventory: MakefileInventory) -> str:
        """Generate a check-all target for aggregator Makefiles"""
        return """check-all: ## Run checks across all plugins
\t@echo "=== Running All Plugin Checks ==="
\t@for plugin in $$(PLUGINS); do \\
\t\techo ""; \\
\t\techo ">>> Checking $$plugin"; \\
\t\t$$(MAKE) -C $$plugin plugin-check 2>/dev/null || echo "  (plugin-check failed)"; \\
\tdone
\t@echo ""
\t@echo "=== All Plugin Checks Complete ===" """

    def run(self, scope: Scope, mode: Mode, plugin_filter: Optional[str] = None) -> Dict[str, Any]:
        """Main orchestration method"""
        results = {
            "scope": scope.value,
            "mode": mode.value,
            "makefiles_analyzed": 0,
            "issues_found": 0,
            "recommendations_made": 0,
            "generated_targets": [],
            "details": []
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
                results["details"].append({
                    "file": inventory.file_path,
                    "score": analysis.score,
                    "issues": len(analysis.anti_patterns) + len(analysis.missing_essential),
                    "recommendations": len(analysis.recommendations)
                })
                results["issues_found"] += len(analysis.anti_patterns) + len(analysis.missing_essential)
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
                analysis = next((a for a in self.analysis_results if a.makefile == inventory.file_path), None)
                if analysis:
                    generated = self.generate_missing_targets(inventory, analysis)
                    if generated:
                        results["generated_targets"].append({
                            "file": inventory.file_path,
                            "content": "\n".join(generated)
                        })

        return results


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze and enhance Makefiles for complete functionality"
    )
    parser.add_argument(
        "--scope",
        choices=["root", "plugins", "all"],
        default="all",
        help="Scope of analysis"
    )
    parser.add_argument(
        "--mode",
        choices=["analyze", "test", "full"],
        default="full",
        help="Operation mode"
    )
    parser.add_argument(
        "--plugin",
        help="Restrict to specific plugin"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply generated changes to Makefiles"
    )

    args = parser.parse_args()

    dogfooder = MakefileDogfooder()
    results = dogfooder.run(
        scope=Scope(args.scope),
        mode=Mode(args.mode),
        plugin_filter=args.plugin
    )

    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        # Text output
        print(f"\n=== Makefile Dogfooding Results ===")
        print(f"Scope: {results['scope']}")
        print(f"Mode: {results['mode']}")
        print(f"Makefiles analyzed: {results['makefiles_analyzed']}")
        print(f"Issues found: {results['issues_found']}")
        print(f"Recommendations made: {results['recommendations_made']}")

        if results.get('details'):
            print("\n=== Details ===")
            for detail in results['details']:
                print(f"\nFile: {detail['file']}")
                print(f"Score: {detail['score']}/100")
                print(f"Issues: {detail['issues']}")
                print(f"Recommendations: {detail['recommendations']}")
                if 'test_results' in detail:
                    tr = detail['test_results']
                    print(f"Tests: {tr['tests_passed']}/{tr['tests_run']} passed")

        if results.get('generated_targets'):
            print("\n=== Generated Targets ===")
            for gen in results['generated_targets']:
                print(f"\n{gen['file']}:")
                print(gen['content'])

    # Apply changes if requested
    if args.apply and results.get('generated_targets'):
        print("\n=== Applying Changes ===")
        for gen in results['generated_targets']:
            print(f"Appending to {gen['file']}...")
            with open(gen['file'], 'a') as f:
                f.write("\n" + gen['content'])
        print("Done!")

    return 0


if __name__ == "__main__":
    sys.exit(main())