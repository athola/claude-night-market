# Imbue Plugin Makefile
# Review workflow management and evidence logging
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help install install-dev test test-unit test-integration test-performance test-all test-coverage \
        test-slow test-parallel lint format format-check type-check typecheck security clean docs check-all ci \
        dev-setup dev-test dev-check validate-plugin deps deps-report status profile-tests mutation-test benchmark \
        demo-catchup demo-review demo-skills plugin-check debug-variables

# Override source directories for this plugin
SRC_DIRS := scripts
RUFF_TARGETS := .
MYPY_TARGETS := scripts/
BANDIT_TARGETS := scripts/
COV_DIRS := scripts
COV_REPORTS := --cov-report=html --cov-report=xml --cov-fail-under=85
TEST_UNIT_TARGETS := tests/unit/
TEST_UNIT_ARGS := -v
TEST_COVERAGE_TARGETS := tests/
TEST_COVERAGE_ARGS :=
SECURITY_EXTRA = $(UV_RUN) safety check

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Prevent parallel execution for targets that share resources
.NOTPARALLEL: docs

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
	$(PYTEST) tests/

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ -v

test-performance: ## Run performance tests only
	$(PYTEST) tests/performance/ -v -m performance

test-slow: ## Run slow tests
	$(PYTEST) tests/ -v -m slow

test-all: ## Run detailed test suite with coverage
	$(PYTEST) tests/ -v --cov=scripts --cov-report=html --cov-report=term-missing

test-parallel: ## Run tests in parallel for speed
	$(PYTEST) tests/ -n auto

# Code Quality
format-check: ## Check if code is formatted correctly
	$(RUFF) format --check .

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
	$(PYTEST) tests/unit/ -x --tb=short

dev-check: ## Quick development checks (lint + unit tests)
	@echo "Running development checks..."
	$(MAKE) lint
	$(MAKE) dev-test
	@echo "Development checks completed!"

# Performance Profiling
profile-tests: ## Profile test execution times
	$(PYTEST) tests/ --durations=0

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

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate scripts --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks
	@if $(PYTEST) --benchmark-only --benchmark-sort=mean 2>/dev/null; then \
		echo "Benchmarks complete"; \
	else \
		echo "pytest-benchmark not installed (pip install pytest-benchmark)"; \
	fi

# ---------- Demo/Dogfood Targets (LIVE) ----------
demo-catchup: ## Demo catchup workflow (LIVE)
	@echo "=== Imbue Catchup Demo (LIVE) ==="
	@echo ""
	@echo "Branch: $$(git rev-parse --abbrev-ref HEAD)"
	@git log --oneline -5
	@echo ""
	@git diff --stat HEAD~3..HEAD 2>/dev/null || git diff --stat HEAD~1..HEAD
	@echo ""
	@echo "Use /imbue:catchup for full workflow."

demo-validator: ## Demo imbue validator (LIVE)
	@echo "=== Imbue Validator Demo (LIVE) ==="
	@echo ""
	$(UV_RUN) python scripts/imbue_validator.py --root . --report

demo-skills: ## List imbue skills
	@echo "=== Imbue Skills ==="
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done

plugin-check: demo-catchup demo-validator demo-skills ## Run all live demos
	@echo ""
	@echo "=== Imbue Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1

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
