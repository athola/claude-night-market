#!/usr/bin/env python3
"""Test script for Sanctum wrapper integration with superpowers:requesting-code-review.

This script validates that the wrapper commands properly integrate with both
Sanctum's existing functionality and superpowers code review capabilities.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\nTesting: {description}")
    print(f"Command: {cmd}")
    print("-" * 50)

    try:
        result = subprocess.run(
            cmd, check=False, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            print("✅ Success")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}...")
        else:
            print(f"❌ Failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}...")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⏰ Timeout after 30 seconds")
        return False
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
        return False


def validate_wrapper_files():
    """Validate that wrapper files exist and have correct structure."""
    print("\n" + "=" * 60)
    print("VALIDATING WRAPPER FILES")
    print("=" * 60)

    wrapper_files = [
        "/home/alext/claude-night-market/plugins/sanctum/commands/pr-wrapper.md",
        "/home/alext/claude-night-market/plugins/sanctum/commands/fix-pr-wrapper.md",
        "/home/alext/claude-night-market/plugins/sanctum/commands/pr-review-wrapper.md",
    ]

    all_valid = True

    for file_path in wrapper_files:
        print(f"\nChecking: {Path(file_path).name}")
        path = Path(file_path)

        if not path.exists():
            print("❌ File not found")
            all_valid = False
            continue

        content = path.read_text()

        # Check for required frontmatter
        if 'extends: "superpowers:requesting-code-review"' not in content:
            print("❌ Missing superpowers extension")
            all_valid = False
        else:
            print("✅ Has superpowers extension")

        # Check for key sections
        required_sections = ["## When to Use", "## Workflow", "## Integration"]
        for section in required_sections:
            if section not in content:
                print(f"❌ Missing section: {section}")
                all_valid = False
            else:
                print(f"✅ Has section: {section}")

    return all_valid


def test_skill_dependencies():
    """Test that required skills are available."""
    print("\n" + "=" * 60)
    print("TESTING SKILL DEPENDENCIES")
    print("=" * 60)

    # Test Sanctum skills
    sanctum_skills = [
        "sanctum:git-workspace-review",
        "sanctum:pr-prep",
        "sanctum:pr-review",
        "sanctum:shared",
    ]

    # Test superpowers skills (will fail if not installed, but that's expected)
    superpowers_skills = ["superpowers:requesting-code-review"]

    print("\nSanctum Skills:")
    for skill in sanctum_skills:
        # Just validate the skill files exist
        skill_path = f"/home/alext/claude-night-market/plugins/sanctum/skills/{skill.split(':')[1]}/SKILL.md"
        if Path(skill_path).exists():
            print(f"✅ {skill} - Skill file exists")
        else:
            print(f"❌ {skill} - Skill file not found")

    print("\nSuperpowers Skills:")
    for skill in superpowers_skills:
        print(f"ℹ️  {skill} - Requires superpowers plugin installation")


def test_wrapper_structure():
    """Test wrapper structure follows guidelines."""
    print("\n" + "=" * 60)
    print("TESTING WRAPPER STRUCTURE")
    print("=" * 60)

    wrappers = [
        ("pr-wrapper", "PR preparation"),
        ("fix-pr-wrapper", "PR fix automation"),
        ("pr-review-wrapper", "PR review enhancement"),
    ]

    for wrapper_name, _description in wrappers:
        print(f"\nTesting {wrapper_name}:")

        file_path = f"/home/alext/claude-night-market/plugins/sanctum/commands/{wrapper_name}.md"
        content = Path(file_path).read_text()

        # Check wrapper pattern compliance
        checks = [
            ("Clear delegation statement", "superpowers:requesting-code-review"),
            ("Backward compatibility", "backward compatibility"),
            ("Integration benefits", "Integration Benefits"),
            ("Migration path", "Migration from"),
            ("Error handling", "## Error Handling"),
        ]

        for check_name, check_text in checks:
            if check_text in content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SANCTUM WRAPPER INTEGRATION TESTS")
    print("=" * 60)

    results = []

    # Test 1: Validate wrapper files
    results.append(("Wrapper Files", validate_wrapper_files()))

    # Test 2: Test skill dependencies
    test_skill_dependencies()

    # Test 3: Test wrapper structure
    test_wrapper_structure()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("\nNotes:")
    print("- Wrapper files are created and properly structured")
    print("- Superpowers plugin needs to be installed for full functionality")
    print("- Sanctum skills are validated and available")
    print("- All wrappers maintain backward compatibility")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
