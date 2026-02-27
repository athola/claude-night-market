# Claude Night Market - Root Makefile
# Delegates to plugin Makefiles for build operations

.PHONY: help all test lint typecheck clean status validate-all plugin-check check-examples demo \
        abstract abstract-% conjure conjure-% conserve conserve-% \
        imbue imbue-% memory-palace memory-palace-% parseltongue parseltongue-% \
        pensive pensive-% sanctum sanctum-% spec-kit spec-kit-%

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Local tool cache (avoids permission issues with default locations)
UV_TOOL_DIR ?= $(abspath .)/.uv-tools
PATH := $(UV_TOOL_DIR)/ruff/bin:$(PATH)

# Plugin directories
PLUGINS_DIR := plugins
ABSTRACT_DIR := $(PLUGINS_DIR)/abstract
CONJURE_DIR := $(PLUGINS_DIR)/conjure
CONSERVE_DIR := $(PLUGINS_DIR)/conserve
IMBUE_DIR := $(PLUGINS_DIR)/imbue
MEMORY_PALACE_DIR := $(PLUGINS_DIR)/memory-palace
PARSELTONGUE_DIR := $(PLUGINS_DIR)/parseltongue
PENSIVE_DIR := $(PLUGINS_DIR)/pensive
SANCTUM_DIR := $(PLUGINS_DIR)/sanctum
SPEC_KIT_DIR := $(PLUGINS_DIR)/spec-kit
ARCHETYPES_DIR := $(PLUGINS_DIR)/archetypes
LEYLINE_DIR := $(PLUGINS_DIR)/leyline
SHARED_DIR := $(PLUGINS_DIR)/shared
MINISTER_DIR := $(PLUGINS_DIR)/minister

