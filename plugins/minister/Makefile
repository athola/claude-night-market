# Minister Plugin Makefile
# Project and initiative tracking for development workflows
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps test test-unit test-integration test-bdd test-coverage lint format type-check typecheck \
        security clean install-hooks status ci demo-tracking demo-initiatives demo-skills plugin-check

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Plugin-specific variables
SRC_DIRS ?= src tests scripts

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
	uv run pytest tests/ -v

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	uv run pytest tests/integration/ -v

test-bdd: ## Run BDD scenario tests
	uv run pytest tests/bdd/ -v

test-coverage: ## Run tests with coverage report
	uv run pytest tests/ --cov=src/minister --cov-report=term-missing --cov-report=html

# ---------- Code Quality ----------
lint: ## Run linting checks
	@echo "Running linting checks..."
	uv run ruff check $(SRC_DIRS) || { echo "⚠ Linting failed"; exit 1; }

format: ## Format code
	@echo "Formatting code..."
	uv run ruff format $(SRC_DIRS)
	uv run ruff check --fix $(SRC_DIRS)

type-check: ## Run type checking
	@echo "Running type checking..."
	uv run mypy src/ || { echo "⚠ Type checking failed"; exit 1; }

# Alias for backwards compatibility
typecheck: type-check

security: ## Run security checks
	@echo "Running security checks..."
	uv run bandit -r src/ || { echo "⚠ Security check failed"; exit 1; }

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

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -f .pre-commit-config.yaml ]; then \
		uv run pre-commit install; \
	else \
		echo "No .pre-commit-config.yaml found"; \
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
