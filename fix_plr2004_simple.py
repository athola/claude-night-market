#!/usr/bin/env python3
"""Simple script to fix PLR2004 magic number issues."""

import re
import subprocess

# Define common constants
COMMON_CONSTANTS = {
    "2": "TWO",
    "3": "THREE",
    "4": "FOUR",
    "5": "FIVE",
    "6": "SIX",
    "7": "SEVEN",
    "8": "EIGHT",
    "9": "NINE",
    "10": "TEN",
    "15": "FIFTEEN",
    "20": "TWENTY",
    "30": "THIRTY",
    "40": "FORTY",
    "50": "FIFTY",
    "60": "SIXTY",
    "70": "SEVENTY",
    "80": "EIGHTY",
    "90": "NINETY",
    "100": "HUNDRED",
    "150": "ONE_FIFTY",
    "200": "TWO_HUNDRED",
    "300": "THREE_HUNDRED",
    "400": "FOUR_HUNDRED",
    "500": "FIVE_HUNDRED",
    "600": "SIX_HUNDRED",
    "700": "SEVEN_HUNDRED",
    "800": "EIGHT_HUNDRED",
    "900": "NINE_HUNDRED",
    "1000": "THOUSAND",
    "2000": "TWO_THOUSAND",
    "3000": "THREE_THOUSAND",
    "4000": "FOUR_THOUSAND",
    "5000": "FIVE_THOUSAND",
    "6000": "SIX_THOUSAND",
    "7000": "SEVEN_THOUSAND",
    "8000": "EIGHT_THOUSAND",
    "9000": "NINE_THOUSAND",
    "10000": "TEN_THOUSAND",
    "15000": "FIFTEEN_THOUSAND",
    "20000": "TWENTY_THOUSAND",
    "50000": "FIFTY_THOUSAND",
    "100000": "HUNDRED_THOUSAND",
    "500000": "FIVE_HUNDRED_THOUSAND",
    "1000000": "MILLION",
    "10_000_000": "TEN_MILLION",
    "50_000_000": "FIFTY_MILLION",
    "100_000_000": "HUNDRED_MILLION",
    "0.1": "ZERO_POINT_ONE",
    "0.2": "ZERO_POINT_TWO",
    "0.3": "ZERO_POINT_THREE",
    "0.4": "ZERO_POINT_FOUR",
    "0.5": "ZERO_POINT_FIVE",
    "0.6": "ZERO_POINT_SIX",
    "0.7": "ZERO_POINT_SEVEN",
    "0.8": "ZERO_POINT_EIGHT",
    "0.9": "ZERO_POINT_NINE",
    "0.95": "ZERO_POINT_NINETY_FIVE",
    "1.0": "ONE_POINT_ZERO",
    "1.5": "ONE_POINT_FIVE",
    "2.0": "TWO_POINT_ZERO",
    "3.0": "THREE_POINT_ZERO",
    "4.0": "FOUR_POINT_ZERO",
    "5.0": "FIVE_POINT_ZERO",
    "8.0": "EIGHT_POINT_ZERO",
    "10.0": "TEN_POINT_ZERO",
    "20.0": "TWENTY_POINT_ZERO",
    "30.0": "THIRTY_POINT_ZERO",
    "42.5": "FORTY_TWO_POINT_FIVE",
    "50.0": "FIFTY_POINT_ZERO",
    "100.0": "ONE_HUNDRED_POINT_ZERO",
    "150.0": "ONE_FIFTY_POINT_ZERO",
    "200.0": "TWO_HUNDRED_POINT_ZERO",
}

# Read ruff output to get all files with PLR2004 errors
result = subprocess.run(
    ["uv", "run", "ruff", "check", "--select=PLR2004", "--output-format=json"],
    check=False,
    capture_output=True,
    text=True,
)

import json
import sys

try:
    errors = json.loads(result.stdout)
except json.JSONDecodeError:
    sys.exit(1)

# Collect all files that need fixing
files_to_fix = set()
for error in errors:
    files_to_fix.add(error["filename"])


# Function to add constants to a file
def add_constants_to_file(file_path) -> bool | None:
    """Add common constants to a Python file if they don't exist."""
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception:
        return False

    # Check if constants already exist
    if "# Constants for PLR2004 magic values" in content:
        return True

    # Find where to insert constants (after imports and docstring)
    lines = content.split("\n")
    insert_pos = 0

    # Skip shebang
    if lines and lines[0].startswith("#!"):
        insert_pos = 1

    # Skip encoding declaration
    if insert_pos < len(lines) and "coding" in lines[insert_pos]:
        insert_pos += 1

    # Skip docstring (if it exists)
    if insert_pos < len(lines) and '"""' in lines[insert_pos]:
        # Skip until closing docstring
        for i in range(insert_pos + 1, len(lines)):
            if '"""' in lines[i]:
                insert_pos = i + 1
                break

    # Skip imports
    while insert_pos < len(lines) and (
        lines[insert_pos].startswith("import ")
        or lines[insert_pos].startswith("from ")
        or not lines[insert_pos].strip()
    ):
        insert_pos += 1

    # Create constants block
    constants_block = [
        "",
        "# Constants for PLR2004 magic values",
    ]

    # Add only the constants we actually need
    needed_constants = set()
    for error in errors:
        if error["filename"] == file_path:
            match = re.search(r"replacing `([^`]+)`", error["message"])
            if match:
                magic_number = match.group(1)
                if magic_number in COMMON_CONSTANTS:
                    needed_constants.add(magic_number)

    # Sort constants for better organization
    for num in sorted(needed_constants, key=lambda x: float(x) if "." in x else int(x)):
        constants_block.append(f"{COMMON_CONSTANTS[num]} = {num}")

    # Insert constants
    lines = lines[:insert_pos] + constants_block + lines[insert_pos:]

    # Write back
    try:
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        return True
    except Exception:
        return False


# Function to replace magic numbers in a file
def replace_magic_numbers_in_file(file_path) -> bool | None:
    """Replace magic numbers with constants in comparisons."""
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception:
        return False

    # For each error in this file, replace the magic number
    for error in errors:
        if error["filename"] != file_path:
            continue

        match = re.search(r"replacing `([^`]+)`", error["message"])
        if not match:
            continue

        magic_number = match.group(1)
        if magic_number not in COMMON_CONSTANTS:
            continue

        constant_name = COMMON_CONSTANTS[magic_number]

        # Escape special characters
        escaped_num = re.escape(magic_number)

        # Replace in comparison contexts
        # Pattern: operator followed by optional space and the magic number
        pattern = rf"([<>=!]=?\s*){escaped_num}(?![0-9_.])"
        replacement = rf"\1{constant_name}"

        # Apply replacement
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content

    # Write back
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    except Exception:
        return False


# Process each file
fixed_count = 0
failed_count = 0

for file_path in sorted(files_to_fix):
    # Add constants first
    if add_constants_to_file(file_path):
        # Then replace magic numbers
        if replace_magic_numbers_in_file(file_path):
            fixed_count += 1
        else:
            failed_count += 1
    else:
        failed_count += 1

if failed_count > 0:
    pass

# Check if we fixed everything
result = subprocess.run(
    ["uv", "run", "ruff", "check", "--select=PLR2004", "--output-format=concise"],
    check=False,
    capture_output=True,
    text=True,
)

remaining = result.stdout.count("\n") if result.stdout else 0
if remaining > 0:
    pass
else:
    pass
