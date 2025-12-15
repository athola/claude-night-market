# config/make/python.mk - Python quality check targets
# Requires: common.mk (for RUFF, MYPY, BANDIT, PYTEST, SRC_DIRS variables)
#
# Standardized target names:
#   - type-check (not typecheck)
#   - test-unit (not unit-tests)
#   - security (not security-check)

format: ## Format code with ruff
	@echo "Formatting code..."
	@$(RUFF) format $(SRC_DIRS) || { echo "⚠ Ruff format failed"; exit 1; }
	@$(RUFF) check --fix $(SRC_DIRS) || { echo "⚠ Ruff check failed"; exit 1; }

lint: ## Run linting checks
	@echo "Running linting..."
	@$(RUFF) check $(SRC_DIRS) || { echo "⚠ Linting failed"; exit 1; }

type-check: ## Run type checking
	@echo "Running type checking..."
	@$(MYPY) $(SRC_DIRS) || { echo "⚠ Type checking failed"; exit 1; }

# Alias for backwards compatibility
typecheck: type-check

security: ## Run security checks
	@echo "Running security checks..."
	@$(BANDIT) -r $(SRC_DIRS) || { echo "⚠ Security check failed"; exit 1; }

# TESTING
test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@$(PYTEST) tests/ -v || { echo "⚠ Tests failed"; exit 1; }

# Alias for backwards compatibility
unit-tests: test-unit

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	@$(PYTEST) tests/ -v --cov=scripts --cov=src/abstract --cov-report=term-missing --cov-report=html || { echo "⚠ Coverage tests failed"; $(PYTEST) tests/ -v --tb=short; }

test-quick: ## Run tests without coverage
	@echo "Running quick tests (no coverage)..."
	@$(PYTEST) tests/ -v --no-cov --tb=short || { echo "⚠ Tests failed"; exit 1; }
