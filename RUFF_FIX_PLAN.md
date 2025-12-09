# Ruff Issues Fix Plan

## Overview
Fix all 4493 remaining ruff issues discovered by `uv run ruff check --fix --unsafe-fixes`. Issues are categorized as follows:

## Tasks

### Task 1: Fix Line Length Issues (E501)
- **Description**: Fix all lines exceeding 88 characters
- **Files affected**: Multiple files across plugins
- **Approach**: Break long lines, use string concatenation, extract variables

### Task 2: Fix Import Placement Issues (PLC0415)
- **Description**: Move imports to top-level of files
- **Files affected**: plugins/abstract/examples/sanctum_integration_example.py
- **Approach**: Move imports to module level, reorganize as needed

### Task 3: Fix Magic Number Issues (PLR2004)
- **Description**: Replace magic numbers with named constants
- **Files affected**: Multiple test files and examples
- **Approach**: Define constants at module level for repeated values

### Task 4: Fix Exception Handling Issues (S110)
- **Description**: Replace try-except-pass with proper logging
- **Files affected**: plugins/abstract/examples/sanctum_integration_example.py
- **Approach**: Add appropriate logging or handling

### Task 5: Fix Ruff Configuration Deprecation Warnings
- **Description**: Update ruff configuration to use new `lint` section format
- **Files affected**: plugins/pensive/pyproject.toml, plugins/parseltongue/pyproject.toml, plugins/memory-palace/hooks/pyproject.toml
- **Approach**: Migrate configuration to new format

### Task 6: Final Verification
- **Description**: Run final ruff check to ensure all issues are resolved
- **Approach**: Execute `uv run ruff check` and verify clean output
