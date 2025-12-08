# Makefile for spec-kit testing

.PHONY: help test test-unit test-integration test-coverage test-verbose test-parallel test-file \
        test-match lint format install clean watch coverage-badge test-performance test-slow test-quick

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Default target
help:
	@echo "Available targets:"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  install      - Install test dependencies"
	@echo "  clean        - Clean test artifacts"

# Install test dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	pytest

# Run unit tests only
test-unit:
	pytest -m "not integration"

# Run integration tests only
test-integration:
	pytest -m integration

# Run tests with coverage
test-coverage:
	pytest --cov=../skills --cov=../commands --cov=../agents --cov-report=html --cov-report=term-missing

# Run tests with verbose output
test-verbose:
	pytest -v

# Run tests in parallel
test-parallel:
	pytest -n auto

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-file FILE=test_file.py"; exit 1; fi
	pytest $(FILE)

# Run tests matching pattern
test-match:
	@if [ -z "$(PATTERN)" ]; then echo "Usage: make test-match PATTERN=test_name"; exit 1; fi
	pytest -k $(PATTERN)

# Lint code
lint:
	@echo "Running linting..."
	@echo "Note: Install ruff, mypy, black for full linting"
	# ruff check .
	# mypy .
	# black --check .

# Format code
format:
	@echo "Formatting code..."
	@echo "Note: Install black, isort for formatting"
	# black .
	# isort .

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Watch for changes and run tests
watch:
	@echo "Watching for changes... (Ctrl+C to stop)"
	@echo "Note: Install pytest-watch for this feature"
	# ptw .

# Generate coverage badge
coverage-badge:
	@echo "Generating coverage badge..."
	@echo "Note: Install coverage-badge for this feature"
	# coverage-badge -o coverage.svg

# Run performance tests
test-performance:
	pytest -m performance --benchmark-only

# Run slow tests
test-slow:
	pytest -m slow -v

# Quick test (skip slow tests)
test-quick:
	pytest -m "not slow" --maxfail=1
