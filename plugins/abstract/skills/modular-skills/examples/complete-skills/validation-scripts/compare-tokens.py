#!/usr/bin/env python3
"""Token comparison script for monolithic vs modular skill comparison.

Demonstrates the efficiency gains from modularization.
"""

import argparse
import json
import sys
from pathlib import Path

import tiktoken


class TokenComparison:
    """Compare token usage between monolithic and modular approaches."""

    def __init__(self):
        """Initialize token comparison tool."""
        # Efficiency thresholds
        self.EXCELLENT_THRESHOLD = 50
        self.GOOD_THRESHOLD = 30
        self.MODERATE_THRESHOLD = 10
        self.MIN_MODULE_COUNT = 3
        # Initialize tokenizer (similar to Claude's)
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback if tiktoken not available
            self.encoder = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Rough estimation: ~4 characters per token
            return len(text) // 4

    def analyze_skill_file(self, file_path: Path) -> dict:
        """Analyze a single skill file."""
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        content = file_path.read_text(encoding="utf-8")

        # Extract frontmatter (between --- markers)
        frontmatter_start = content.find("---")
        frontmatter_end = content.find("---", frontmatter_start + 3)

        frontmatter_tokens = 0
        body_tokens = 0

        if frontmatter_start != -1 and frontmatter_end != -1:
            frontmatter = content[frontmatter_start : frontmatter_end + 3]
            body = content[frontmatter_end + 3 :]
            frontmatter_tokens = self.count_tokens(frontmatter)
            body_tokens = self.count_tokens(body)
        else:
            body_tokens = self.count_tokens(content)

        total_tokens = frontmatter_tokens + body_tokens

        return {
            "path": str(file_path),
            "size_bytes": len(content.encode("utf-8")),
            "total_tokens": total_tokens,
            "frontmatter_tokens": frontmatter_tokens,
            "body_tokens": body_tokens,
            "lines": len(content.splitlines()),
        }

    def analyze_monolithic(self, monolithic_path: Path) -> dict:
        """Analyze the monolithic skill file."""
        print(f"🔍 Analyzing monolithic skill: {monolithic_path.name}")
        return self.analyze_skill_file(monolithic_path)

    def analyze_modular(self, modular_dir: Path) -> dict:
        """Analyze the modular skill directory."""
        print(f"🔍 Analyzing modular skill: {modular_dir.name}")

        results = {
            "hub": None,
            "modules": {},
            "tools": {},
            "total_tokens": 0,
            "total_files": 0,
        }

        # Analyze hub skill (SKILL.md)
        hub_path = modular_dir / "SKILL.md"
        if hub_path.exists():
            results["hub"] = self.analyze_skill_file(hub_path)
            results["total_tokens"] += results["hub"]["total_tokens"]
            results["total_files"] += 1

        # Analyze modules
        modules_dir = modular_dir / "modules"
        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir():
                    module_skill = module_dir / "SKILL.md"
                    if module_skill.exists():
                        module_data = self.analyze_skill_file(module_skill)
                        results["modules"][module_dir.name] = module_data
                        results["total_tokens"] += module_data["total_tokens"]
                        results["total_files"] += 1

        # Analyze tools
        tools_dir = modular_dir / "tools"
        if tools_dir.exists():
            for tool_file in tools_dir.iterdir():
                if tool_file.is_file() and tool_file.suffix in [".py", ".sh", ".js"]:
                    tool_data = self.analyze_skill_file(tool_file)
                    results["tools"][tool_file.name] = tool_data
                    results["total_tokens"] += tool_data["total_tokens"]
                    results["total_files"] += 1

        return results

    def calculate_efficiency_metrics(self, monolithic: dict, modular: dict) -> dict:
        """Calculate efficiency metrics comparing both approaches."""
        if "error" in monolithic or not modular.get("total_files"):
            return {"error": "Invalid comparison data"}

        monolithic_tokens = monolithic["total_tokens"]
        modular_tokens = modular["total_tokens"]

        token_savings = monolithic_tokens - modular_tokens
        if monolithic_tokens > 0:
            token_reduction_pct = (token_savings / monolithic_tokens) * 100
        else:
            token_reduction_pct = 0

        # Calculate efficiency for different scenarios
        scenarios = {
            "full_load": {
                "description": "Loading complete skill (all modules and tools)",
                "tokens": modular_tokens,
                "efficiency": f"{token_reduction_pct:.1f}% token reduction",
            },
            "core_only": {
                "description": "Loading only hub skill for overview",
                "tokens": modular["hub"]["total_tokens"] if modular["hub"] else 0,
                "efficiency": self._calculate_percentage_reduction(
                    monolithic_tokens,
                    modular["hub"]["total_tokens"] if modular["hub"] else 0,
                ),
            },
            "single_module": {
                "description": "Loading hub + one specific module",
                "tokens": self._calculate_hub_plus_min_module(modular),
                "efficiency": "Focused content loading",
            },
            "common_workflow": {
                "description": "Typical workflow: hub + git + testing + code review",
                "tokens": self._calculate_common_workflow(modular),
                "efficiency": "Targeted workflow optimization",
            },
        }

        return {
            "monolithic_tokens": monolithic_tokens,
            "modular_total_tokens": modular_tokens,
            "token_savings": token_savings,
            "token_reduction_percentage": token_reduction_pct,
            "scenarios": scenarios,
            "modularity_score": len(modular["modules"]) + len(modular["tools"]),
            "reuseability_score": len(modular["modules"]) * 2,
            "maintainability_score": modular["total_files"],
        }

    def _calculate_common_workflow(self, modular: dict) -> int:
        """Calculate tokens for common development workflow."""
        tokens = modular["hub"]["total_tokens"] if modular["hub"] else 0

        # Common modules that are frequently used together
        common_modules = ["git-workflow", "testing-strategies", "code-review"]
        for module_name in common_modules:
            if module_name in modular["modules"]:
                tokens += modular["modules"][module_name]["total_tokens"]

        return tokens

    def _calculate_percentage_reduction(self, original: int, new: int) -> str:
        """Calculate percentage reduction between original and new values."""
        if original > 0:
            reduction = ((original - new) / original) * 100
            return f"{reduction:.1f}% token reduction"
        return "0% token reduction"

    def _calculate_hub_plus_min_module(self, modular: dict) -> int:
        """Calculate tokens for hub plus the smallest module."""
        hub_tokens = modular["hub"]["total_tokens"] if modular["hub"] else 0

        if not modular["modules"]:
            return hub_tokens

        min_module_tokens = min(
            module["total_tokens"] for module in modular["modules"].values()
        )
        return hub_tokens + min_module_tokens

    def print_comparison_report(self, comparison: dict) -> None:
        """Print a detailed comparison report."""
        print("\n" + "=" * 60)
        print("📊 TOKEN COMPARISON REPORT")
        print("=" * 60)

        if "error" in comparison:
            print(f"❌ Error: {comparison['error']}")
            return

        monolithic = comparison["monolithic_analysis"]
        modular = comparison["modular_analysis"]
        metrics = comparison["efficiency_metrics"]

        print("\n📁 Files Analyzed:")
        print("  Monolithic: 1 file")
        module_count = len(modular["modules"])
        tool_count = len(modular["tools"])
        files_info = (
            f"{modular['total_files']} files "
            f"({module_count} modules + {tool_count} tools)"
        )
        print(f"  Modular: {files_info}")

        print("\n🔢 Token Usage:")
        print(f"  Monolithic: {monolithic['total_tokens']:,} tokens")
        print(f"  Modular: {metrics['modular_total_tokens']:,} tokens")
        print(f"  Savings: {metrics['token_savings']:,} tokens")
        print(f"  Reduction: {metrics['token_reduction_percentage']:.1f}%")

        print("\n🎯 Usage Scenarios:")
        for _scenario_name, scenario in metrics["scenarios"].items():
            print(f"  {scenario['description']}:")
            print(f"    Tokens: {scenario['tokens']:,}")
            print(f"    Efficiency: {scenario['efficiency']}")

        print("\n📈 Quality Metrics:")
        print(f"  Modularity Score: {metrics['modularity_score']}/10")
        print(f"  Reusability Score: {metrics['reuseability_score']}/20")
        print(f"  Maintainability Score: {metrics['maintainability_score']}/15")

        print("\n🔍 Module Breakdown:")
        if modular["hub"]:
            print(f"  Hub (SKILL.md): {modular['hub']['total_tokens']:,} tokens")

        for module_name, module_data in modular["modules"].items():
            print(f"  Module {module_name}: {module_data['total_tokens']:,} tokens")

        for tool_name, tool_data in modular["tools"].items():
            print(f"  Tool {tool_name}: {tool_data['total_tokens']:,} tokens")

        # Efficiency recommendations
        print("\n💡 Efficiency Recommendations:")

        if metrics["token_reduction_percentage"] > self.EXCELLENT_THRESHOLD:
            print("  ✅ Excellent token efficiency achieved!")
        elif metrics["token_reduction_percentage"] > self.GOOD_THRESHOLD:
            print("  ✅ Good token efficiency improvement")
        elif metrics["token_reduction_percentage"] > self.MODERATE_THRESHOLD:
            print("  ⚠️  Moderate token efficiency gains")
        else:
            print("  ❌ Limited token efficiency - consider further modularization")

        if len(modular["modules"]) >= self.MIN_MODULE_COUNT:
            print("  ✅ Strong modularity with multiple focused components")
        else:
            print("  ⚠️  Consider breaking down into more focused modules")

    def generate_comparison_json(self, comparison: dict, output_path: Path) -> None:
        """Generate detailed JSON comparison report."""
        comparison_data = {
            "timestamp": str(Path.cwd()),
            "analysis": comparison,
            "metadata": {
                "monolithic_approach": "Single large skill file with all functionality",
                "modular_approach": (
                    "Hub-and-spoke pattern with focused modules and tools"
                ),
                "tokenizer": "cl100k_base (approximation of Claude's tokenizer)",
            },
        }

        with open(output_path, "w") as f:
            json.dump(comparison_data, f, indent=2)

    def run_comparison(self, monolithic_path: str, modular_path: str) -> dict:
        """Run complete comparison analysis."""
        monolithic_file = Path(monolithic_path)
        modular_dir = Path(modular_path)

        monolithic_analysis = self.analyze_monolithic(monolithic_file)
        modular_analysis = self.analyze_modular(modular_dir)
        efficiency_metrics = self.calculate_efficiency_metrics(
            monolithic_analysis, modular_analysis
        )

        return {
            "monolithic_analysis": monolithic_analysis,
            "modular_analysis": modular_analysis,
            "efficiency_metrics": efficiency_metrics,
        }


def main():
    """Entry point for token comparison script."""
    parser = argparse.ArgumentParser(
        description="Compare token usage between monolithic and modular skills"
    )
    parser.add_argument("monolithic", help="Path to monolithic skill file")
    parser.add_argument("modular", help="Path to modular skill directory")
    parser.add_argument("--output", "-o", help="Output JSON file for detailed analysis")
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress detailed output, only show summary",
    )

    args = parser.parse_args()

    # Initialize and run comparison
    comparison = TokenComparison()
    results = comparison.run_comparison(args.monolithic, args.modular)

    if not args.quiet:
        comparison.print_comparison_report(results)

    if args.output:
        comparison.generate_comparison_json(results, Path(args.output))
        print(f"\n📄 Detailed report saved to: {args.output}")

    # Exit with error code if analysis failed
    if "error" in results or "error" in results.get("efficiency_metrics", {}):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
