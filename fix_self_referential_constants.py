#!/usr/bin/env python3
"""Script to fix self-referential constants created by ruff."""

from pathlib import Path


def fix_constants_in_file(file_path: Path) -> bool:
    """Fix self-referential constants in a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Define common constants with their actual values
        common_constants = {
            "ZERO": "0",
            "ONE": "1",
            "TWO": "2",
            "THREE": "3",
            "FOUR": "4",
            "FIVE": "5",
            "SIX": "6",
            "SEVEN": "7",
            "EIGHT": "8",
            "NINE": "9",
            "TEN": "10",
            "ELEVEN": "11",
            "TWELVE": "12",
            "THIRTEEN": "13",
            "FOURTEEN": "14",
            "FIFTEEN": "15",
            "SIXTEEN": "16",
            "SEVENTEEN": "17",
            "EIGHTEEN": "18",
            "NINETEEN": "19",
            "TWENTY": "20",
            "TWENTY_FIVE": "25",
            "THIRTY": "30",
            "THIRTY_FIVE": "35",
            "FORTY": "40",
            "FIFTY": "50",
            "SIXTY": "60",
            "SEVENTY": "70",
            "EIGHTY": "80",
            "NINETY": "90",
            "HUNDRED": "100",
            "ONE_HUNDRED": "100",
            "TWO_HUNDRED": "200",
            "THREE_HUNDRED": "300",
            "FOUR_HUNDRED": "400",
            "FIVE_HUNDRED": "500",
            "THOUSAND": "1000",
            "ONE_THOUSAND": "1000",
            "TWO_THOUSAND": "2000",
            "FIVE_THOUSAND": "5000",
            "TEN_THOUSAND": "10000",
            "FIFTY_THOUSAND": "50000",
            "HUNDRED_THOUSAND": "100000",
            "MILLION": "1000000",
            "TEN_MILLION": "10000000",
            "FIFTY_MILLION": "50000000",
            "HUNDRED_MILLION": "100000000",
            "POINT_ONE": "0.1",
            "POINT_TWO": "0.2",
            "POINT_THREE": "0.3",
            "POINT_FOUR": "0.4",
            "POINT_FIVE": "0.5",
            "POINT_SIX": "0.6",
            "POINT_SEVEN": "0.7",
            "POINT_EIGHT": "0.8",
            "POINT_NINE": "0.9",
            "ONE_POINT_FIVE": "1.5",
            "TWO_POINT_FIVE": "2.5",
            "NINETY_POINT_ZERO": "90.0",
        }

        # Find the constants section
        lines = content.split("\n")
        constants_start = -1
        constants_end = -1

        for i, line in enumerate(lines):
            if "# Constants for PLR2004 magic values" in line:
                constants_start = i
            elif (
                constants_start >= 0
                and line.strip()
                and not line.startswith(" ")
                and not line.startswith("#")
            ):
                # Found end of constants section
                constants_end = i
                break

        if constants_start >= 0:
            if constants_end == -1:
                constants_end = len(lines)

            # Process the constants section
            for i in range(constants_start + 1, constants_end):
                line = lines[i]
                if "=" in line and not line.strip().startswith("#"):
                    # Extract constant name
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        const_name = parts[0].strip()
                        const_value = parts[1].strip()

                        # Check if it's self-referential
                        if const_name == const_value and const_name in common_constants:
                            lines[i] = f"{const_name} = {common_constants[const_name]}"

            content = "\n".join(lines)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception:
        return False


def main() -> None:
    """Main function to fix self-referential constants."""
    # Get list of files that need fixing from the previous command
    files_to_fix = [
        "plugins/conservation/tests/unit/commands/test_analyze_growth.py",
        "plugins/conservation/tests/unit/commands/test_optimize_context.py",
        "plugins/conservation/tests/unit/scripts/test_conservation_validator.py",
        "plugins/conservation/tests/unit/skills/test_context_optimization.py",
        "plugins/conservation/tests/unit/skills/test_mcp_code_execution.py",
        "plugins/conservation/tests/unit/skills/test_optimizing_large_skills.py",
        "plugins/conservation/tests/unit/skills/test_performance_monitoring.py",
        "plugins/conservation/tests/unit/skills/test_token_conservation.py",
        "plugins/imbue/tests/integration/test_review_workflow_integration.py",
        "plugins/imbue/tests/performance/test_validator_performance.py",
        "plugins/imbue/tests/performance/test_workflow_scalability.py",
        "plugins/imbue/tests/unit/agents/test_review_analyst.py",
        "plugins/imbue/tests/unit/commands/test_review_command.py",
        "plugins/imbue/tests/unit/skills/test_catchup.py",
        "plugins/memory-palace/scripts/seed_corpus.py",
        "plugins/memory-palace/tests/test_garden_metrics.py",
        "plugins/sanctum/skills/doc-consolidation/scripts/consolidation_planner.py",
    ]

    fixed_count = 0
    for file_path in files_to_fix:
        path = Path(file_path)
        if path.exists():
            if fix_constants_in_file(path):
                fixed_count += 1
            else:
                pass
        else:
            pass


if __name__ == "__main__":
    main()
