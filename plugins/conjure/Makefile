# Conjure Plugin Makefile
# Delegation services for external LLM providers
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps check fix format lint type-check typecheck spellcheck security test status clean \
        install-hooks validate-all quota-status usage-report validate-delegation delegate-status \
        delegate-verify delegate-usage delegate-test delegate-gemini delegate-qwen delegate-auto \
        demo-token-estimate precommit

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Override source directories for this plugin
SRC_DIRS := scripts hooks

# Default target
help:
	@echo "Conjure Plugin - Make Targets"
	@echo "=============================="
	@echo ""
	@echo "Development:"
	@echo "  deps              Install and sync dependencies"
	@echo "  check             Run dependency validation"
	@echo "  fix               Auto-fix code style issues"
	@echo "  format            Format Python code"
	@echo "  lint              Run linting checks"
	@echo "  type-check        Run type checking"
	@echo "  security          Run security checks"
	@echo "  test              Run all quality checks"
	@echo "  precommit         Run pre-commit against all files"
	@echo "  status            Show project overview"
	@echo "  clean             Clean cache and build files"
	@echo "  install-hooks     Install pre-commit hooks"
	@echo ""
	@echo "Delegation commands:"
	@echo "  quota-status      Check delegation quota status"
	@echo "  usage-report      Generate usage report"
	@echo "  validate-delegation  Validate delegation configuration"
	@echo "  delegate-status   Check delegation service availability"
	@echo "  delegate-verify   Verify authentication for all services"
	@echo "  delegate-usage    Show usage analytics across services"
	@echo "  delegate-test     Test all delegation services"
	@echo ""
	@echo "Usage examples:"
	@echo "  make delegate-gemini PROMPT='Analyze code' FILES='src/main.py'"
	@echo "  make delegate-qwen PROMPT='Extract patterns' FILES='src/**/*.py'"
	@echo "  make delegate-auto PROMPT='Best analysis' FILES='src/'"

# Dependency management
deps:
	UV_CACHE_DIR=$(PWD)/.uv-cache uv sync
	UV_CACHE_DIR=$(PWD)/.uv-cache uv run python -c "import tiktoken; print('tiktoken available')"

demo-token-estimate:
	@echo "Demonstrating token estimation with tiktoken"
	UV_CACHE_DIR=$(PWD)/.uv-cache uv run python -c "from tools.delegation_executor import Delegator; files=[]; prompt='Summarize the delegation executor and quota tracker.'; print(f'Estimated tokens: {Delegator().estimate_tokens(files, prompt)}')"

check:
	@echo "Running dependency validation..."
	uv run python scripts/quota_tracker.py --status || true
	uv run python scripts/usage_logger.py --validate || true

fix:
	@echo "Auto-fixing code style issues..."
	uv run ruff format $(SRC_DIRS)
	uv run ruff check --fix $(SRC_DIRS)

# Code quality
format:
	@echo "Formatting Python code..."
	uv run ruff format $(SRC_DIRS)
	uv run ruff check --fix $(SRC_DIRS)

lint:
	@echo "Running linting checks..."
	uv run ruff check $(SRC_DIRS)

type-check:
	@echo "Running type checking..."
	uv run mypy scripts/
	uv run ty check scripts/ || true

# Alias for backwards compatibility
typecheck: type-check

spellcheck:
	@echo "Running spell check..."
	uv run typos $(SRC_DIRS)

security:
	@echo "Running security checks..."
	uv run bandit -r $(SRC_DIRS) || { echo "⚠ Security check failed"; exit 1; }

test: check lint type-check security
	@echo "All checks passed!"

precommit:
	@echo "Running pre-commit hooks..."
	uv run pre-commit run --all-files

# Git and hooks
install-hooks:
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

validate-all:
	@echo "Running full validation..."
	uv run python scripts/quota_tracker.py --status
	uv run python scripts/usage_logger.py --validate
	uv run pre-commit run --all-files || true

# Maintenance
clean:
	@echo "Cleaning up..."
	rm -rf .venv 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	uv cache clean 2>/dev/null || true

# Quick commands
status: ## Show project overview
	@echo "Conjure Plugin Status:"
	@echo "Skills:  $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Scripts: $$(find scripts/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Hooks:   $$(find hooks/ -name '*.py' 2>/dev/null | wc -l)"

# Delegation specific commands
quota-status:
	@echo "Checking delegation quota status..."
	uv run python scripts/quota_tracker.py --status

usage-report:
	@echo "Generating usage report..."
	uv run python scripts/usage_logger.py --report

validate-delegation:
	@echo "Validating delegation configuration..."
	uv run python scripts/quota_tracker.py --validate-config

# Delegation executor commands
delegate-status:
	@echo "Checking delegation service status..."
	uv run python scripts/delegation_executor.py --list-services

delegate-verify:
	@echo "Verifying delegation services..."
	uv run python scripts/delegation_executor.py gemini --verify || true
	uv run python scripts/delegation_executor.py qwen --verify || true

delegate-usage:
	@echo "Showing delegation usage analytics..."
	uv run python scripts/delegation_executor.py --usage

delegate-gemini:
	@echo "Delegating to Gemini..."
	uv run python scripts/delegation_executor.py gemini "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-qwen:
	@echo "Delegating to Qwen..."
	uv run python scripts/delegation_executor.py qwen "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-auto:
	@echo "Auto-selecting best delegation service..."
	uv run python scripts/delegation_executor.py auto "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-test:
	@echo "Testing delegation services..."
	@echo "Testing Gemini..."
	uv run python scripts/delegation_executor.py gemini "Respond with 'OK'" || echo "Gemini not available"
	@echo "Testing Qwen..."
	uv run python scripts/delegation_executor.py qwen "Respond with 'OK'" || echo "Qwen not available"
	@echo "Showing usage..."
	uv run python scripts/delegation_executor.py --usage
