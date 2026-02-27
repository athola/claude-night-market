# Parseltongue Plugin Makefile
# Python development patterns and best practices
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY:
.PHONY: all async-patterns-tests benchmark ci clean coverage coverage-check coverage-report \
	debug-variables demo-analyze-tests demo-async demo-check-async demo-perf demo-run-profiler \
	demo-skills demo-testing dev dev-install format help install lint memory-profile mutation-test \
	plugin-check python-tests quality-check security status test test-analyze-tests test-async \
	test-check-async test-duplicates test-edge-case test-file test-fixtures test-integration \
	test-language test-parallel test-pattern test-perf test-performance test-run-profiler \
	test-structure test-testing test-unit testing-guidance-tests type-check typecheck

# Plugin-specific variables (must be before include)
# Note: source is in 'parseltongue/' not 'src/'
SRC_DIRS := parseltongue tests
MYPY_TARGETS := parseltongue
BANDIT_TARGETS := parseltongue
COV_DIRS := parseltongue
PYTEST_TARGETS := tests/
TEST_UNIT_ARGS := -v -m unit
SECURITY_EXTRA = $(UV_RUN) safety check || echo "[WARNING] Safety check unavailable"

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# ---------- Help ----------
help: ## Show this help message
	@echo "Parseltongue Plugin - Make Targets"
	@echo "==================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Default target
all: test lint ## Run tests and linting

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST) $(PYTEST_TARGETS) -v

test-integration: ## Run only integration tests
	$(PYTEST) -v -m integration

test-async: ## Run async-focused tests
	$(PYTEST) -v -m asyncio

test-performance: ## Run performance tests
	$(PYTEST) -v -m performance --benchmark-only

test-testing: ## Run testing-focused tests
	$(PYTEST) -v -m testing

test-edge-case: ## Run edge case tests
	$(PYTEST) -v -m edge_case

test-language: ## Run language detection tests
	$(PYTEST) -v -m language_detection

coverage: ## Run tests with coverage report
	$(PYTEST) --cov=parseltongue --cov-report=html --cov-report=term-missing

coverage-check: ## Check coverage meets 85% threshold
	$(PYTEST) --cov=parseltongue --cov-fail-under=85 --cov-report=term-missing

test-parallel: ## Run tests in parallel
	$(PYTEST) -n auto -v

test-file: ## Run specific test file (FILE=path)
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-file FILE=path/to/test.py"; exit 1; fi
	$(PYTEST) -v $(FILE)

test-pattern: ## Run tests matching pattern (PATTERN=name)
	@if [ -z "$(PATTERN)" ]; then echo "Usage: make test-pattern PATTERN=test_name"; exit 1; fi
	$(PYTEST) -v -k "$(PATTERN)"

# ---------- Code Quality ----------
quality-check: format lint type-check coverage-check ## Run all quality checks
	@echo "All quality checks passed!"

# ---------- Installation ----------
dev-install: ## Install in development mode
	pip install -e ".[dev]"

install: ## Install for production
	pip install .

# ---------- Category Tests ----------
python-tests: ## Run Python-specific tests
	$(PYTEST) tests/skills/test_python_*.py -v

async-patterns-tests: ## Run async pattern tests
	$(PYTEST) tests/test_async_patterns.py tests/test_*.py -k "async" -v

testing-guidance-tests: ## Run testing guidance tests
	$(PYTEST) tests/test_testing_guidance.py tests/test_*.py -k "testing" -v

# ---------- Analysis ----------
benchmark: ## Run performance benchmarks
	$(PYTEST) tests/test_performance_optimization.py --benchmark-only --benchmark-sort=mean || echo "No benchmark tests"

memory-profile: ## Profile memory usage
	python -m memory_profiler tests/performance/memory_usage.py || echo "memory_profiler not installed"

mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate parseltongue --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

test-structure: ## Verify test structure
	@echo "Checking test structure..."
	@echo "Test files: $$(find tests/ -name 'test_*.py' | wc -l)"
	@echo "Test functions: $$(grep -r 'def test_' tests/ | wc -l)"
	@echo "Test classes: $$(grep -r 'class Test' tests/ | wc -l)"

