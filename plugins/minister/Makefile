# Minister Plugin Makefile
# Project and initiative tracking for development workflows
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps test test-unit test-integration test-bdd test-coverage lint format type-check typecheck \
        security clean install-hooks status ci mutation-test benchmark demo-tracking demo-initiatives demo-skills plugin-check debug-variables

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests scripts
COV_DIRS := src/minister
MYPY_TARGETS := src/
BANDIT_TARGETS := src/
TEST_UNIT_TARGETS := tests/unit/
TEST_UNIT_ARGS := -v

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Default target
help: ## Show this help message
	@echo "Minister Plugin - Make Targets"
	@echo "==============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Dependencies ----------
deps: ## Install and sync dependencies
	uv sync

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST) tests/ -v

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ -v

test-bdd: ## Run BDD scenario tests
	$(PYTEST) tests/bdd/ -v

# ---------- CI ----------
ci: lint type-check test ## Run CI pipeline
	@echo "CI pipeline completed!"

# ---------- Maintenance ----------
clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Minister Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Source:   $$(find src/ -name '*.py' 2>/dev/null | wc -l) Python files"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SHELL: $(SHELL)"
	@echo "SHELLFLAGS: $(SHELLFLAGS)"
	@echo "PYTHONPATH: $(PYTHONPATH)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "RUFF_TARGETS: $(RUFF_TARGETS)"
	@echo "MYPY_TARGETS: $(MYPY_TARGETS)"
	@echo "BANDIT_TARGETS: $(BANDIT_TARGETS)"
	@echo "COV_DIRS: $(COV_DIRS)"
	@echo "PYTEST_TARGETS: $(PYTEST_TARGETS)"
	@echo "MAKEFLAGS: $(MAKEFLAGS)"

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -f .pre-commit-config.yaml ]; then \
		uv run pre-commit install; \
	else \
		echo "No .pre-commit-config.yaml found"; \
	fi

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate src/minister --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks
	@if $(PYTEST) --benchmark-only --benchmark-sort=mean 2>/dev/null; then \
		echo "Benchmarks complete"; \
	else \
		echo "pytest-benchmark not installed (pip install pytest-benchmark)"; \
	fi

# ---------- Demo/Dogfood Targets ----------
demo-tracking: ## Demo project tracking on minister itself
	@echo "=== Minister Tracking Demo ==="
	@echo "Demonstrating project tracking capabilities..."
	@echo ""
	@echo "Step 1: Project metrics"
	@echo "Python files: $$(find src/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Test files: $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "Data files: $$(find data/ -type f 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 2: Project tracker check"
	@uv run python -c "from minister.project_tracker import *; print('ProjectTracker available')" 2>/dev/null || echo "  (project tracker not loaded)"
	@echo ""
	@echo "Tracking demo complete."

demo-initiatives: ## Demo initiative management
	@echo "=== Minister Initiatives Demo ==="
	@echo "Demonstrating initiative tracking..."
	@echo ""
	@echo "Step 1: Test structure"
	@echo "Unit tests: $$(find tests/unit -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "Integration tests: $$(find tests/integration -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "BDD scenarios: $$(find tests/bdd -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 2: Data directory"
	@ls data/ 2>/dev/null | head -5 || echo "  (no data files)"
	@echo ""
	@echo "Initiatives demo complete."

demo-skills: ## Validate minister skill structure
	@echo "=== Minister Skills Demo ==="
	@echo "Project management skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no skills found)"
	@echo ""
	@echo "Commands:"
	@find commands/ -name "*.md" 2>/dev/null | wc -l | xargs -I{} echo "  {} commands defined"

plugin-check: demo-tracking demo-initiatives demo-skills status ## Run all demo workflows
	@echo ""
	@echo "=== Minister Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
