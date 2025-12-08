#!/usr/bin/env python3
"""Comprehensive skill optimization patterns and tools.
CLI interface for systematic skill file optimization.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def analyze_skill_file(file_path: str) -> dict[str, Any]:
    """Analyze skill file for optimization opportunities."""
    with open(file_path) as f:
        content = f.read()

    lines = content.split('\n')
    total_lines = len(lines)

    # Count code blocks
    code_blocks = content.count('```')

    # Count Python functions
    python_functions = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))

    # Find functions over 20 lines
    long_functions = []
    if python_functions > 0:
        in_function = False
        function_start = 0
        function_lines = 0

        for i, line in enumerate(lines):
            if re.match(r'^def\s+\w+', line):
                if in_function:
                    long_functions.append((function_start, function_lines))
                in_function = True
                function_start = i + 1
                function_lines = 0
            elif in_function and line.strip() and not line.startswith('    '):
                long_functions.append((function_start, function_lines))
                in_function = False
            elif in_function:
                function_lines += 1

        if in_function:
            long_functions.append((function_start, function_lines))

    return {
        'file_path': file_path,
        'total_lines': total_lines,
        'code_blocks': code_blocks,
        'python_functions': python_functions,
        'long_functions': [(start+1, lines) for start, lines in long_functions if lines > 20],
        'needs_optimization': total_lines > 300 or code_blocks > 5 or python_functions > 10
    }

def calculate_size_reduction(original_lines: int, optimizations: list[str]) -> dict[str, float]:
    """Calculate expected size reduction from optimizations."""
    reductions = {
        'externalize_heavy_implementations': 0.65,  # 60-70% reduction
        'consolidate_similar_functions': 0.175,       # 15-20% reduction
        'replace_code_with_structured_data': 0.125,  # 10-15% reduction
        'progressive_loading': 0.075                  # 5-10% reduction
    }

    total_reduction = 0.0
    applied_optimizations = []

    for opt in optimizations:
        if opt in reductions:
            total_reduction += reductions[opt]
            applied_optimizations.append(opt)

    # Cap at 90% reduction (realistic maximum)
    total_reduction = min(total_reduction, 0.9)

    return {
        'original_lines': original_lines,
        'expected_lines': int(original_lines * (1 - total_reduction)),
        'reduction_percentage': total_reduction * 100,
        'applied_optimizations': applied_optimizations
    }

def generate_optimization_plan(analysis: dict[str, Any]) -> dict[str, Any]:
    """Generate systematic optimization plan based on analysis."""
    plan = {
        'analysis': analysis,
        'optimizations_needed': [],
        'file_structure': {},
        'expected_outcome': {}
    }

    # Determine optimizations needed
    if analysis['total_lines'] > 300:
        plan['optimizations_needed'].append('externalize_heavy_implementations')

    if analysis['python_functions'] > 5:
        plan['optimizations_needed'].append('consolidate_similar_functions')

    if analysis['code_blocks'] > 3:
        plan['optimizations_needed'].append('replace_code_with_structured_data')

    if analysis['total_lines'] > 200:
        plan['optimizations_needed'].append('progressive_loading')

    # Generate file structure
    if plan['optimizations_needed']:
        Path(analysis['file_path']).stem
        plan['file_structure'] = {
            'SKILL.md': 'Optimized documentation (~150-200 lines)',
            'tools/': {
                'analyzer.py': 'Heavy implementations with CLI',
                'controller.py': 'Control logic and strategy generation',
                'config.yaml': 'Structured configuration data'
            },
            'examples/': {
                'basic-usage.py': 'Minimal working example'
            }
        }

    # Calculate expected outcome
    if plan['optimizations_needed']:
        outcome = calculate_size_reduction(analysis['total_lines'], plan['optimizations_needed'])
        plan['expected_outcome'] = outcome

    return plan

def main():
    """CLI interface for skill optimization analysis."""
    parser = argparse.ArgumentParser(description='Analyze and plan skill file optimization')
    parser.add_argument('skill_file', help='Path to skill file (SKILL.md)')
    parser.add_argument('--output-json', action='store_true', help='Output results as JSON')
    parser.add_argument('--verbose', action='store_true', help='Detailed analysis output')
    parser.add_argument('--generate-plan', action='store_true', help='Generate optimization plan')

    args = parser.parse_args()

    # Validate file exists
    if not os.path.exists(args.skill_file):
        print(f"Error: File '{args.skill_file}' not found")
        return 1

    # Analyze skill file
    analysis = analyze_skill_file(args.skill_file)

    if args.verbose or args.generate_plan:
        print("=== SKILL FILE ANALYSIS ===")
        print(f"File: {analysis['file_path']}")
        print(f"Total lines: {analysis['total_lines']}")
        print(f"Code blocks: {analysis['code_blocks']}")
        print(f"Python functions: {analysis['python_functions']}")

        if analysis['long_functions']:
            print(f"Long functions (>20 lines): {len(analysis['long_functions'])}")
            for start, lines in analysis['long_functions']:
                print(f"  Line {start}: {lines} lines")

        print(f"Needs optimization: {analysis['needs_optimization']}")
        print()

    if args.generate_plan:
        plan = generate_optimization_plan(analysis)
        print("=== OPTIMIZATION PLAN ===")

        if plan['optimizations_needed']:
            print("Optimizations recommended:")
            for opt in plan['optimizations_needed']:
                print(f"  - {opt}")
            print()

            print("Expected outcome:")
            outcome = plan['expected_outcome']
            print(f"  Original: {outcome['original_lines']} lines")
            print(f"  Expected: {outcome['expected_lines']} lines")
            print(f"  Reduction: {outcome['reduction_percentage']:.1f}%")
            print()

            print("File structure:")
            for item, description in plan['file_structure'].items():
                if isinstance(description, dict):
                    print(f"  {item}/")
                    for subitem, subdesc in description.items():
                        print(f"    {subitem}: {subdesc}")
                else:
                    print(f"  {item}: {description}")
        else:
            print("No optimization needed - file is already optimized")

    if args.output_json:
        if args.generate_plan:
            plan = generate_optimization_plan(analysis)
            print(json.dumps(plan, indent=2))
        else:
            print(json.dumps(analysis, indent=2))

    return 0

if __name__ == "__main__":
    sys.exit(main())
