# config/make/common.mk - Common variables and tool detection
# Include this at the top of your Makefile: include config/make/common.mk

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Run all recipe lines in single shell (performance + variable persistence)
.ONESHELL:

# Tool detection with helpful error messages
PYTHON ?= python3
UV ?= uv

# Verify required tools are available (fail fast with actionable errors)
ifeq ($(shell command -v $(UV) 2>/dev/null),)
$(error uv is required but not installed. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh)
endif

ifeq ($(shell command -v $(PYTHON) 2>/dev/null),)
$(error $(PYTHON) is required but not installed. Install Python 3.10+ from python.org or your package manager)
endif

# Optional tool detection (warn but don't fail)
HAS_PRE_COMMIT := $(shell command -v pre-commit 2>/dev/null)
HAS_SPHINX := $(shell $(PYTHON) -c "import sphinx" 2>/dev/null && echo yes)

# Tool commands - abstracted for single-point-of-change
UV_RUN := $(UV) run
UV_PYTHON := $(UV_RUN) python
PYTEST := $(UV_RUN) pytest
MYPY := $(UV_RUN) mypy
RUFF := $(UV_RUN) ruff
BANDIT := $(UV_RUN) bandit
SPHINXBUILD := $(UV_RUN) sphinx-build

# Directories (configurable for portability)
BUILD_DIR ?= build
DIST_DIR ?= dist
COV_DIR ?= htmlcov
DOCS_BUILD_DIR ?= docs/build
PYTHONPATH ?= src

# Source directories (override via environment or Makefile.local)
SCRIPTS_DIR ?= scripts
HOOKS_DIR ?= hooks
SKILLS_DIR ?= skills
# Note: SRC_DIRS should be set by each plugin BEFORE including this file
# Default only applies if plugin doesn't set it
SRC_DIRS ?= $(SCRIPTS_DIR)

# Helper function to check if a file exists
define file_exists
$(shell test -f $(1) && echo yes || echo no)
endef

# Helper macro to require TARGET argument (reduces repetition in skill analysis targets)
# Note: We use TARGET instead of PATH because PATH is a reserved environment variable
define require_path
@test -n "$(TARGET)" || { echo "Usage: make $(1) TARGET=<path>"; exit 1; }
endef
