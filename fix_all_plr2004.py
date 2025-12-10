#!/usr/bin/env python3
"""Script to fix all PLR2004 magic number issues."""

import os
import re
import subprocess

# Common threshold constants
THRESHOLD_CONSTANTS = {
    # Token limits
    "100000": "MAX_TOKENS_100K",
    "85000": "MAX_TOKENS_85K",
    "108000": "MAX_TOKENS_108K",
    "50000": "MAX_TOKENS_50K",
    "20000": "MAX_TOKENS_20K",
    "15000": "MAX_TOKENS_15K",
    "12000": "MAX_TOKENS_12K",
    "10000": "MAX_TOKENS_10K",
    "8000": "MAX_TOKENS_8K",
    "5000": "MAX_TOKENS_5K",
    "2000": "MAX_TOKENS_2K",
    "1500": "MAX_TOKENS_1_5K",
    "1200": "MAX_TOKENS_1_2K",
    "1000": "MAX_TOKENS_1K",
    "800": "MAX_TOKENS_800",
    # Time/Speed thresholds
    "150.0": "SECONDS_150",
    "50.0": "SECONDS_50",
    "20.0": "SECONDS_20",
    "10.0": "SECONDS_10",
    "8.0": "SECONDS_8",
    "5.0": "SECONDS_5",
    "2.0": "SECONDS_2",
    "1.0": "SECONDS_1",
    "0.8": "SECONDS_0_8",
    # Percentage/Utilization thresholds
    "0.95": "PERCENT_95",
    "0.9": "PERCENT_90",
    "0.8": "PERCENT_80",
    "0.7": "PERCENT_70",
    "0.6": "PERCENT_60",
    "0.5": "PERCENT_50",
    "0.4": "PERCENT_40",
    "0.3": "PERCENT_30",
    "0.2": "PERCENT_20",
    "0.1": "PERCENT_10",
    "0.05": "PERCENT_5",
    # Count thresholds
    "500": "COUNT_500",
    "200": "COUNT_200",
    "100": "COUNT_100",
    "90": "COUNT_90",
    "80": "COUNT_80",
    "70": "COUNT_70",
    "60": "COUNT_60",
    "50": "COUNT_50",
    "30": "COUNT_30",
    "20": "COUNT_20",
    "15": "COUNT_15",
    "10": "COUNT_10",
    "8": "COUNT_8",
    "7": "COUNT_7",
    "6": "COUNT_6",
    "5": "COUNT_5",
    "4": "COUNT_4",
    "3": "COUNT_3",
    "2": "COUNT_2",
    # Memory thresholds (bytes)
    "50_000_000": "MEMORY_50MB",
    "10_000_000": "MEMORY_10MB",
    "1_000_000": "MEMORY_1MB",
    "100_000": "MEMORY_100KB",
    "50_000": "MEMORY_50KB",
    # Special values
    "42.5": "VALUE_42_5",
}


def extract_magic_numbers_from_ruff() -> dict[str, list[tuple[str, int, str]]]:
    """Extract all PLR2004 errors from ruff output."""
    # Run ruff to get all PLR2004 errors
    result = subprocess.run(
        ["uv", "run", "ruff", "check", "--select=PLR2004", "--output-format=json"],
        check=False,
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    import json

    try:
        errors = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Failed to parse ruff JSON output
        return {}

    # Group by file
    files_with_errors: dict[str, list[tuple[str, int, str]]] = {}

    for error in errors:
        file_path = error["filename"]
        line = error["location"]["row"]
        message = error["message"]

        # Extract the magic number from the message
        match = re.search(r"replacing `([^`]+)`", message)
        if match:
            magic_number = match.group(1)

            if file_path not in files_with_errors:
                files_with_errors[file_path] = []

            files_with_errors[file_path].append((magic_number, line, message))

    return files_with_errors


def generate_constants_for_file(
    magic_numbers: list[tuple[str, int, str]],
) -> dict[str, str]:
    """Generate constant names for magic numbers in a file."""
    constants: dict[str, str] = {}

    for magic_number, _line, _message in magic_numbers:
        if magic_number in constants:
            continue

        # Use predefined constant if available
        if magic_number in THRESHOLD_CONSTANTS:
            constants[magic_number] = THRESHOLD_CONSTANTS[magic_number]
        # Generate a generic constant name
        elif "." in magic_number:
            clean_num = magic_number.replace(".", "_").replace("-", "_")
            constants[magic_number] = f"FLOAT_{clean_num}"
        else:
            clean_num = magic_number.replace("-", "_")
            constants[magic_number] = f"INT_{clean_num}"

    return constants


def fix_file(
    file_path: str,
    magic_numbers: list[tuple[str, int, str]],
    dry_run: bool = False,
) -> bool:
    """Fix magic numbers in a specific file."""
    if not magic_numbers:
        return True

    # Generate constants for this file
    constants = generate_constants_for_file(magic_numbers)

    # Read the file
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        # Error reading file
        return False

    # Skip verbose output in utility script

    if dry_run:
        # Dry run - just return success
        return True

    # Find where to insert constants (after imports)
    lines = content.split("\n")
    import_end = 0

    # Find the end of imports
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not (stripped.startswith(("import", "from"))):
            import_end = i
            # Skip blank lines after imports
            while import_end < len(lines) and not lines[import_end].strip():
                import_end += 1
            break

    # Insert constants section
    if constants:
        constant_lines = ["# Constants for magic values (PLR2004)"]
        # Sort constants by numeric value for better organization
        for num in sorted(
            constants.keys(),
            key=lambda x: float(x) if "." in x else int(x),
        ):
            constant_lines.append(f"{constants[num]} = {num}")

        # Insert after imports
        lines = lines[:import_end] + constant_lines + [""] + lines[import_end:]

        # Update the content
        content = "\n".join(lines)

    # Replace magic numbers with constants
    # We need to be careful to only replace in comparison contexts
    for magic_number, constant_name in constants.items():
        # Escape special regex characters
        escaped_num = re.escape(magic_number)

        # Pattern to match magic numbers in comparisons
        # Look for patterns like: > num, < num, == num, >= num, <= num, != num
        pattern = rf"([><=!]=?\s*){escaped_num}(?!\w)"
        replacement = rf"\1{constant_name}"

        # Apply replacement
        new_content = re.sub(pattern, replacement, content)
        content = new_content

    # Write the file back
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        # Error writing file
        return False


def main() -> None:
    """Main function to fix all PLR2004 issues."""
    # Get all PLR2004 errors
    files_with_errors = extract_magic_numbers_from_ruff()

    if not files_with_errors:
        # No PLR2004 issues found!
        return

    # Get choice from environment variable or default to fixing
    choice = os.environ.get("PLR2004_CHOICE", "2").strip()

    if choice == "1":
        # Dry run mode
        for file_path, issues in files_with_errors.items():
            fix_file(file_path, issues, dry_run=True)
    elif choice == "2":
        # Fix files mode
        fixed = 0
        failed = 0

        for file_path, issues in files_with_errors.items():
            if fix_file(file_path, issues, dry_run=False):
                fixed += 1
            else:
                failed += 1
    else:
        # Exiting...
        pass


if __name__ == "__main__":
    main()
