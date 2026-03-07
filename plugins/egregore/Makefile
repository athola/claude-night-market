# Egregore Plugin Makefile
# Autonomous agent orchestrator

.PHONY: check clean deps fix format help lint test type-check

ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

help: ## Show this help message
	@echo "Egregore Plugin - Make Targets"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile

deps: ## Install dependencies
	uv sync

lint: ## Run linting
	uv run ruff check scripts/ tests/

format: ## Format code
	uv run ruff format scripts/ tests/

fix: ## Auto-fix lint issues
	uv run ruff check --fix scripts/ tests/

type-check: ## Run type checking
	uv run mypy scripts/

test: ## Run tests
	uv run pytest tests/ -v --tb=short

check: lint type-check test ## Run all checks
	@echo "All checks passed!"

clean: ## Clean artifacts
	rm -rf .venv .uv-cache __pycache__ .mypy_cache .pytest_cache

Makefile.local:;
-include Makefile.local

%::
	@echo "Error: Unknown target '$$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
