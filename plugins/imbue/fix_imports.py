#!/usr/bin/env python3
"""Fix ruff import issues in test files."""

import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> None:
    """Fix imports in a single file."""
    content = file_path.read_text()

    # Find all inline imports
    inline_imports = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#'):
            # Skip if it's already at the top (first 50 lines)
            if i < 50:
                continue
            inline_imports.append((i, line.strip()))

    if not inline_imports:
        return

    # Extract unique imports
    unique_imports = set()
    for _, import_line in inline_imports:
        unique_imports.add(import_line)

    # Find where to add imports (after existing imports)
    import_section_end = 0
    for i, line in enumerate(lines):
        if line.strip().startswith(('import ', 'from ')):
            import_section_end = i + 1
        elif line.strip().startswith('#') and i < 30:
            # Skip comments
            continue
        elif not line.strip() and i < import_section_end + 5:
            # Allow empty lines after imports
            continue
        elif import_section_end > 0 and i > import_section_end + 5:
            break

    # Insert new imports
    new_imports = sorted(unique_imports)
    insert_pos = import_section_end

    for imp in new_imports:
        lines.insert(insert_pos, imp)
        insert_pos += 1

    # Remove inline imports
    # Work backwards to avoid line number changes
    for line_idx, _ in reversed(inline_imports):
        # Remove the import line
        lines.pop(line_idx)
        # Also remove the next line if it's empty
        if line_idx < len(lines) and not lines[line_idx].strip():
            lines.pop(line_idx)

    # Write back
    file_path.write_text('\n'.join(lines))


def main():
    """Fix all test files."""
    test_dir = Path('tests')

    for py_file in test_dir.rglob('*.py'):
        if 'conftest.py' in str(py_file):
            continue  # Skip conftest files
        fix_imports_in_file(py_file)


if __name__ == '__main__':
    main()