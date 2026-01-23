# Conjure Plugin Makefile
# Delegation services for external LLM providers
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps check fix format lint type-check typecheck spellcheck security test status clean \
        install-hooks validate-all quota-status usage-report validate-delegation delegate-status \
        delegate-verify delegate-usage delegate-test delegate-gemini delegate-qwen delegate-auto \
        demo-token-estimate precommit mutation-test benchmark memory-profile demo-delegation demo-skills plugin-check debug-variables

# Override source directories for this plugin
SRC_DIRS := scripts hooks
MYPY_TARGETS := scripts/
BANDIT_TARGETS := $(SRC_DIRS)
TYPECHECK_EXTRA = $(UV_RUN) ty check scripts/ || true

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Default target
help: ## Show this help message
	@echo "Conjure Plugin - Make Targets"
	@echo "=============================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Usage examples:"
	@echo "  make delegate-gemini PROMPT='Analyze code' FILES='src/main.py'"
	@echo "  make delegate-qwen PROMPT='Extract patterns' FILES='src/**/*.py'"
	@echo "  make delegate-auto PROMPT='Best analysis' FILES='src/'"

# Dependency management
deps: ## Install and sync dependencies
	UV_CACHE_DIR=$(PWD)/.uv-cache uv sync
	UV_CACHE_DIR=$(PWD)/.uv-cache uv run python -c "import tiktoken; print('tiktoken available')"

demo-token-estimate: ## Demo token estimation with tiktoken
	@echo "Demonstrating token estimation with tiktoken"
	UV_CACHE_DIR=$(PWD)/.uv-cache uv run python -c "from tools.delegation_executor import Delegator; files=[]; prompt='Summarize the delegation executor and quota tracker.'; print(f'Estimated tokens: {Delegator().estimate_tokens(files, prompt)}')"

check: ## Run dependency validation
	@echo "Running dependency validation..."
	uv run python scripts/quota_tracker.py --status || true
	uv run python scripts/usage_logger.py --validate || true

fix: ## Auto-fix code style issues
	@echo "Auto-fixing code style issues..."
	$(RUFF) format $(SRC_DIRS)
	$(RUFF) check --fix $(SRC_DIRS)

# Code quality
spellcheck: ## Run spell check
	@echo "Running spell check..."
	$(UV_RUN) typos $(SRC_DIRS)

test: check lint type-check security ## Run all quality checks
	@echo "All checks passed!"

precommit: ## Run pre-commit against all files
	@echo "Running pre-commit hooks..."
	uv run pre-commit run --all-files

# Git and hooks
install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

validate-all: ## Run full validation suite
	@echo "Running full validation..."
	uv run python scripts/quota_tracker.py --status
	uv run python scripts/usage_logger.py --validate
	uv run pre-commit run --all-files || true

# Maintenance
clean: ## Clean cache and build files
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

# Delegation specific commands
quota-status: ## Check delegation quota status
	@echo "Checking delegation quota status..."
	uv run python scripts/quota_tracker.py --status

usage-report: ## Generate usage report
	@echo "Generating usage report..."
	uv run python scripts/usage_logger.py --report

validate-delegation: ## Validate delegation configuration
	@echo "Validating delegation configuration..."
	uv run python scripts/quota_tracker.py --validate-config

# Delegation executor commands
delegate-status: ## Check delegation service availability
	@echo "Checking delegation service status..."
	uv run python scripts/delegation_executor.py --list-services

delegate-verify: ## Verify authentication for all services
	@echo "Verifying delegation services..."
	uv run python scripts/delegation_executor.py gemini --verify || true
	uv run python scripts/delegation_executor.py qwen --verify || true

delegate-usage: ## Show usage analytics across services
	@echo "Showing delegation usage analytics..."
	uv run python scripts/delegation_executor.py --usage

delegate-gemini: ## Delegate to Gemini
	@echo "Delegating to Gemini..."
	uv run python scripts/delegation_executor.py gemini "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-qwen: ## Delegate to Qwen
	@echo "Delegating to Qwen..."
	uv run python scripts/delegation_executor.py qwen "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-auto: ## Auto-select best delegation service
	@echo "Auto-selecting best delegation service..."
	uv run python scripts/delegation_executor.py auto "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-test: ## Test all delegation services
	@echo "Testing delegation services..."
	@echo "Testing Gemini..."
	uv run python scripts/delegation_executor.py gemini "Respond with 'OK'" || echo "Gemini not available"
	@echo "Testing Qwen..."
	uv run python scripts/delegation_executor.py qwen "Respond with 'OK'" || echo "Qwen not available"
	@echo "Showing usage..."
	uv run python scripts/delegation_executor.py --usage

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate scripts --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks (API delegation latency)
	$(PYTEST) --benchmark-only --benchmark-sort=mean || echo "pytest-benchmark not installed"

memory-profile: ## Profile memory usage
	@echo "Memory profiling not yet configured for conjure"
	@echo "Install memory_profiler: pip install memory_profiler"

# ---------- Demo/Dogfood Targets ----------
demo-delegation: ## Demo delegation workflow
	@echo "=== Conjure Delegation Demo ==="
	@echo "Demonstrating delegation-core skill workflow..."
	@echo ""
	@echo "Step 1: Service availability"
	@uv run python scripts/delegation_executor.py --list-services 2>/dev/null || echo "  (services not configured)"
	@echo ""
	@echo "Step 2: Quota status"
	@uv run python scripts/quota_tracker.py --status 2>/dev/null || echo "  (quota tracking inactive)"
	@echo ""
	@echo "Step 3: Token estimation sample"
	@uv run python -c "from tools.delegation_executor import Delegator; d=Delegator(); print(f'Estimated tokens for test prompt: {d.estimate_tokens([], \"Hello world\")}')" 2>/dev/null || echo "  (token estimator not available)"
	@echo ""
	@echo "Delegation demo complete. Use conjure:delegation-core for full workflow."

demo-skills: ## Validate conjure skill structure
	@echo "=== Conjure Skills Demo ==="
	@echo "Delegation skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  delegation-core:    $$(test -f skills/delegation-core/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  gemini-delegation:  $$(test -f skills/gemini-delegation/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  qwen-delegation:    $$(test -f skills/qwen-delegation/SKILL.md && echo '[OK]' || echo '[X]')"

plugin-check: demo-delegation demo-skills status ## Run all demo workflows
	@echo ""
	@echo "=== Conjure Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