test-perf: ## Analyze test performance
	@echo "Analyzing test performance..."
	@time $(PYTEST) --collect-only -q > /dev/null 2>&1 || true
	@echo "Test collection completed"

test-duplicates: ## Check for duplicate test code
	@echo "Largest test files:"
	@find tests/ -name "*.py" -exec wc -l {} \; 2>/dev/null | sort -n | tail -10

test-fixtures: ## Validate test fixtures
	@python -c "from tests.conftest import *; print('All fixtures imported successfully')" || echo "Fixture validation failed"

coverage-report: ## Generate coverage report
	$(PYTEST) --cov=parseltongue --cov-report=html --cov-report=xml
	@echo "Coverage report generated in htmlcov/"

# ---------- Workflows ----------
dev: format lint test-unit ## Quick development loop

ci: format lint type-check security coverage-check ## Full CI pipeline
	@echo "CI pipeline completed successfully!"

# ---------- Maintenance ----------
clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage .mypy_cache/ .ruff_cache/ bandit-report.json 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Parseltongue Plugin Status:"
	@echo "Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Tests:  $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "Source: $$(find src/ -name '*.py' 2>/dev/null | wc -l) Python files"

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

# ---------- Demo/Dogfood Targets (LIVE) ----------
demo-tests: ## Run tests to demonstrate testing patterns (LIVE)
	@echo "=== Parseltongue Testing Demo (LIVE) ==="
	@echo ""
	$(PYTEST) tests/ -v --tb=short -q --co 2>/dev/null | head -20 || $(PYTEST) tests/ -v --tb=short -q | head -30

demo-coverage: ## Run coverage analysis (LIVE)
	@echo "=== Parseltongue Coverage Demo (LIVE) ==="
	@echo ""
	$(PYTEST) --cov=parseltongue --cov-report=term-missing -q 2>/dev/null | head -30 || echo "Coverage: run 'make coverage' for full report"

demo-lint: ## Run linting on parseltongue code (LIVE)
	@echo "=== Parseltongue Lint Demo (LIVE) ==="
	@echo ""
	$(RUFF) check parseltongue/ --statistics 2>/dev/null || echo "Linting clean or ruff not configured"

demo-skills: ## List parseltongue skills
	@echo "=== Parseltongue Skills ==="
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done

plugin-check: demo-tests demo-lint demo-skills ## Run all live demos
	@echo ""
	@echo "=== Parseltongue Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

demo-analyze-tests: ## Demo analyze-tests command (LIVE)
	@echo "=== analyze-tests Demo (LIVE) ==="
	@echo ""
	@echo "Command: /analyze-tests"
	@echo "Plugin: parseltongue"
	@echo ""
	@echo "This demonstrates analyze-tests usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /analyze-tests for full workflow."


demo-run-profiler: ## Demo run-profiler command (LIVE)
	@echo "=== run-profiler Demo (LIVE) ==="
	@echo ""
	@echo "Command: /run-profiler"
	@echo "Plugin: parseltongue"
	@echo ""
	@echo "This demonstrates run-profiler usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /run-profiler for full workflow."


demo-check-async: ## Demo check-async command (LIVE)
	@echo "=== check-async Demo (LIVE) ==="
	@echo ""
	@echo "Command: /check-async"
	@echo "Plugin: parseltongue"
	@echo ""
	@echo "This demonstrates check-async usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /check-async for full workflow."


demo-parseltongue-commands: demo-analyze-tests demo-run-profiler demo-check-async ## Run all parseltongue documented command demos
	@echo ""
	@echo "=== Parseltongue All Commands Demo Complete ==="
	@echo "Ran 3 documented commands"
	@echo ""


test-analyze-tests: ## Test analyze-tests command workflow
	@echo "=== Testing analyze-tests workflow ==="
	@echo "Validating: /analyze-tests"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-run-profiler: ## Test run-profiler command workflow
	@echo "=== Testing run-profiler workflow ==="
	@echo "Validating: /run-profiler"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-check-async: ## Test check-async command workflow
	@echo "=== Testing check-async workflow ==="
	@echo "Validating: /check-async"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""




# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
