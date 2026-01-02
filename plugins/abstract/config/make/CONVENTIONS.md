# Makefile Conventions

This document establishes standards for Makefiles across the claude-night-market project.

## Include Files

All plugin Makefiles should include the shared configuration:

```make
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
```

Available includes:
- `common.mk` - Shell config, tool detection, variables
- `python.mk` - Python quality targets (format, lint, type-check, security, test-unit)
- `docs.mk` - Sphinx documentation targets

## Required Settings

Every Makefile MUST have:

```make
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c
```

This validates:
- `-e`: Exit on error
- `-u`: Error on undefined variables
- `-o pipefail`: Return first failure in pipelines

## Target Naming Standards

Use these standardized names (with aliases for backwards compatibility):

| Standard Name | NOT | Notes |
|--------------|-----|-------|
| `type-check` | `typecheck` | Hyphenated for consistency |
| `test-unit` | `unit-tests` | Verb-first pattern |
| `test-integration` | `integration-tests` | Verb-first pattern |
| `test-coverage` | `coverage-tests` | Verb-first pattern |
| `security` | `security-check` | Simple noun |
| `install-hooks` | `setup-hooks` | Action-noun pattern |

## .PHONY Declarations

ALL targets must be declared .PHONY. Group related targets:

```make
.PHONY: help all test lint clean \
        test-unit test-integration test-coverage \
        format type-check security
```

## Variable Patterns

Use `?=` for overridable defaults:

```make
UV ?= uv
PYTHON ?= python3
SRC_DIRS ?= scripts src
```

## Error Handling

Wrap potentially failing commands:

```make
target:
	@command || { echo "WARNING: Command failed"; exit 1; }
```

For optional commands that shouldn't block:

```make
target:
	@command 2>/dev/null || true
```

## Interactive Targets

NEVER use `read -p` (breaks CI). Use variable patterns:

```make
# Good
test-file:
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-file FILE=path"; exit 1; fi
	pytest -v $(FILE)

# Bad - breaks CI/CD
test-file:
	@read -p "Enter file: " file; pytest -v $$file
```

## Help Target

Use the auto-generating awk pattern:

```make
help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
```

Add `## Description` after target names to auto-document.

## Directory Structure

```
plugin/
├── Makefile              # Plugin-specific targets
├── config/
│   └── make/            # Only in abstract (shared includes)
│       ├── common.mk
│       ├── python.mk
│       └── docs.mk
```
