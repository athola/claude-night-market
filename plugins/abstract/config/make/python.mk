# config/make/python.mk - Python quality check targets
# Requires: common.mk (for RUFF, MYPY, BANDIT, PYTEST, SRC_DIRS variables)
#
# Standardized target names:
#   - type-check (not typecheck)
#   - test-unit (not unit-tests)
#   - security (not security-check)

# Target configuration (override in plugin Makefile as needed)
TEST_DIR ?= tests
PYTEST_TARGETS ?= $(TEST_DIR)/
PYTEST_FLAGS ?= -v

RUFF_TARGETS ?= $(SRC_DIRS)
MYPY_TARGETS ?= $(SRC_DIRS)
BANDIT_TARGETS ?= $(SRC_DIRS)
# A plugin without its own [tool.bandit] table uses the repository's,
# whose skips each carry a reason. Before this, bandit ran with no skips
# there and failed on the subprocess use every plugin shares.
_PYTHON_MK_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
BANDIT_CONFIG ?= $(if $(shell grep -l '^\[tool\.bandit\]' pyproject.toml 2>/dev/null),pyproject.toml,$(_PYTHON_MK_DIR)../../../../pyproject.toml)

TEST_UNIT_TARGETS ?= $(PYTEST_TARGETS)
TEST_UNIT_ARGS ?= $(PYTEST_FLAGS)
TEST_COVERAGE_TARGETS ?= $(PYTEST_TARGETS)
TEST_COVERAGE_ARGS ?= $(PYTEST_FLAGS)
TEST_QUICK_TARGETS ?= $(PYTEST_TARGETS)
TEST_QUICK_ARGS ?= --no-cov --tb=short

COV_DIRS ?= $(SRC_DIRS)
COV_REPORTS ?= --cov-report=term-missing --cov-report=html

COV_ARGS := $(foreach dir,$(COV_DIRS),--cov=$(dir))

.PHONY: format lint type-check typecheck security test-unit unit-tests test-coverage test-quick

format: ## Format code with ruff
	@echo "Formatting code..."
	@$(RUFF) format $(RUFF_TARGETS) || { echo "[FAIL] Ruff format failed"; exit 1; }
	@$(RUFF) check --fix $(RUFF_TARGETS) || { echo "[FAIL] Ruff check failed"; exit 1; }

lint: ## Run linting checks
	@echo "Running linting..."
	@$(RUFF) check $(RUFF_TARGETS) || { echo "[FAIL] Linting failed"; exit 1; }

type-check: ## Run type checking
	@echo "Running type checking..."
	@$(MYPY) $(MYPY_TARGETS) || { echo "[FAIL] Type checking failed"; exit 1; }
ifneq ($(strip $(TYPECHECK_EXTRA)),)
	@$(TYPECHECK_EXTRA)
endif

# Alias for backwards compatibility
typecheck: type-check

security: ## Run security checks
	@echo "Running security checks..."
	@$(BANDIT) -c $(BANDIT_CONFIG) -r $(BANDIT_TARGETS) || { echo "[FAIL] Security check failed"; exit 1; }
ifneq ($(strip $(SECURITY_EXTRA)),)
	@$(SECURITY_EXTRA)
endif

# TESTING
test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@$(PYTEST) $(TEST_UNIT_TARGETS) $(TEST_UNIT_ARGS) || { echo "[FAIL] Tests failed"; exit 1; }
ifneq ($(strip $(TEST_UNIT_EXTRA)),)
	@$(TEST_UNIT_EXTRA)
endif

# Alias for backwards compatibility
unit-tests: test-unit

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	@$(PYTEST) $(TEST_COVERAGE_TARGETS) $(TEST_COVERAGE_ARGS) $(COV_ARGS) $(COV_REPORTS)

test-quick: ## Run tests without coverage
	@echo "Running quick tests (no coverage)..."
	@$(PYTEST) $(TEST_QUICK_TARGETS) $(TEST_QUICK_ARGS) || { echo "[FAIL] Tests failed"; exit 1; }
