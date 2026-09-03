# config/make/common.mk - Common variables and tool detection
# Include this at the top of your Makefile: include config/make/common.mk

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# .SHELLFLAGS and .ONESHELL arrived in GNU make 3.82. Stock macOS ships
# 3.81 from the Xcode command line tools, which ignores both, so every
# recipe below runs without -euo pipefail and a failing pipeline stage
# passes. Say so once per invocation rather than pretend the gate holds.
ifeq ($(filter 3.82 4.%,$(firstword $(MAKE_VERSION))),)
$(warning GNU make $(MAKE_VERSION) ignores .SHELLFLAGS and .ONESHELL; recipes run without -euo pipefail. Install GNU make 3.82+ (brew install make) and run gmake.)
endif

# Run all recipe lines in single shell (performance + variable persistence)
.ONESHELL:

# Tool detection with helpful error messages
PYTHON ?= python3
UV ?= uv

# Verify required tools are available (fail fast with actionable errors).
# help, clean and status need neither tool, so skip the probes for them.
ifneq ($(filter-out help clean status,$(MAKECMDGOALS)),)
ifeq ($(shell command -v $(UV) 2>/dev/null),)
$(error uv is required but not installed. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh)
endif

ifeq ($(shell command -v $(PYTHON) 2>/dev/null),)
$(error $(PYTHON) is required but not installed. Install Python 3.10+ from python.org or your package manager)
endif
endif

# Tool commands - abstracted for single-point-of-change
UV_RUN := $(UV) run
UV_RUN_PYTHON := $(UV_RUN) python
PYTEST := $(UV_RUN) pytest
MYPY := $(UV_RUN) mypy
RUFF := $(UV_RUN) ruff
BANDIT := $(UV_RUN) bandit

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
