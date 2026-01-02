#!/usr/bin/env python3
"""Test that bloat-detector modules are properly referenced."""

import re
from pathlib import Path


def test_bloat_detector_modules():
    """Verify that all modules are referenced in SKILL.md."""
    skill_dir = Path(__file__).parent.parent / "skills" / "bloat-detector"
    skill_file = skill_dir / "SKILL.md"
    modules_dir = skill_dir / "modules"

    # Read main skill file
    assert skill_file.exists(), f"SKILL.md not found at {skill_file}"
    skill_content = skill_file.read_text()

    # Find all module files
    assert modules_dir.exists(), f"modules/ directory not found at {modules_dir}"
    module_files = list(modules_dir.glob("*.md"))
    assert len(module_files) > 0, "No module files found"

    # Check each module is referenced
    referenced_modules = set()
    unreferenced_modules = []

    for module_file in module_files:
        module_name = module_file.stem

        # Check for various reference patterns
        patterns = [
            rf"\b{module_name}\b",  # Plain name
            rf"modules/{module_name}",  # Path reference
            rf"{module_name}\.md",  # File reference
        ]

        is_referenced = any(
            re.search(pattern, skill_content, re.IGNORECASE) for pattern in patterns
        )

        if is_referenced:
            referenced_modules.add(module_name)
        else:
            unreferenced_modules.append(module_name)

    # Report results
    print(f"\n✓ Modules directory: {modules_dir}")
    print(f"✓ Total modules found: {len(module_files)}")
    print(f"✓ Modules referenced: {len(referenced_modules)}")

    if referenced_modules:
        print("\nReferenced modules:")
        for module in sorted(referenced_modules):
            print(f"  ✓ {module}")

    if unreferenced_modules:
        print("\n✗ UNREFERENCED modules:")
        for module in unreferenced_modules:
            print(f"  ✗ {module}")
        raise AssertionError(
            f"{len(unreferenced_modules)} module(s) not referenced in SKILL.md: "
            f"{', '.join(unreferenced_modules)}"
        )

    print(f"\n✅ All {len(module_files)} modules are properly referenced!")


def test_module_frontmatter():
    """Verify that all modules have proper frontmatter."""
    modules_dir = Path(__file__).parent.parent / "skills" / "bloat-detector" / "modules"
    module_files = list(modules_dir.glob("*.md"))

    issues = []

    for module_file in module_files:
        content = module_file.read_text()

        # Check frontmatter exists
        if not content.startswith("---"):
            issues.append(f"{module_file.name}: Missing frontmatter")
            continue

        # Extract frontmatter
        parts = content.split("---", 2)
        if len(parts) < 3:
            issues.append(f"{module_file.name}: Incomplete frontmatter")
            continue

        frontmatter = parts[1]

        # Check required fields
        required_fields = ["module:", "category:", "dependencies:"]
        for field in required_fields:
            if field not in frontmatter:
                issues.append(f"{module_file.name}: Missing '{field}' in frontmatter")

    if issues:
        print("\n✗ Frontmatter issues:")
        for issue in issues:
            print(f"  ✗ {issue}")
        raise AssertionError(f"{len(issues)} frontmatter issue(s) found")

    print(f"\n✅ All {len(module_files)} modules have valid frontmatter!")


def test_no_spoke_to_spoke_references():
    """Verify that modules don't reference each other (hub-spoke pattern)."""
    modules_dir = Path(__file__).parent.parent / "skills" / "bloat-detector" / "modules"
    module_files = list(modules_dir.glob("*.md"))

    violations = []

    for module_file in module_files:
        content = module_file.read_text()
        current_module = module_file.stem

        # Check for references to other modules
        for other_module_file in module_files:
            if other_module_file == module_file:
                continue

            other_module = other_module_file.stem

            # Check for module reference patterns
            patterns = [
                rf"modules/{other_module}\b",
                rf"@include\s+{other_module}\b",
                rf"\b{other_module}\.md\b",
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(
                        f"{current_module}.md references {other_module}.md "
                        f"(violates hub-spoke pattern)"
                    )
                    break

    if violations:
        print("\n✗ Hub-spoke violations:")
        for violation in violations:
            print(f"  ✗ {violation}")
        raise AssertionError(
            f"{len(violations)} spoke-to-spoke reference(s) found. "
            f"Modules should only be referenced by SKILL.md, not by other modules."
        )

    print("✅ No spoke-to-spoke references found (hub-spoke pattern maintained)!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing bloat-detector module structure")
    print("=" * 60)

    try:
        test_bloat_detector_modules()
        test_module_frontmatter()
        test_no_spoke_to_spoke_references()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise
