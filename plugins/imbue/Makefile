# Imbue Plugin Makefile
# Review workflow management and evidence logging
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help install install-dev test test-unit test-integration test-performance test-all test-coverage \
        test-slow test-parallel lint format format-check type-check typecheck security clean docs check-all ci \
        dev-setup dev-test dev-check validate-plugin deps deps-report status profile-tests \
        demo-catchup demo-review demo-skills plugin-check

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Override source directories for this plugin
SRC_DIRS := scripts

# Default target - auto-generated help from ## comments
help: ## Show this help message
	@echo "Imbue Plugin - Make Targets"
	@echo "============================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile

# Installation
install: ## Install the package
	uv sync

install-dev: ## Install development dependencies
	uv sync --group dev

# Testing
test: ## Run all tests
	uv run pytest tests/

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	uv run pytest tests/integration/ -v

test-performance: ## Run performance tests only
	uv run pytest tests/performance/ -v -m performance

test-slow: ## Run slow tests
	uv run pytest tests/ -v -m slow

test-all: ## Run comprehensive test suite with coverage
	uv run pytest tests/ -v --cov=scripts --cov-report=html --cov-report=term-missing

test-coverage: ## Generate coverage report
	uv run pytest tests/ --cov=scripts --cov-report=html --cov-report=xml --cov-fail-under=85

test-parallel: ## Run tests in parallel for speed
	uv run pytest tests/ -n auto

# Code Quality
lint: ## Run linting checks
	uv run ruff check .

format: ## Format code with ruff
	uv run ruff format .

format-check: ## Check if code is formatted correctly
	uv run ruff format --check .

type-check: ## Run type checking with mypy
	uv run mypy scripts/

# Alias for backwards compatibility
typecheck: type-check

security: ## Run security checks
	uv run bandit -r scripts/
	uv run safety check

# Documentation
docs: ## Generate documentation
	@echo "Documentation available in tests/README.md"

# Quality Gates
check-all: ## Run all quality checks
	@echo "Running all quality checks..."
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) security
	$(MAKE) test-coverage
	@echo "All quality checks passed!"

# CI Pipeline
ci: ## Run CI pipeline (all checks and tests)
	@echo "Running CI pipeline..."
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) security
	$(MAKE) test-all
	@echo "CI pipeline completed successfully!"

# Development Workflow
dev-setup: ## Set up development environment
	@echo "Setting up development environment..."
	uv sync --group dev
	uv run pre-commit install
	@echo "Development environment ready!"

dev-test: ## Quick development test (unit tests only, fast feedback)
	uv run pytest tests/unit/ -x --tb=short

dev-check: ## Quick development checks (lint + unit tests)
	@echo "Running development checks..."
	$(MAKE) lint
	$(MAKE) dev-test
	@echo "Development checks completed!"

# Performance Profiling
profile-tests: ## Profile test execution times
	uv run pytest tests/ --durations=0

# Validation
validate-plugin: ## Run imbue validator on the plugin
	uv run python scripts/imbue_validator.py --root . --report

# Legacy support (existing commands)
deps: ## Install and sync dependencies (legacy)
	uv sync

deps-report: ## Generate detailed dependency report (legacy)
	@echo "Imbue Plugin Dependency Report"
	@echo "==============================="
	@echo "Role: Provides review workflow and evidence logging infrastructure"
	@echo "Used by: other plugins requiring review workflows"
	@echo "External dependencies: None"

status: ## Show project overview
	@echo "Imbue Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Agents:   $$(find agents/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Scripts:  $$(find scripts/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

# ---------- Demo/Dogfood Targets ----------
demo-catchup: ## Demo catchup workflow on this repo's recent changes
	@echo "=== Imbue Catchup Demo ==="
	@echo "Demonstrating catchup methodology on recent git history..."
	@echo ""
	@echo "Step 1: Context - Current branch and status"
	@git rev-parse --abbrev-ref HEAD
	@git log --oneline -5
	@echo ""
	@echo "Step 2: Delta - Recent changes"
	@git diff --stat HEAD~3..HEAD 2>/dev/null || git diff --stat HEAD~1..HEAD
	@echo ""
	@echo "Step 3: Insights - Files changed by category"
	@echo "Skills:   $$(git diff --name-only HEAD~3..HEAD 2>/dev/null | grep -c 'skills/' || echo 0)"
	@echo "Tests:    $$(git diff --name-only HEAD~3..HEAD 2>/dev/null | grep -c 'test' || echo 0)"
	@echo "Scripts:  $$(git diff --name-only HEAD~3..HEAD 2>/dev/null | grep -c '\.py$$' || echo 0)"
	@echo ""
	@echo "Catchup demo complete. Use /imbue:catchup for full workflow."

demo-review: ## Demo review workflow on imbue's own skills
	@echo "=== Imbue Review Demo ==="
	@echo "Demonstrating review workflow on imbue skills..."
	@echo ""
	@echo "Step 1: Context - Plugin root and structure"
	@pwd
	@echo ""
	@echo "Step 2: Scope - Skills inventory"
	@find skills/ -name "SKILL.md" -exec echo "  - {}" \;
	@echo ""
	@echo "Step 3: Evidence - Skill frontmatter validation"
	@for skill in skills/*/SKILL.md; do \
		echo "Checking $$skill..."; \
		head -15 "$$skill" | grep -E '^(name|description|category):' || echo "  (frontmatter incomplete)"; \
	done
	@echo ""
	@echo "Review demo complete. Use /imbue:review for full workflow."

demo-skills: ## Validate imbue skill structure and content
	@echo "=== Imbue Skills Demo ==="
	@echo "Validating skill files..."
	@for skill in skills/*/SKILL.md; do \
		echo ""; \
		echo ">>> $$skill"; \
		head -1 "$$skill" | grep -q "^---" && echo "  ✓ Has frontmatter" || echo "  ✗ Missing frontmatter"; \
		grep -q "## When to Use" "$$skill" && echo "  ✓ Has usage section" || echo "  ✗ Missing usage section"; \
		wc -l < "$$skill" | xargs -I{} echo "  Lines: {}"; \
	done
	@echo ""
	@echo "Skills validation complete."

plugin-check: demo-catchup demo-review demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Imbue Plugin Check Complete ==="

# Cleanup
clean: ## Clean up generated files
	@echo "Cleaning up..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	uv cache clean
	@echo "Cleanup completed!"
