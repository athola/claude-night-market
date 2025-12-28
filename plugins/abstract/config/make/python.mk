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

TEST_UNIT_TARGETS ?= $(PYTEST_TARGETS)
TEST_UNIT_ARGS ?= $(PYTEST_FLAGS)
TEST_COVERAGE_TARGETS ?= $(PYTEST_TARGETS)
TEST_COVERAGE_ARGS ?= $(PYTEST_FLAGS)
TEST_QUICK_TARGETS ?= $(PYTEST_TARGETS)
TEST_QUICK_ARGS ?= --no-cov --tb=short

COV_DIRS ?= $(SRC_DIRS)
COV_REPORTS ?= --cov-report=term-missing --cov-report=html
TEST_FALLBACK_TARGETS ?= $(PYTEST_TARGETS)
TEST_FALLBACK_ARGS ?= -v --tb=short

COV_ARGS := $(foreach dir,$(COV_DIRS),--cov=$(dir))

format: ## Format code with ruff
	@echo "Formatting code..."
	@$(RUFF) format $(RUFF_TARGETS) || { echo "[WARN] Ruff format failed"; exit 1; }
	@$(RUFF) check --fix $(RUFF_TARGETS) || { echo "[WARN] Ruff check failed"; exit 1; }

lint: ## Run linting checks
	@echo "Running linting..."
	@$(RUFF) check $(RUFF_TARGETS) || { echo "[WARN] Linting failed"; exit 1; }

type-check: ## Run type checking
	@echo "Running type checking..."
	@$(MYPY) $(MYPY_TARGETS) || { echo "[WARN] Type checking failed"; exit 1; }
ifneq ($(strip $(TYPECHECK_EXTRA)),)
	@$(TYPECHECK_EXTRA)
endif

# Alias for backwards compatibility
typecheck: type-check

security: ## Run security checks
	@echo "Running security checks..."
	@$(BANDIT) -r $(BANDIT_TARGETS) || { echo "[WARN] Security check failed"; exit 1; }
ifneq ($(strip $(SECURITY_EXTRA)),)
	@$(SECURITY_EXTRA)
endif

# TESTING
test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@$(PYTEST) $(TEST_UNIT_TARGETS) $(TEST_UNIT_ARGS) || { echo "[WARN] Tests failed"; exit 1; }

# Alias for backwards compatibility
unit-tests: test-unit

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	@$(PYTEST) $(TEST_COVERAGE_TARGETS) $(TEST_COVERAGE_ARGS) $(COV_ARGS) $(COV_REPORTS) || { echo "[WARN] Coverage tests failed"; $(PYTEST) $(TEST_FALLBACK_TARGETS) $(TEST_FALLBACK_ARGS); }

test-quick: ## Run tests without coverage
	@echo "Running quick tests (no coverage)..."
	@$(PYTEST) $(TEST_QUICK_TARGETS) $(TEST_QUICK_ARGS) || { echo "[WARN] Tests failed"; exit 1; }
