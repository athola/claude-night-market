# Leyline Plugin Makefile
# Infrastructure utilities: token tracking, quota management, plugin updates
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps test test-unit test-coverage lint format type-check typecheck security clean \
        install-hooks status ci demo-tokens demo-quota demo-skills plugin-check

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests scripts

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Default target
help: ## Show this help message
	@echo "Leyline Plugin - Make Targets"
	@echo "=============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Dependencies ----------
deps: ## Install and sync dependencies
	uv sync

# ---------- Testing ----------
test: ## Run all tests
	uv run pytest tests/ -v

test-unit: ## Run unit tests only
	uv run pytest tests/ -v -m "not integration"

test-coverage: ## Run tests with coverage report
	uv run pytest tests/ --cov=src/leyline --cov-report=term-missing --cov-report=html

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
	@echo "Leyline Plugin Status:"
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
demo-tokens: ## Demo token estimation on leyline source
	@echo "=== Leyline Token Demo ==="
	@echo "Demonstrating token tracking capabilities..."
	@echo ""
	@echo "Step 1: Source code metrics"
	@echo "Python files: $$(find src/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Total lines: $$(find src/ -name '*.py' -exec cat {} \; 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 2: Token module check"
	@uv run python -c "from leyline.tokens import estimate_tokens; print(f'Token estimator available')" 2>/dev/null || echo "  (token module not loaded)"
	@echo ""
	@echo "Token demo complete."

demo-quota: ## Demo quota tracking
	@echo "=== Leyline Quota Demo ==="
	@echo "Demonstrating quota tracking capabilities..."
	@echo ""
	@echo "Step 1: Quota tracker check"
	@uv run python -c "from leyline.quota_tracker import QuotaTracker; print('QuotaTracker available')" 2>/dev/null || echo "  (quota tracker not loaded)"
	@echo ""
	@echo "Step 2: MECW module check"
	@uv run python -c "from leyline.mecw import *; print('MECW utilities available')" 2>/dev/null || echo "  (MECW module not loaded)"
	@echo ""
	@echo "Quota demo complete."

demo-skills: ## Validate leyline skill structure
	@echo "=== Leyline Skills Demo ==="
	@echo "Infrastructure skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no skills found)"
	@echo ""
	@echo "Commands:"
	@find commands/ -name "*.md" 2>/dev/null | wc -l | xargs -I{} echo "  {} commands defined"

plugin-check: demo-tokens demo-quota demo-skills status ## Run all demo workflows
	@echo ""
	@echo "=== Leyline Plugin Check Complete ==="
