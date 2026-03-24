.PHONY: help install test lint format check docker-build docker-run clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## Install phantom with dev dependencies
	uv pip install --extra dev -e .

test: ## Run all tests
	uv run --extra dev python -m pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	uv run --extra dev python -m pytest tests/unit/ -v --tb=short

lint: ## Run linter
	uv run --extra dev ruff check src/ tests/

format: ## Format code
	uv run --extra dev ruff format src/ tests/

check: ## Check display environment
	uv run python -m phantom.cli --check

docker-build: ## Build sandboxed Docker image
	docker build -f scripts/Dockerfile -t phantom:latest .

docker-run: ## Run interactive shell in sandbox
	docker run -it --rm \
		-e ANTHROPIC_API_KEY \
		phantom:latest

clean: ## Remove build artifacts
	rm -rf .venv/ dist/ *.egg-info .pytest_cache .ruff_cache
