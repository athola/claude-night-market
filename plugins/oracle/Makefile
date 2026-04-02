# Oracle Plugin Makefile
# ONNX Runtime inference daemon for Claude Code plugins

.PHONY: help deps fix check clean \
	lint format type-check typecheck security test-unit test

# Plugin-specific variables (must be before include)
SRC_DIRS := src/oracle hooks tests
RUFF_TARGETS := src/oracle/ tests/
MYPY_TARGETS := src/oracle/
BANDIT_TARGETS := src/oracle/
COV_DIRS := src/oracle
PYTEST_TARGETS := tests/

ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Note: lint, format, type-check, typecheck, security, test-unit,
# test-coverage, test-quick are provided by python.mk

help: ## Show this help message
	@echo "Oracle Plugin - Make Targets"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

deps: ## Install dependencies
	$(UV) sync --extra dev

fix: ## Auto-fix lint issues
	$(RUFF) check --fix $(RUFF_TARGETS)

test: ## Run tests
	$(PYTEST) $(PYTEST_TARGETS) -v --tb=short

check: lint type-check test ## Run all checks
	@echo "All checks passed!"

clean: ## Clean artifacts
	rm -rf .venv .uv-cache __pycache__ .mypy_cache .pytest_cache
