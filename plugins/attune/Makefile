# Attune Plugin Makefile

.PHONY: help
help:
	@echo "Attune Plugin - Project Initialization & Workflow Automation"
	@echo ""
	@echo "Available targets:"
	@echo "  help          Show this help message"
	@echo "  dev-setup     Install development dependencies"
	@echo "  test          Run test suite"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-verbose  Run tests with verbose output"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  lint          Run code linting"
	@echo "  format        Format code with ruff"
	@echo "  typecheck     Run type checking with mypy"
	@echo "  clean         Clean build artifacts and cache"

.PHONY: dev-setup
dev-setup:
	@echo "Installing development dependencies..."
	uv sync --all-extras
	uv run pre-commit install

.PHONY: test
test:
	@echo "Running test suite..."
	cd ../.. && uv run --directory plugins/attune pytest plugins/attune/tests/ -v

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	cd ../.. && uv run --directory plugins/attune pytest plugins/attune/tests/ -v -m unit

.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	cd ../.. && uv run --directory plugins/attune pytest plugins/attune/tests/ -v -m integration

.PHONY: test-verbose
test-verbose:
	@echo "Running tests with verbose output..."
	cd ../.. && uv run --directory plugins/attune pytest plugins/attune/tests/ -vv --tb=short

.PHONY: test-coverage
test-coverage:
	@echo "Running tests with coverage..."
	cd ../.. && uv run --directory plugins/attune pytest plugins/attune/tests/ --cov=scripts --cov-report=term-missing --cov-report=html

.PHONY: lint
lint:
	@echo "Running ruff linter..."
	uv run ruff check scripts/ tests/

.PHONY: format
format:
	@echo "Formatting code with ruff..."
	uv run ruff check --fix scripts/ tests/
	uv run ruff format scripts/ tests/

.PHONY: typecheck
typecheck:
	@echo "Running mypy type checker..."
	uv run mypy scripts/

.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf **/__pycache__/
	rm -rf **/*.pyc
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
