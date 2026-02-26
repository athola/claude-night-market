#!/usr/bin/env python3
"""Meta-evaluation of evaluation-related skills and frameworks.

This script validates that evaluation-related skills follow their own quality
standards, preventing cargo cult patterns and ensuring recursive validation.

Checks:
- Evaluation skills have tests validating their quality criteria
- Documentation follows the standards it defines
- Verification steps exist after code examples
- TOCs exist for long modules (>100 lines)
- Anti-cargo cult patterns are enforced
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


class MetaEvaluator:
    """Validate that evaluation skills meet their own standards."""

    # Evaluation skills from the inventory
    EVALUATION_SKILLS = {
        # Abstract plugin
        "abstract": ["skills-eval", "hooks-eval", "modular-skills", "subagent-testing"],
        # Imbue plugin
        "imbue": [
            "proof-of-work",
            "review-core",
            "structured-output",
        ],
        # Leyline plugin
        "leyline": [
            "evaluation-framework",
            "testing-quality-standards",
            "pytest-config",
        ],
        # Pensive plugin (review skills)
        "pensive": [
            "test-review",
            "api-review",
            "architecture-review",
            "bug-review",
        ],
        # Sanctum plugin (validation skills)
        "sanctum": ["pr-review", "test-updates", "git-workspace-review"],
        # Parseltongue plugin (testing skills)
        "parseltongue": ["python-testing", "python-performance"],
        # Conserve plugin (quality skills)
        "conserve": ["code-quality-principles", "context-optimization"],
    }

    def __init__(self, plugins_root: Path, verbose: bool = False):
        self.plugins_root = plugins_root
        self.verbose = verbose
        self.issues: list[dict[str, Any]] = []

    def check_file_exists(self, skill_path: Path) -> bool:
        """Check if skill SKILL.md exists."""
        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            return False
        return True

    def read_skill_content(self, skill_path: Path) -> str | None:
        """Read skill content from SKILL.md."""
        skill_file = skill_path / "SKILL.md"
        try:
            with skill_file.open(encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            if self.verbose:
                print(f"[ERROR] Failed to read {skill_file}: {e}")
            return None

    def check_toc_exists(self, content: str, skill_name: str) -> bool:
        """Check if skill has Table of Contents."""
        has_toc = (
            "## Table of Contents" in content or "table of contents" in content.lower()
        )

        if not has_toc:
            # Check if content is long enough to warrant TOC
            line_count = len(content.split("\n"))
            if line_count > 100:
                self.issues.append(
                    {
                        "type": "missing_toc",
                        "skill": skill_name,
                        "severity": "medium",
                        "message": f"Skill has {line_count} lines but no TOC",
                        "fix": "Add Table of Contents after frontmatter for navigation",
                    }
                )
                return False

        return True

    def check_verification_steps(self, content: str, skill_name: str) -> bool:
        """Check if code examples include verification steps."""
        # Look for code blocks
        code_blocks = re.findall(r"```[\w]*\n([^`]+)```", content, re.MULTILINE)

        if not code_blocks:
            return True  # No code blocks to verify

        # Check for verification patterns after code blocks
        has_verification = (
            "verification" in content.lower() or "verify" in content.lower()
        )

        if not has_verification and len(code_blocks) > 2:
            self.issues.append(
                {
                    "type": "missing_verification",
                    "skill": skill_name,
                    "severity": "medium",
                    "message": f"Skill has {len(code_blocks)} code blocks but no verification steps",
                    "fix": 'Add "**Verification:** Run `command` to verify" after examples',
                }
            )
            return False

        return True

    def check_concrete_quick_start(self, content: str, skill_name: str) -> bool:
        """Check if Quick Start has concrete commands, not abstract descriptions."""
        # Look for Quick Start section
        quick_start_match = re.search(
            r"## Quick Start\s+(.*?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE
        )

        if not quick_start_match:
            return True  # No Quick Start section

        quick_start_content = quick_start_match.group(1)

        # Check for concrete indicators (code blocks, commands)
        has_concrete = (
            "```" in quick_start_content
            or "python" in quick_start_content.lower()
            or "bash" in quick_start_content.lower()
            or "`" in quick_start_content
        )

        # Check for abstract indicators (should, configure, set up)
        is_abstract = (
            "should " in quick_start_content.lower()
            or "configure " in quick_start_content.lower()
            and "python" not in quick_start_content.lower()
        )

        if is_abstract and not has_concrete:
            self.issues.append(
                {
                    "type": "abstract_quick_start",
                    "skill": skill_name,
                    "severity": "high",
                    "message": "Quick Start uses abstract descriptions instead of concrete commands",
                    "fix": "Replace 'Configure X' with 'Run `command` to configure X'",
                }
            )
            return False

        return True

    def check_quality_criteria_defined(self, content: str, skill_name: str) -> bool:
        """Check if evaluation skill defines quality criteria."""
        # Look for quality-related terms
        quality_terms = [
            "quality",
            "criteria",
            "standard",
            "threshold",
            "metric",
            "scor",
            "evaluat",
        ]

        has_quality = any(term in content.lower() for term in quality_terms)

        if not has_quality:
            self.issues.append(
                {
                    "type": "missing_quality_criteria",
                    "skill": skill_name,
                    "severity": "high",
                    "message": "Evaluation skill doesn't define quality criteria or scoring",
                    "fix": "Add quality criteria, scoring rubric, or evaluation thresholds",
                }
            )
            return False

        return True

    def check_anti_cargo_cult(self, content: str, skill_name: str) -> bool:
        """Check if skill documents anti-cargo-cult patterns."""
        # For evaluation skills, check if they warn about common anti-patterns
        anti_pattern_terms = [
            "anti-pattern",
            "cargo cult",
            "testing theater",
            "abstract",
            "verification",
        ]

        has_anti_cargo_cult = any(
            term in content.lower() for term in anti_pattern_terms
        )

        if not has_anti_cargo_cult:
            # Only report as issue in verbose mode (low severity)
            if self.verbose:
                self.issues.append(
                    {
                        "type": "missing_anti_cargo_cult",
                        "skill": skill_name,
                        "severity": "low",
                        "message": "Evaluation skill doesn't document anti-cargo-cult patterns",
                        "fix": "Add section warning against testing theater and abstract documentation",
                    }
                )
            return False

        return True

    def check_tests_exist(self, plugin: str, skill: str) -> bool:
        """Check if skill has corresponding test file."""
        # Convert skill name (with hyphens) to test file name (with underscores)
        test_name = skill.replace("-", "_")

        # Look for test file patterns
        test_patterns = [
            self.plugins_root
            / plugin
            / "tests"
            / "unit"
            / "skills"
            / f"test_{test_name}.py",
            self.plugins_root / plugin / "tests" / f"test_{test_name}.py",
            self.plugins_root / plugin / "tests" / "unit" / f"test_{test_name}.py",
        ]

        for test_path in test_patterns:
            if test_path.exists():
                return True

        # For critical evaluation skills, missing tests is a high severity issue
        critical_skills = {
            "abstract": ["skills-eval", "hooks-eval", "modular-skills"],
            "imbue": ["proof-of-work"],
            "leyline": ["evaluation-framework", "testing-quality-standards"],
        }

        if plugin in critical_skills and skill in critical_skills[plugin]:
            self.issues.append(
                {
                    "type": "missing_tests",
                    "skill": f"{plugin}:{skill}",
                    "severity": "high",
                    "message": "Critical evaluation skill lacks BDD test validation",
                    "fix": f"Create tests/unit/skills/test_{skill}.py with quality checks",
                }
            )
            return False

        return True

    def evaluate_skill(self, plugin: str, skill: str) -> dict[str, Any]:
        """Evaluate a single evaluation skill."""
        skill_path = self.plugins_root / plugin / "skills" / skill

        results: dict[str, Any] = {
            "plugin": plugin,
            "skill": skill,
            "path": str(skill_path),
            "checks": {},
            "issues": [],
        }

        # Check if skill exists
        if not self.check_file_exists(skill_path):
            results["checks"]["exists"] = False
            self.issues.append(
                {
                    "type": "missing_skill",
                    "skill": f"{plugin}:{skill}",
                    "severity": "critical",
                    "message": "Skill directory not found",
                    "fix": "Create skill directory with SKILL.md",
                }
            )
            return results

        results["checks"]["exists"] = True

        # Read content
        content = self.read_skill_content(skill_path)
        if content is None:
            return results

        # Run checks
        results["checks"]["toc"] = self.check_toc_exists(content, f"{plugin}:{skill}")
        results["checks"]["verification"] = self.check_verification_steps(
            content, f"{plugin}:{skill}"
        )
        results["checks"]["concrete_quick_start"] = self.check_concrete_quick_start(
            content, f"{plugin}:{skill}"
        )
        results["checks"]["quality_criteria"] = self.check_quality_criteria_defined(
            content, f"{plugin}:{skill}"
        )
        results["checks"]["anti_cargo_cult"] = self.check_anti_cargo_cult(
            content, f"{plugin}:{skill}"
        )
        results["checks"]["tests_exist"] = self.check_tests_exist(plugin, skill)

        return results

    def evaluate_all(self) -> dict[str, Any]:
        """Evaluate all evaluation skills."""
        all_results: dict[str, Any] = {
            "skills_evaluated": 0,
            "skills_passed": 0,
            "skills_with_issues": 0,
            "total_issues": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "results": [],
        }

        for plugin, skills in self.EVALUATION_SKILLS.items():
            for skill in skills:
                result = self.evaluate_skill(plugin, skill)
                all_results["results"].append(result)
                all_results["skills_evaluated"] += 1

                # Count issues for this skill
                skill_issues = [
                    i for i in self.issues if i["skill"] == f"{plugin}:{skill}"
                ]
                if skill_issues:
                    all_results["skills_with_issues"] += 1
                    all_results["total_issues"] += len(skill_issues)
                    for issue in skill_issues:
                        severity = issue.get("severity", "low")
                        all_results["by_severity"][severity] += 1
                else:
                    all_results["skills_passed"] += 1

        return all_results

    def print_results(self, results: dict[str, Any]) -> None:
        """Print evaluation results."""
        print("\n" + "=" * 60)
        print("META-EVALUATION RESULTS")
        print("=" * 60)

        # Show which plugins are being evaluated
        plugins_evaluated = list(self.EVALUATION_SKILLS.keys())
        print(f"\nPlugins: {', '.join(plugins_evaluated)}")

        # Summary
        print(f"\nSkills Evaluated: {results['skills_evaluated']}")
        print(f"Skills Passed: {results['skills_passed']}")
        print(f"Skills with Issues: {results['skills_with_issues']}")
        print(f"\nTotal Issues: {results['total_issues']}")

        # By severity
        print("\nIssues by Severity:")
        for severity, count in results["by_severity"].items():
            if count > 0:
                print(f"  {severity.upper()}: {count}")

        # Individual skill results
        if self.verbose or results["total_issues"] > 0:
            print("\n" + "=" * 60)
            print("DETAILED RESULTS")
            print("=" * 60)

            for result in results["results"]:
                skill_name = f"{result['plugin']}:{result['skill']}"
                skill_issues = [i for i in self.issues if i["skill"] == skill_name]

                if skill_issues:
                    print(f"\n{skill_name}:")
                    for issue in skill_issues:
                        severity = issue.get("severity", "low").upper()
                        print(f"  [{severity}] {issue['message']}")
                        if "fix" in issue:
                            print(f"    → Fix: {issue['fix']}")

    def print_summary(self, results: dict[str, Any]) -> None:
        """Print summary and recommendations."""
        print("\n" + "=" * 60)
        print("SUMMARY & RECOMMENDATIONS")
        print("=" * 60)

        if results["total_issues"] == 0:
            print("\n✅ All evaluation skills meet quality standards!")
            print("\nRecursive validation is working correctly.")
            return

        # Critical issues
        if results["by_severity"]["critical"] > 0:
            print(
                f"\n🔴 CRITICAL: {results['by_severity']['critical']} critical issues found"
            )
            print("   These indicate evaluation skills are missing or broken.")
            print("   Action: Create or fix these skills immediately.")

        # High issues
        if results["by_severity"]["high"] > 0:
            print(f"\n🟠 HIGH: {results['by_severity']['high']} high-priority issues")
            print("   These indicate quality standards are not being met.")
            print(
                "   Action: Add missing quality criteria, tests, or concrete examples."
            )

        # Medium issues
        if results["by_severity"]["medium"] > 0:
            print(
                f"\n🟡 MEDIUM: {results['by_severity']['medium']} medium-priority issues"
            )
            print("   These affect navigation and documentation quality.")
            print("   Action: Add TOCs for long modules, include verification steps.")

        # Low issues
        if results["by_severity"]["low"] > 0:
            print(f"\n🔵 LOW: {results['by_severity']['low']} low-priority issues")
            print("   These are improvements to anti-cargo-cult documentation.")
            print("   Action: Add anti-pattern warnings to prevent cargo cult.")

        # Pass rate
        pass_rate = (
            (results["skills_passed"] / results["skills_evaluated"] * 100)
            if results["skills_evaluated"] > 0
            else 0
        )
        print(f"\nPass Rate: {pass_rate:.1f}%")

        if pass_rate < 50:
            print("\n⚠️  WARNING: Less than half of evaluation skills meet standards.")
            print("   Recursive validation is broken.")
            print("   Priority: Address critical and high issues immediately.")
        elif pass_rate < 80:
            print("\n⚠️  CAUTION: Many evaluation skills need improvement.")
            print("   Priority: Address high and medium issues.")
        else:
            print("\n✓ GOOD: Most evaluation skills meet quality standards.")
            print("   Continue improving remaining issues.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Meta-evaluation of evaluation-related skills"
    )
    parser.add_argument(
        "--plugins-root",
        type=Path,
        default=Path.cwd() / "plugins",
        help="Root directory containing plugins (default: ./plugins)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed results for all skills",
    )
    parser.add_argument(
        "--plugin",
        help="Evaluate specific plugin only",
    )

    args = parser.parse_args()

    # Validate plugins root
    if not args.plugins_root.exists():
        print(f"[ERROR] Plugins root not found: {args.plugins_root}")
        sys.exit(1)

    # Create evaluator
    evaluator = MetaEvaluator(args.plugins_root, verbose=args.verbose)

    # If specific plugin requested, filter skills
    if args.plugin:
        if args.plugin in evaluator.EVALUATION_SKILLS:
            skills = {args.plugin: evaluator.EVALUATION_SKILLS[args.plugin]}
            evaluator.EVALUATION_SKILLS = skills
        else:
            print(f"[WARN] Plugin {args.plugin} not in evaluation skills inventory")
            print(f"Available plugins: {list(evaluator.EVALUATION_SKILLS.keys())}")

    # Run evaluation
    results = evaluator.evaluate_all()

    # Print results
    evaluator.print_results(results)
    evaluator.print_summary(results)

    # Exit code based on results
    if results["by_severity"]["critical"] > 0:
        sys.exit(1)  # Critical issues
    elif results["by_severity"]["high"] > 0:
        sys.exit(1)  # High priority issues
    elif results["total_issues"] > 0:
        sys.exit(0)  # Issues exist but not critical
    else:
        sys.exit(0)  # All clean


if __name__ == "__main__":
    main()
