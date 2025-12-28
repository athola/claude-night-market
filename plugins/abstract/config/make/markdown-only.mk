# config/make/markdown-only.mk - Markdown-only plugin defaults
# Use for plugins without Python/uv dependencies.

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Run all recipe lines in single shell (performance + variable persistence)
.ONESHELL:

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

# Helper macro to require PATH argument (reduces repetition in skill analysis targets)
define require_path
@test -n "$(PATH)" || { echo "Usage: make $(1) PATH=<path>"; exit 1; }
endef
