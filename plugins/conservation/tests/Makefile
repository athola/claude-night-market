# Conservation Plugin Test Makefile
# Provides convenient targets for running tests with different configurations

.PHONY: help test test-unit test-integration test-performance test-verbose test-coverage test-quick \
        test-bdd test-skills test-commands test-agents test-scripts test-unit-marker test-integration-marker \
        test-performance-marker coverage clean-coverage lint format check ci test-watch test-parallel \
        test-pattern test-debug test-marker benchmark test-memory test-profile test-docs test-security \
        quality-gate help-patterns

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Default target
help:
	@echo "Conservation Plugin Test Suite"
	@echo ""
	@echo "Available targets:"
	@echo "  test           - Run all tests with coverage"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-performance - Run performance tests only"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  test-quick     - Run tests without coverage (faster)"
	@echo "  test-bdd       - Run BDD-style tests only"
	@echo "  coverage       - Generate coverage report"
	@echo "  clean-coverage - Clean coverage files"
	@echo "  lint           - Run linting"
	@echo "  format         - Format code"
	@echo "  check          - Run all checks (lint + test)"
	@echo "  ci             - Run full CI pipeline"

# Environment setup
PYTHON := python3
UV := uv

# Test configuration
TEST_DIR := tests
COVERAGE_DIR := htmlcov
COVERAGE_FILE := .coverage

# Run all tests with coverage
test:
	$(UV) run pytest $(TEST_DIR)/ --cov=scripts --cov-report=html --cov-report=term-missing -v

# Run unit tests only
test-unit:
	$(UV) run pytest $(TEST_DIR)/unit/ -v --cov=scripts --cov-report=term-missing

# Run integration tests only
test-integration:
	$(UV) run pytest $(TEST_DIR)/integration/ -v --cov=scripts --cov-report=term-missing

# Run performance tests only
test-performance:
	$(UV) run pytest $(TEST_DIR)/performance/ -v --cov=scripts --cov-report=term-missing

# Run tests with verbose output
test-verbose:
	$(UV) run pytest $(TEST_DIR)/ -vv --cov=scripts --cov-report=html

# Run tests without coverage (faster for development)
test-quick:
	$(UV) run pytest $(TEST_DIR)/ --no-cov -v

# Run BDD-style tests only
test-bdd:
	$(UV) run pytest $(TEST_DIR)/ -m bdd -v

# Run specific test categories
test-skills:
	$(UV) run pytest $(TEST_DIR)/unit/skills/ -v

test-commands:
	$(UV) run pytest $(TEST_DIR)/unit/commands/ -v

test-agents:
	$(UV) run pytest $(TEST_DIR)/unit/agents/ -v

test-scripts:
	$(UV) run pytest $(TEST_DIR)/unit/scripts/ -v

# Run tests by marker
test-unit-marker:
	$(UV) run pytest $(TEST_DIR)/ -m unit -v

test-integration-marker:
	$(UV) run pytest $(TEST_DIR)/ -m integration -v

test-performance-marker:
	$(UV) run pytest $(TEST_DIR)/ -m performance -v

# Generate coverage report only
coverage:
	$(UV) run pytest $(TEST_DIR)/ --cov=scripts --cov-report=html --cov-report=xml
	@echo "Coverage report generated in $(COVERAGE_DIR)/index.html"

# Clean coverage files
clean-coverage:
	rm -rf $(COVERAGE_DIR)
	rm -f $(COVERAGE_FILE)
	rm -f coverage.xml

# Run linting
lint:
	$(UV) run ruff check .
	$(UV) run mypy scripts/

# Format code
format:
	$(UV) run ruff format .

# Run all checks (lint + test)
check: lint test

# Full CI pipeline
ci: clean-coverage lint test
	@echo "CI pipeline completed successfully"

# Development helpers
# Watch for changes and run tests automatically
test-watch:
	$(UV) run pytest-watch $(TEST_DIR)/ -v

# Run tests in parallel for faster execution
test-parallel:
	$(UV) run pytest $(TEST_DIR)/ -n auto --cov=scripts

# Run tests with specific pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=<test-pattern>"; \
		exit 1; \
	fi
	$(UV) run pytest $(TEST_DIR)/ -k "$(PATTERN)" -v

# Debug failing tests
test-debug:
	$(UV) run pytest $(TEST_DIR)/ -v -s --tb=long

# Run tests with specific marker and verbose output
test-marker:
	@if [ -z "$(MARKER)" ]; then \
		echo "Usage: make test-marker MARKER=<marker-name>"; \
		echo "Available markers: unit, integration, performance, bdd, slow"; \
		exit 1; \
	fi
	$(UV) run pytest $(TEST_DIR)/ -m "$(MARKER)" -v

# Performance benchmarking
benchmark:
	$(UV) run pytest $(TEST_DIR)/performance/ --benchmark-only

# Memory leak detection
test-memory:
	$(UV) run pytest $(TEST_DIR)/ --memray

# Run tests with profiling
test-profile:
	$(UV) run pytest $(TEST_DIR)/ --profile

# Test documentation
test-docs:
	$(UV) run pytest --doctest-modules --doctest-glob="*.md"

# Security testing
test-security:
	$(UV) run bandit -r scripts/ -f json -o security-report.json

# Quality gates
quality-gate: test
	@if [ $$($(UV) run python -c "import json; data=json.load(open('.coverage')); coverage=data.get('totals', {}).get('percent_covered', 0); print(int(coverage))") -lt 85 ]; then \
		echo "ERROR: Coverage below 85% threshold"; \
		exit 1; \
	fi
	@echo "Quality gate passed: Coverage >= 85%"

# Help for test patterns
help-patterns:
	@echo "Common test patterns:"
	@echo "  make test-pattern PATTERN=test_context"
	@echo "  make test-pattern PATTERN=mecw"
	@echo "  make test-pattern PATTERN=token_conservation"
	@echo ""
	@echo "Common markers:"
	@echo "  make test-marker MARKER=unit"
	@echo "  make test-marker MARKER=integration"
	@echo "  make test-marker MARKER=bdd"