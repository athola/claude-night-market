# Conjure Plugin Makefile
# Delegation services for external LLM providers
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: benchmark check clean debug-variables delegate-auto delegate-codex delegate-doctor \
	delegate-gemini delegate-glimmer delegate-glm delegate-install delegate-minimax delegate-muse \
	delegate-opencode delegate-qwen delegate-setup \
	delegate-status delegate-test delegate-usage delegate-verify demo-delegation demo-plugin \
	demo-skills demo-status demo-token-estimate deps fix help install-hooks memory-profile \
	mutation-test plugin-check precommit quota-status spellcheck status test test-plugin \
	test-status test-suite usage-report validate-all validate-delegation demo-conjure-commands

# Override source directories for this plugin
SRC_DIRS := scripts hooks
MYPY_TARGETS := scripts/
BANDIT_TARGETS := $(SRC_DIRS)
TYPECHECK_EXTRA = $(UV_RUN) ty check scripts/

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
	@echo "  make delegate-minimax PROMPT='Summarize' FILES='src/**/*.py'"
	@echo "  make delegate-glm PROMPT='Review this design'"
	@echo "  make delegate-muse PROMPT='Run the tests and summarize failures'"
	@echo "  make delegate-codex PROMPT='Explain this module'"
	@echo "  make delegate-opencode PROMPT='Find the bug'"
	@echo "  make delegate-glimmer PROMPT='Summarize' FILES='src/'   # local, no quota"
	@echo "  make delegate-setup      # which providers are installed?"
	@echo "  make delegate-doctor     # what is broken and how to fix it"
	@echo "  make delegate-install    # install what is missing, with confirmation"
	@echo "  make delegate-auto PROMPT='Best analysis' FILES='src/'"

# Dependency management
deps: ## Install and sync dependencies
	UV_CACHE_DIR=$(PWD)/.uv-cache uv sync
	UV_CACHE_DIR=$(PWD)/.uv-cache uv run python -c "import tiktoken; print('tiktoken available')"

demo-token-estimate: ## Demo token estimation with tiktoken
	@echo "Demonstrating token estimation with tiktoken"
	UV_CACHE_DIR=$(PWD)/.uv-cache uv run python -c "from scripts.delegation_executor import estimate_tokens; files=['scripts/delegation_executor.py', 'scripts/quota_tracker.py']; prompt='Summarize the delegation executor and quota tracker.'; print(f'Estimated tokens: {estimate_tokens(files, prompt)}')"

check: ## Run dependency validation
	@echo "Running dependency validation..."
	uv run python scripts/quota_tracker.py --status
	uv run python scripts/usage_logger.py --validate

fix: ## Auto-fix code style issues
	@echo "Auto-fixing code style issues..."
	$(RUFF) format $(SRC_DIRS)
	$(RUFF) check --fix $(SRC_DIRS)

# Code quality
spellcheck: ## Run spell check
	@echo "Running spell check..."
	$(UV_RUN) typos $(SRC_DIRS)

test: check lint type-check security test-suite ## Run all quality checks
	@echo "All checks passed!"

test-suite: ## Run the pytest suite
	@# This target is why `test` exists. Without it `make test` ran style
	@# and typing only, so the pre-commit "Test Changed Plugins" hook
	@# reported passing tests for this plugin while the suite was red. A
	@# gate that cannot fail is not a gate.
	@echo "Running test suite..."
	$(PYTEST) tests/

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
	uv run pre-commit run --all-files

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

delegate-setup: ## Show which provider CLIs are installed and authenticated
	@uv run python scripts/delegation_setup.py --status

delegate-doctor: ## Explain each unhealthy provider and the command that fixes it
	@uv run python scripts/delegation_setup.py --doctor

delegate-install: ## Offer to install every missing provider CLI, one confirmation each
	@uv run python scripts/delegation_setup.py --all

delegate-verify: ## Verify authentication for all registered services
	@echo "Verifying delegation services..."
	@# The service list comes from the registry rather than being spelled
	@# out here, so a newly registered provider is verified without editing
	@# this target. Every service is verified before the target fails, so
	@# one broken service does not hide the state of the others.
	@fail=0; \
	for svc in $$(uv run python scripts/delegation_executor.py --list-services | awk -F: '{print $$1}'); do \
		uv run python scripts/delegation_executor.py $$svc --verify || fail=1; \
	done; \
	exit $$fail

delegate-usage: ## Show usage analytics across services
	@echo "Showing delegation usage analytics..."
	uv run python scripts/delegation_executor.py --usage

