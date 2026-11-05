# config/make/markdown-only.mk - Markdown-only plugin defaults
# Use for plugins without Python/uv dependencies.

# Every plugin Makefile defines `help:`. Pinned because the
# debug-variables rule below would otherwise be the first rule read.
.DEFAULT_GOAL := help

include $(dir $(lastword $(MAKEFILE_LIST)))base.mk

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

.PHONY: debug-variables
debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "SHELL: $(SHELL)"
	@echo "SHELLFLAGS: $(.SHELLFLAGS)"
	@echo "SKILLS_DIR: $(SKILLS_DIR)"
	@echo "COMMANDS_DIR: $(COMMANDS_DIR)"
	@echo "AGENTS_DIR: $(AGENTS_DIR)"
	@echo "DOCS_DIR: $(DOCS_DIR)"
	@echo "SCRIPTS_DIR: $(SCRIPTS_DIR)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "MAKEFLAGS: $(MAKEFLAGS)"
