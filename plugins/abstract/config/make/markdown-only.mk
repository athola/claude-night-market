# config/make/markdown-only.mk - Markdown-only plugin defaults
# Use for plugins without Python/uv dependencies.

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# .SHELLFLAGS arrived in GNU make 3.82. Stock macOS ships 3.81 from the
# Xcode command line tools, which parses the assignment above and ignores
# it. 3.81 does honor flags written into SHELL itself, so for the releases
# that ignore .SHELLFLAGS the flags go there, and every make runs recipes
# under -euo pipefail. The filter names the releases that ignore the
# assignment, so a make newer than 4.x keeps the plain form.
ifneq ($(filter 3.7% 3.80 3.81,$(firstword $(MAKE_VERSION))),)
SHELL := /bin/bash -euo pipefail
endif

# No .ONESHELL. 3.81 ignores it, so every recipe here was written to run
# one line per shell, and on 3.82+ it changed that: a mid-recipe exit
# ended the recipe and a cd leaked into later lines. One semantics on
# every make.

# Common directories (override via environment or Makefile.local)
SKILLS_DIR ?= skills
COMMANDS_DIR ?= commands
AGENTS_DIR ?= agents
DOCS_DIR ?= docs
SCRIPTS_DIR ?= scripts
HOOKS_DIR ?= hooks
SRC_DIRS ?= $(SKILLS_DIR) $(COMMANDS_DIR) $(AGENTS_DIR)

# Helper function to check if a file exists
define file_exists
$(shell test -f $(1) && echo yes || echo no)
endef

# Helper macro to require TARGET argument (reduces repetition in skill analysis targets)
# Note: We use TARGET instead of PATH because PATH is a reserved environment variable
define require_path
@test -n "$(TARGET)" || { echo "Usage: make $(1) TARGET=<path>"; exit 1; }
endef