delegate-gemini: ## Delegate to Gemini
	@echo "Delegating to Gemini..."
	uv run python scripts/delegation_executor.py gemini "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-qwen: ## Delegate to Qwen
	@echo "Delegating to Qwen..."
	uv run python scripts/delegation_executor.py qwen "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-minimax: ## Delegate to MiniMax
	@echo "Delegating to MiniMax..."
	uv run python scripts/delegation_executor.py minimax "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-glm: ## Delegate to GLM-5.3 via Z.ai
	@echo "Delegating to GLM..."
	uv run python scripts/delegation_executor.py glm "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-muse: ## Delegate to Meta Muse Code
	@echo "Delegating to Muse..."
	uv run python scripts/delegation_executor.py muse "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-codex: ## Delegate to OpenAI Codex CLI
	@echo "Delegating to Codex..."
	uv run python scripts/delegation_executor.py codex "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-opencode: ## Delegate to OpenCode
	@echo "Delegating to OpenCode..."
	uv run python scripts/delegation_executor.py opencode "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-glimmer: ## Delegate to Muse Glimmer running locally via ollama
	@echo "Delegating to Muse Glimmer (local)..."
	uv run python scripts/delegation_executor.py glimmer "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-auto: ## Auto-select best delegation service
	@echo "Auto-selecting best delegation service..."
	uv run python scripts/delegation_executor.py auto "$(PROMPT)" $(if $(FILES),--files $(FILES))

delegate-test: ## Test all delegation services
	@echo "Testing delegation services..."
	@# Iterates the registry so a newly registered provider is exercised
	@# here without editing this target.
	@for svc in $$(uv run python scripts/delegation_executor.py --list-services | awk -F: '{print $$1}'); do \
		echo "Testing $$svc..."; \
		uv run python scripts/delegation_executor.py $$svc "Respond with 'OK'" \
			|| echo "$$svc not available"; \
	done
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
	@# pytest-benchmark is an optional dev extra. Detect it explicitly so a
	@# real benchmark failure fails the target instead of being reported as a
	@# missing plugin. pytest exit 5 means nothing was collected, not failure.
	@if ! $(UV_RUN) python -c "import pytest_benchmark" 2>/dev/null; then \
		echo "Not applicable: pytest-benchmark is not installed"; \
	else \
		$(PYTEST) --benchmark-only --benchmark-sort=mean; \
		status=$$?; \
		if [ $$status -eq 5 ]; then \
			echo "Not applicable: no benchmark tests are defined"; \
		elif [ $$status -ne 0 ]; then \
			exit $$status; \
		fi; \
	fi

memory-profile: ## Profile memory usage
	@if python3 -c "import memory_profiler" 2>/dev/null; then \
		$(UV_RUN) python3 -m memory_profiler scripts/*.py; \
	else \
		echo "Install memory_profiler: pip install memory_profiler"; \
	fi

# ---------- Demo/Dogfood Targets ----------
demo-delegation: ## Demo delegation workflow
	@echo "=== Conjure Delegation Demo ==="
	@echo "Demonstrating delegation-core skill workflow..."
	@echo ""
	@echo "Step 1: Service availability"
	@uv run python scripts/delegation_executor.py --list-services
	@echo ""
	@echo "Step 2: Quota status"
	@uv run python scripts/quota_tracker.py --status
	@echo ""
	@echo "Step 3: Token estimation sample"
	@uv run python -c "from scripts.delegation_executor import estimate_tokens; print(f'Estimated tokens for test prompt: {estimate_tokens([], \"Hello world\")}')"
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
	@echo "Skill coverage (registration vs disk):"
	@uv run python scripts/check_skill_coverage.py

plugin-check: demo-delegation demo-skills status ## Run all demo workflows
	@echo ""
	@echo "=== Conjure Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

demo-plugin: ## Print how to install the plugin (informational, runs nothing)
	@echo "=== plugin (informational) ==="
	@echo ""
	@echo "Command: /plugin install athola@claude-night-market"
	@echo "Plugin: conjure"
	@echo ""
	@echo "This demonstrates plugin usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /plugin install athola@claude-night-market for full workflow."

demo-status: ## Print how to reach /status (informational, runs nothing)
	@echo "=== status (informational) ==="
	@echo ""
	@echo "Command: /status"
	@echo "Plugin: conjure"
	@echo ""
	@echo "This demonstrates status usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /status for full workflow."


demo-conjure-commands: demo-plugin demo-status delegate-setup ## Run all conjure documented command demos
	@echo ""
	@echo "=== Conjure All Commands Demo Complete ==="
	@echo ""

test-plugin: ## Test plugin install and delegation commands
	@echo "Running delegation and skills tests..."
	$(PYTEST) tests/ -v -k "delegation or skills" || $(PYTEST) tests/ -v --tb=short

test-status: ## Test delegation status command
	@echo "Running quota and status tests..."
	uv run python scripts/quota_tracker.py --status
	@# pytest exits 5 when the -k filter matches nothing, which is not a
	@# failure. Every other nonzero exit is a real test failure and must fail
	@# the target. The previous fallback arm ran a command literally named
	@# '@echo' ('@' is only a Make prefix at the start of a recipe line, not
	@# after a line continuation), so it always died with 127 instead.
	@$(PYTEST) tests/ -v -k "quota or status"; \
	status=$$?; \
	if [ $$status -eq 5 ]; then \
		echo "Not applicable: no quota or status tests are defined"; \
	elif [ $$status -ne 0 ]; then \
		exit $$status; \
	fi


# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