# All plugin directories for iteration (auto-detected)
PLUGIN_MAKEFILES := $(wildcard $(PLUGINS_DIR)/*/Makefile)
ALL_PLUGINS := $(patsubst %/Makefile,%,$(PLUGIN_MAKEFILES))

# Default target
all: lint test ## Run lint and test across all plugins

help: ## Show this help message
	@echo ""
	@echo "Claude Night Market - Make Targets"
	@echo "==================================="
	@echo ""
	@echo "Root targets (run on ALL code, not just changed files):"
	@echo "  help              Show this help message"
	@echo "  all               Run lint and test across all plugins"
	@echo "  test              Run tests in all plugins (ALL code)"
	@echo "  lint              Run linting in all plugins (ALL code)"
	@echo "  typecheck         Run type checking in all plugins (ALL code)"
	@echo "  status            Show status of all plugins"
	@echo "  clean             Clean all plugin artifacts"
	@echo "  validate-all      Validate all plugin structures"
	@echo "  plugin-check      Run demo/dogfood checks across all plugins"
	@echo "  check-examples    Verify all plugins have proper examples"
	@echo ""
	@echo "Plugin delegation (run with 'make <plugin>-<target>'):"
	@echo "  abstract-*        Abstract plugin targets (e.g., abstract-test)"
	@echo "  conjure-*         Conjure plugin targets"
	@echo "  conserve-*        Conserve plugin targets"
	@echo "  imbue-*           Imbue plugin targets"
	@echo "  memory-palace-*   Memory Palace plugin targets"
	@echo "  parseltongue-*    Parseltongue plugin targets"
	@echo "  pensive-*         Pensive plugin targets"
	@echo "  sanctum-*         Sanctum plugin targets"
	@echo "  spec-kit-*        Spec-Kit plugin targets"
	@echo ""
	@echo "Examples:"
	@echo "  make abstract-help      Show abstract plugin targets"
	@echo "  make pensive-test       Run pensive tests"
	@echo "  make sanctum-lint       Run sanctum linting"
	@echo ""
	@echo "Or use 'make -C <plugin-dir> <target>' directly"

# Aggregate targets
# NOTE: These targets run on ALL code (not just changed files)
# For changed-files-only checks, use pre-commit hooks or run scripts with --changed
test: ## Run tests in all plugins (ALL code, not just changed)
	@./scripts/run-plugin-tests.sh --all

lint: ## Run linting on all plugins (ALL code, not just changed)
	@echo "=== Running Lint on ALL Code ==="
	@echo ""
	@echo ">>> Running ruff format on plugins/..."
	@uv run ruff format --config pyproject.toml plugins/ || (echo "❌ Ruff format failed" && exit 1)
	@echo "✓ Ruff format passed"
	@echo ""
	@echo ">>> Running ruff check with auto-fix on plugins/..."
	@uv run ruff check --fix --config pyproject.toml plugins/ || (echo "❌ Ruff check failed" && exit 1)
	@echo "✓ Ruff check passed"
	@echo ""
	@echo ">>> Running ruff format again (to fix any formatting from check)..."
	@uv run ruff format --config pyproject.toml plugins/ || (echo "❌ Ruff format failed" && exit 1)
	@echo "✓ Ruff format passed"
	@echo ""
	@echo ">>> Running bandit security checks on plugins/..."
	@uv run bandit --quiet -c pyproject.toml -r plugins/ || (echo "❌ Bandit failed" && exit 1)
	@echo "✓ Bandit passed"
	@echo ""
	@echo "=== Lint Complete (All Code Checked) ==="

typecheck: ## Run type checking on all plugins (ALL code, not just changed)
	@./scripts/run-plugin-typecheck.sh --all

# Plugin delegation - Abstract
abstract-%:
	@$(MAKE) -C $(ABSTRACT_DIR) $*

abstract:
	@$(MAKE) -C $(ABSTRACT_DIR)

# Plugin delegation - Conjure
conjure-%:
	@$(MAKE) -C $(CONJURE_DIR) $*

conjure:
	@$(MAKE) -C $(CONJURE_DIR)

# Plugin delegation - Conserve
conserve-%:
	@$(MAKE) -C $(CONSERVE_DIR) $*

conserve:
	@$(MAKE) -C $(CONSERVE_DIR)

# Plugin delegation - Imbue
imbue-%:
	@$(MAKE) -C $(IMBUE_DIR) $*

imbue:
	@$(MAKE) -C $(IMBUE_DIR)

# Plugin delegation - Memory Palace
memory-palace-%:
	@$(MAKE) -C $(MEMORY_PALACE_DIR) $*

memory-palace:
	@$(MAKE) -C $(MEMORY_PALACE_DIR)

# Plugin delegation - Parseltongue
parseltongue-%:
	@$(MAKE) -C $(PARSELTONGUE_DIR) $*

parseltongue:
	@$(MAKE) -C $(PARSELTONGUE_DIR)

# Plugin delegation - Pensive
pensive-%:
	@$(MAKE) -C $(PENSIVE_DIR) $*

pensive:
	@$(MAKE) -C $(PENSIVE_DIR)

# Plugin delegation - Sanctum
sanctum-%:
	@$(MAKE) -C $(SANCTUM_DIR) $*

sanctum:
	@$(MAKE) -C $(SANCTUM_DIR)

# Plugin delegation - Spec-Kit
spec-kit-%:
	@$(MAKE) -C $(SPEC_KIT_DIR) $*

spec-kit:
	@$(MAKE) -C $(SPEC_KIT_DIR)

status: ## Show status of all plugins
	@echo "=== Plugin Status ==="
	@for plugin in $(ALL_PLUGINS); do \
		echo ""; \
		echo ">>> $$plugin:"; \
		$(MAKE) -C $$plugin status 2>/dev/null || echo "  (status unavailable)"; \
	done

clean: ## Clean all plugin artifacts
	@echo "Cleaning all plugins..."
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ]; then \
			echo "Cleaning $$plugin..."; \
			$(MAKE) -C $$plugin clean 2>/dev/null || true; \
		fi; \
	done
	@echo "Done."

validate-all: ## Validate all plugin structures
	@echo "=== Validating Plugin Structures ==="
	@for plugin in $(ALL_PLUGINS); do \
		echo ""; \
		echo ">>> Validating $$plugin:"; \
		python3 $(ABSTRACT_DIR)/scripts/validate_plugin.py $$plugin || echo "  (validation failed)"; \
	done

plugin-check: ## Run demo/dogfood checks across all plugins
	@echo "=== Running Plugin Checks (Dogfooding) ==="
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ] && grep -q "^plugin-check:" "$$plugin/Makefile"; then \
			echo ""; \
			echo ">>> $$plugin:"; \
			$(MAKE) -C $$plugin plugin-check 2>/dev/null || echo "  (plugin-check failed)"; \
		fi; \
	done
	@echo ""
	@echo "=== All Plugin Checks Complete ==="

check-examples: ## Verify all plugins have proper examples
	@echo "=== Checking Plugin Examples ==="
	@python3 tests/integration/test_all_plugin_examples.py --report
	@echo ""
	@echo "=== Example Check Complete ==="

demo: ## Demonstrate Claude Night Market capabilities
	@echo "=== Claude Night Market Demo ==="
	@echo ""
	@echo "Installed Plugins:"
	@for plugin in $(ALL_PLUGINS); do \
		name=$$(basename $$plugin); \
		desc=$$(head -5 $$plugin/.claude-plugin/plugin.json 2>/dev/null | grep '"description"' | cut -d'"' -f4 | head -c 50); \
		echo "  - $$name: $$desc..."; \
	done
	@echo ""
	@echo "Quick Commands:"
	@echo "  make help           - Show all available targets"
	@echo "  make status         - Show plugin status overview"
	@echo "  make plugin-check   - Run all plugin self-tests"
	@echo "  make test           - Run tests across all plugins"
	@echo "  make lint           - Run linting across all plugins"
	@echo ""
	@echo "Per-Plugin Commands:"
	@echo "  make <plugin>-help  - Show plugin-specific targets"
	@echo "  make <plugin>-test  - Run plugin tests"
	@echo ""
	@echo "New in v1.1.2 - Bloat Detection:"
	@echo "  make conserve-demo-bloat      - Demo bloat detection on conserve plugin"
	@echo "  /bloat-scan --level 2         - Run bloat scan in Claude Code"
	@echo "  /unbloat --from-scan report   - Safe bloat remediation"
	@echo ""
	@echo "Example: make abstract-help"
