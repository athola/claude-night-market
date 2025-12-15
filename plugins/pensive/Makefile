# Pensive Plugin Makefile
# Code review and quality analysis tools
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: all test test-unit test-integration test-edge-case coverage coverage-check lint format \
        type-check quality-check clean dev-install install test-parallel security perf-test \
        docs docs-serve test-file test-pattern duplication-check complexity-check deps-update \
        deps-outdated mutation-test dev ci benchmark memory-profile coverage-badge test-structure \
        help status demo-makefile-review demo-bug-review demo-skills plugin-check

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Default target
all: test lint ## Run tests and linting

# ---------- Testing ----------
test: ## Run all tests
	pytest -v

test-unit: ## Run only unit tests
	pytest -v -m unit

test-integration: ## Run only integration tests
	pytest -v -m integration

test-edge-case: ## Run edge case tests
	pytest -v -m edge_case

coverage: ## Run tests with coverage report
	pytest --cov=pensive --cov-report=html --cov-report=term-missing

coverage-check: ## Check coverage meets 85% threshold
	pytest --cov=pensive --cov-fail-under=85 --cov-report=term-missing

test-parallel: ## Run tests in parallel
	pytest -n auto -v

test-file: ## Run specific test file (FILE=path)
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-file FILE=path/to/test.py"; exit 1; fi
	pytest -v $(FILE)

test-pattern: ## Run tests matching pattern (PATTERN=name)
	@if [ -z "$(PATTERN)" ]; then echo "Usage: make test-pattern PATTERN=test_name"; exit 1; fi
	pytest -v -k "$(PATTERN)"

# ---------- Code Quality ----------
lint: ## Run linting checks
	ruff check $(SRC_DIRS) || { echo "⚠ Linting failed"; exit 1; }

format: ## Format code
	ruff format $(SRC_DIRS)

type-check: ## Run type checking
	mypy src/ || { echo "⚠ Type checking failed"; exit 1; }

security: ## Run security checks
	bandit -r src/ || { echo "⚠ Security check failed"; exit 1; }
	safety check || echo "⚠ Safety check unavailable"

quality-check: format lint type-check coverage-check ## Run all quality checks
	@echo "All quality checks passed!"

# ---------- Installation ----------
dev-install: ## Install in development mode
	pip install -e ".[dev]"

install: ## Install for production
	pip install .

# ---------- Documentation ----------
docs: ## Generate documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

# ---------- Analysis ----------
duplication-check: ## Check for duplicate code
	radon cc src/ --min B
	radon mi src/

complexity-check: ## Analyze code complexity
	radon cc src/ --min B
	xenon --max-absolute B --max-modules A --max-average A src/ || true

perf-test: ## Run performance tests
	pytest -v -m performance --benchmark-only

benchmark: ## Run performance benchmarks
	pytest --benchmark-only --benchmark-sort=mean

memory-profile: ## Profile memory usage
	python -m memory_profiler tests/performance/memory_usage.py || echo "memory_profiler not installed"

mutation-test: ## Run mutation testing
	mutmut run --paths-to-mutate src/ || echo "mutmut not installed"

test-structure: ## Verify test structure
	@echo "Checking test structure..."
	@echo "Test files: $$(find tests/ -name 'test_*.py' | wc -l)"
	@echo "Test functions: $$(grep -r 'def test_' tests/ | wc -l)"
	@echo "Test classes: $$(grep -r 'class Test' tests/ | wc -l)"

# ---------- Dependencies ----------
deps-update: ## Update dependencies
	pip install --upgrade pip
	pip install --upgrade -e ".[dev]"

deps-outdated: ## Check for outdated dependencies
	pip list --outdated

# ---------- Workflows ----------
dev: format lint test-unit ## Quick development loop

ci: format lint type-check security coverage-check ## Full CI pipeline
	@echo "CI pipeline completed successfully!"

# ---------- Maintenance ----------
clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage .mypy_cache/ .ruff_cache/ 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Pensive Plugin Status:"
	@echo "Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Tests:  $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "Source: $$(find src/ -name '*.py' 2>/dev/null | wc -l) Python files"

coverage-badge: ## Generate coverage badge
	coverage-badge -o docs/coverage.svg || echo "coverage-badge not installed"

# ---------- Demo/Dogfood Targets ----------
demo-makefile-review: ## Demo Makefile review on this plugin's Makefile
	@echo "=== Pensive Makefile Review Demo ==="
	@echo "Demonstrating makefile-review skill on this Makefile..."
	@echo ""
	@echo "Step 1: Structure Check"
	@echo "Targets defined: $$(grep -cE '^[a-zA-Z_-]+:' Makefile)"
	@echo "PHONY declarations: $$(grep -c '.PHONY' Makefile)"
	@echo "Has help target: $$(grep -q '^help:' Makefile && echo 'yes' || echo 'no')"
	@echo ""
	@echo "Step 2: Pattern Analysis"
	@grep -E '^\s*\$$(MAKE)' Makefile | head -5 || echo "  (no recursive make calls)"
	@echo ""
	@echo "Step 3: Quality Checks"
	@echo "Uses SHELL directive: $$(grep -q '^SHELL' Makefile && echo 'yes' || echo 'no')"
	@echo "Tab indentation: $$(grep -cP '^\t' Makefile) recipe lines"
	@echo ""
	@echo "Makefile review demo complete. Use /pensive:makefile-review for full analysis."

demo-bug-review: ## Demo bug review on pensive source code
	@echo "=== Pensive Bug Review Demo ==="
	@echo "Demonstrating bug-review skill on pensive skills..."
	@echo ""
	@echo "Step 1: File Inventory"
	@find skills/ -name "*.md" -type f | head -10
	@echo ""
	@echo "Step 2: Pattern Scanning"
	@echo "TODO comments: $$(grep -r 'TODO' skills/ 2>/dev/null | wc -l)"
	@echo "FIXME comments: $$(grep -r 'FIXME' skills/ 2>/dev/null | wc -l)"
	@echo "Error patterns: $$(grep -r 'error\|Error\|ERROR' skills/ 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 3: Validation Check"
	@for skill in skills/*/SKILL.md; do \
		grep -q "## When to Use" "$$skill" || echo "  Missing usage: $$skill"; \
	done
	@echo ""
	@echo "Bug review demo complete. Use /pensive:bug-review for full analysis."

demo-skills: ## Validate pensive skill structure
	@echo "=== Pensive Skills Demo ==="
	@echo "Available review skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  api-review:       $$(test -f skills/api-review/SKILL.md && echo '✓' || echo '✗')"
	@echo "  bug-review:       $$(test -f skills/bug-review/SKILL.md && echo '✓' || echo '✗')"
	@echo "  makefile-review:  $$(test -f skills/makefile-review/SKILL.md && echo '✓' || echo '✗')"
	@echo "  test-review:      $$(test -f skills/test-review/SKILL.md && echo '✓' || echo '✗')"
	@echo "  rust-review:      $$(test -f skills/rust-review/SKILL.md && echo '✓' || echo '✗')"

plugin-check: demo-makefile-review demo-bug-review demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Pensive Plugin Check Complete ==="

# ---------- Help ----------
help: ## Show this help message
	@echo "Pensive Plugin - Make Targets"
	@echo "=============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile
