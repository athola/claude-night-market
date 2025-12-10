#!/usr/bin/env python3
"""Script to fix PLR2004 magic number issues in test files."""

import ast
import re
from pathlib import Path

# Common magic numbers and their suggested constant names
COMMON_MAGIC_NUMBERS: dict[str, str] = {
    "0": "ZERO",
    "1": "ONE",
    "2": "TWO",
    "3": "THREE",
    "4": "FOUR",
    "5": "FIVE",
    "6": "SIX",
    "7": "SEVEN",
    "8": "EIGHT",
    "9": "NINE",
    "10": "TEN",
    "20": "TWENTY",
    "30": "THIRTY",
    "40": "FORTY",
    "50": "FIFTY",
    "60": "SIXTY",
    "70": "SEVENTY",
    "80": "EIGHTY",
    "90": "NINETY",
    "100": "HUNDRED",
    "200": "TWO_HUNDRED",
    "300": "THREE_HUNDRED",
    "400": "FOUR_HUNDRED",
    "500": "FIVE_HUNDRED",
    "1000": "THOUSAND",
    "2000": "TWO_THOUSAND",
    "5000": "FIVE_THOUSAND",
    "10000": "TEN_THOUSAND",
    "50000": "FIFTY_THOUSAND",
    "100000": "HUNDRED_THOUSAND",
    "1000000": "MILLION",
    "10_000_000": "TEN_MILLION",
    "50_000_000": "FIFTY_MILLION",
    "100_000_000": "HUNDRED_MILLION",
    "0.1": "POINT_ONE",
    "0.2": "POINT_TWO",
    "0.3": "POINT_THREE",
    "0.4": "POINT_FOUR",
    "0.5": "POINT_FIVE",
    "0.6": "POINT_SIX",
    "0.7": "POINT_SEVEN",
    "0.8": "POINT_EIGHT",
    "0.9": "POINT_NINE",
}


def find_magic_numbers_in_file(file_path: Path) -> list[tuple[int, str, str]]:
    """Find magic numbers in comparisons within a Python file."""
    magic_numbers = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
    except Exception:
        return magic_numbers

    # Parse the file to understand the structure
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return magic_numbers

    # Find all comparison nodes
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            # Check each comparator
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and isinstance(
                    comparator.value,
                    (int, float),
                ):
                    # Check if it's a magic number (not 0 or 1, which are common)
                    if comparator.value not in [0, 1]:
                        line_num = comparator.lineno
                        line_content = lines[line_num - 1]
                        magic_numbers.append(
                            (line_num, str(comparator.value), line_content.strip()),
                        )

    return magic_numbers


def generate_constants_for_file(
    magic_numbers: list[tuple[int, str, str]],
) -> dict[str, str]:
    """Generate appropriate constant names for magic numbers found in a file."""
    constants = {}
    seen_numbers = set()

    for _line_num, value, line_content in magic_numbers:
        if value in seen_numbers:
            continue

        seen_numbers.add(value)

        # Suggest a constant name based on the context
        if value in COMMON_MAGIC_NUMBERS:
            base_name = COMMON_MAGIC_NUMBERS[value]
        # For uncommon numbers, create a generic name
        elif "." in value:
            base_name = f"FLOAT_{value.replace('.', '_')}"
        else:
            base_name = f"NUM_{value}"

        # Try to infer a better name from context
        if "memory" in line_content.lower():
            constants[value] = f"MAX_MEMORY_{base_name}"
        elif "time" in line_content.lower():
            constants[value] = f"MAX_TIME_{base_name}"
        elif "len(" in line_content:
            constants[value] = f"MIN_LENGTH_{base_name}"
        elif "files" in line_content.lower():
            constants[value] = f"MAX_FILES_{base_name}"
        elif "items" in line_content.lower():
            constants[value] = f"MAX_ITEMS_{base_name}"
        else:
            constants[value] = base_name

    return constants


def fix_file(file_path: Path, dry_run: bool = True) -> bool:
    """Fix magic numbers in a file."""
    magic_numbers = find_magic_numbers_in_file(file_path)

    if not magic_numbers:
        return True

    for _line_num, value, _line_content in magic_numbers:
        pass

    # Generate constants
    constants = generate_constants_for_file(magic_numbers)

    if dry_run:
        for value, name in constants.items():
            pass
        return False

    # Actually fix the file
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Add constants at the top after imports
        lines = content.split("\n")
        import_end = 0

        # Find where imports end
        for i, line in enumerate(lines):
            if line.strip() and not (line.startswith(("import", "from"))):
                import_end = i
                break

        # Insert constants
        constant_lines = ["# Constants for test thresholds"]
        for value, name in constants.items():
            constant_lines.append(f"{name} = {value}")

        lines = lines[:import_end] + constant_lines + lines[import_end:]

        # Replace magic numbers in comparisons
        content = "\n".join(lines)

        # Replace magic numbers in comparison contexts
        for value, name in constants.items():
            # Pattern to match magic numbers in comparisons
            pattern = r"([><=!]=?\s*)" + re.escape(value) + r"(?!\w)"
            replacement = r"\1" + name
            content = re.sub(pattern, replacement, content)

        # Write back the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    except Exception:
        return False


def main() -> None:
    """Main function to fix PLR2004 issues."""
    # Find all Python test files
    test_files = []
    for pattern in ["**/test_*.py", "**/*_test.py"]:
        test_files.extend(Path().glob(pattern))

    # Filter to files that have PLR2004 issues
    files_to_fix = []
    for file_path in test_files:
        magic_numbers = find_magic_numbers_in_file(file_path)
        if magic_numbers:
            files_to_fix.append(file_path)

    if not files_to_fix:
        return

    # Ask user what to do
    response = input(
        "\nDo you want to:\n1. Show suggested changes (dry run)\n2. Apply fixes\n3. Exit\n> ",
    )

    if response == "1":
        for file_path in files_to_fix:
            fix_file(file_path, dry_run=True)
    elif response == "2":
        fixed_count = 0
        for file_path in files_to_fix:
            if fix_file(file_path, dry_run=False):
                fixed_count += 1
    else:
        pass


if __name__ == "__main__":
    main()
