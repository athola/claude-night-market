# Hookify Plugin Makefile
# Hook generation and pattern matching utilities
#
# Uses shared Make includes from abstract plugin

.PHONY: help dev-setup clean status debug-variables \
        demo-matchers demo-rules plugin-check test

# Plugin-specific variables (must be before include)
SRC_DIRS := core matchers utils scripts hooks tests
RUFF_TARGETS := core/ matchers/ utils/ scripts/ hooks/ tests/
MYPY_TARGETS := core/ matchers/ utils/ scripts/
BANDIT_TARGETS := core/ matchers/ utils/ scripts/
COV_DIRS := core matchers utils
PYTEST_TARGETS := tests/

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# ---------- Help ----------
help: ## Show this help message
	@echo "Hookify Plugin - Make Targets"
	@echo "============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Setup ----------
dev-setup: ## Install development dependencies
	@echo "Installing development dependencies..."
	$(UV) sync --all-extras
	$(UV_RUN) pre-commit install || true

# ---------- Maintenance ----------
clean: ## Clean build artifacts and cache
	@echo "Cleaning build artifacts..."
	rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Hookify Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Agents:   $$(find agents/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Python:   $$(find . -name '*.py' -not -path '*/__pycache__/*' 2>/dev/null | wc -l) files"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "RUFF_TARGETS: $(RUFF_TARGETS)"
	@echo "MYPY_TARGETS: $(MYPY_TARGETS)"

# ---------- Demo/Dogfood Targets ----------
demo-matchers: ## Demo pattern matcher functionality
	@echo "=== Hookify Pattern Matchers Demo ==="
	@echo "Available matchers:"
	@for f in matchers/*.py; do \
		name=$$(basename "$$f" .py); \
		[ "$$name" != "__init__" ] && echo "  - $$name"; \
	done 2>/dev/null || echo "  (no matchers found)"

demo-rules: ## Demo rule engine functionality
	@echo "=== Hookify Rule Engine Demo ==="
	@echo "Core modules:"
	@for f in core/*.py; do \
		name=$$(basename "$$f" .py); \
		[ "$$name" != "__init__" ] && echo "  - $$name"; \
	done 2>/dev/null || echo "  (no modules found)"

plugin-check: demo-matchers demo-rules status ## Run all demo workflows
	@echo ""
	@echo "=== Hookify Plugin Check Complete ==="

# ---------- Testing ----------
test: test-unit ## Run all tests

# Include local overrides if they exist
Makefile.local:;
-include Makefile.local
