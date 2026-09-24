SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# .SHELLFLAGS arrived in GNU make 3.82. Stock macOS ships 3.81 from the
# Xcode command line tools, which parses the assignment above and ignores
# it, so every recipe here runs without -euo pipefail. Say so once per
# invocation rather than pretend the gate holds.
ifneq ($(filter 3.7% 3.80 3.81,$(firstword $(MAKE_VERSION))),)
$(warning GNU make $(MAKE_VERSION) ignores .SHELLFLAGS; recipes run without -euo pipefail. Install GNU make 3.82+ (brew install make) and run gmake.)
endif

.PHONY: help install test test-unit lint typecheck format check docker-build docker-run clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## Install phantom with dev dependencies
	uv sync --extra dev

test: ## Run all tests
	uv run --extra dev python -m pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	uv run --extra dev python -m pytest tests/unit/ -v --tb=short

typecheck: ## Run type checking
	uv run --extra dev mypy src/ tests/

lint: ## Run linter
	uv run --extra dev ruff check src/ tests/

format: ## Format code
	uv run --extra dev ruff format src/ tests/

check: ## Check display environment
	uv run python -m phantom.cli --check

docker-build: ## Build sandboxed Docker image
	@command -v docker >/dev/null 2>&1 || \
		{ echo "docker is required for this target. Install Docker Desktop or your distribution's docker package."; exit 1; }
	docker build -f scripts/Dockerfile -t phantom:latest .

docker-run: ## Run interactive shell in sandbox
	@command -v docker >/dev/null 2>&1 || \
		{ echo "docker is required for this target. Install Docker Desktop or your distribution's docker package."; exit 1; }
	docker run -it --rm \
		-e ANTHROPIC_API_KEY \
		phantom:latest

clean: ## Remove build artifacts
	rm -rf .venv/ dist/ *.egg-info .pytest_cache .ruff_cache
