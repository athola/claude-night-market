# config/make/common.mk - Common variables and tool detection
# Include this at the top of your Makefile: include config/make/common.mk

# A bare `make` must not mutate the tree. python.mk's first rule is
# `format:`, which runs `ruff format` and `ruff check --fix`, and every
# plugin includes it above its own `help:`. Without this assignment
# `.DEFAULT_GOAL` fell to that first rule, so `make` in 19 of 23
# plugins, and the root `make <plugin>` delegation that invokes exactly
# that, rewrote the source before printing anything.
#
# Explicit assignment beats first-rule order regardless of include
# position. Every plugin Makefile defines `help:`.
.DEFAULT_GOAL := help

include $(dir $(lastword $(MAKEFILE_LIST)))base.mk

# Tool detection with helpful error messages
PYTHON ?= python3
UV ?= uv

# Verify required tools are available (fail fast with actionable errors).
# help, clean and status need neither tool, so skip the probes for them.
ifneq ($(filter-out help clean status,$(or $(MAKECMDGOALS),$(.DEFAULT_GOAL))),)
ifeq ($(shell command -v $(UV) 2>/dev/null),)
$(error uv is required but not installed. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh)
endif

ifeq ($(shell command -v $(PYTHON) 2>/dev/null),)
$(error $(PYTHON) is required but not installed. Install Python 3.10+ from python.org or your package manager)
endif
endif

# $(call pytest_selection,ARGS): run pytest on a selection that can match
# nothing yet (a marker or -k no test carries). pytest's exit 5 ("no tests
# collected") prints a note; every other failure fails the target. It
# replaces `$(PYTEST) -k x || $(PYTEST) tests/`, which ran a second suite
# whenever the first failed, so a failing selected test passed the target.
pytest_selection = status=0; $(PYTEST) $(1) || status=$$?; \
	if [ $$status -eq 5 ]; then echo "No tests matched this selection (pytest exit 5)"; else exit $$status; fi

# Tool commands - abstracted for single-point-of-change
UV_RUN := $(UV) run
UV_RUN_PYTHON := $(UV_RUN) python
PYTEST := $(UV_RUN) pytest
MYPY := $(UV_RUN) mypy
RUFF := $(UV_RUN) ruff
BANDIT := $(UV_RUN) bandit
# mutmut 3 dropped --paths-to-mutate and --tests-dir, which every
# mutation-test target passes. Pinned here so the targets share one pin.
MUTMUT := $(UV_RUN) --with 'mutmut<3' mutmut

# Directories (configurable for portability)
BUILD_DIR ?= build
DIST_DIR ?= dist
COV_DIR ?= htmlcov
DOCS_BUILD_DIR ?= docs/build
# No PYTHONPATH here. Make exports a variable to recipes only when it
# came from the environment or is marked `export`, so `PYTHONPATH ?= src`
# reached no recipe and only made `debug-variables` report a value the
# recipes did not have. The one consumer sets it inline:
# `plugins/abstract/Makefile:99` writes `@PYTHONPATH=src $(PYTEST) ...`.

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

.PHONY: debug-variables
debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SHELL: $(SHELL)"
	@echo "SHELLFLAGS: $(.SHELLFLAGS)"
	@echo "PYTHONPATH: $(PYTHONPATH)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "RUFF_TARGETS: $(RUFF_TARGETS)"
	@echo "MYPY_TARGETS: $(MYPY_TARGETS)"
	@echo "BANDIT_TARGETS: $(BANDIT_TARGETS)"
	@echo "COV_DIRS: $(COV_DIRS)"
	@echo "PYTEST_TARGETS: $(PYTEST_TARGETS)"
	@echo "MAKEFLAGS: $(MAKEFLAGS)"
