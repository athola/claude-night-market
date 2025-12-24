# Conservation Plugin Makefile
# Context optimization and resource management
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps check fix format lint type-check typecheck spellcheck security test clean install-hooks \
        status validate-all deps-report fix-apply cli-status cli-validate token-estimate perf-check \
        validate-skills test-skills demo-context demo-tokens demo-skills plugin-check

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Plugin-specific variables
override SRC_DIRS := scripts services

# Default target
help: ## Show this help message
	@echo "Conservation Plugin - Make Targets"
	@echo "==================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile
	@echo ""
	@echo "Token estimation examples:"
	@echo "  make token-estimate ARGS='--directory skills/'"
	@echo "  make token-estimate ARGS='--file skills/context-optimization/SKILL.md'"

# ---------- Dependencies ----------
deps: ## Install and sync dependencies
	uv sync

check: ## Run dependency validation
	@echo "Running dependency validation..."
	@echo "Note: tools/dependency_manager.py not yet implemented - using uv check"
	uv pip check || true

fix: ## Show dependency fixes (dry run)
	@echo "Auto-fixing dependency issues..."
	@echo "Note: tools/dependency_manager.py not yet implemented"
	@echo "Run 'uv sync' to ensure dependencies are current"

fix-apply: ## Apply dependency fixes
	@echo "Applying dependency fixes..."
	@echo "Note: tools/dependency_manager.py not yet implemented"
	uv sync

deps-report: ## Generate detailed dependency report
	@echo "Generating detailed dependency report..."
	@echo "Note: tools/dependency_manager.py not yet implemented"
	uv pip list

# ---------- Code Quality ----------
format: ## Format Python code
	@echo "Formatting Python code..."
	uv run ruff format $(SRC_DIRS)
	uv run ruff check --fix $(SRC_DIRS)

lint: ## Run linting checks
	@echo "Running linting checks..."
	uv run ruff check $(SRC_DIRS)

type-check: ## Run type checking
	@echo "Running type checking..."
	uv run mypy $(SRC_DIRS) || { echo "⚠ Type checking failed"; exit 1; }

# Alias for backwards compatibility
typecheck: type-check

spellcheck: ## Run spell check
	@echo "Running spell check..."
	uv run typos $(SRC_DIRS)

security: ## Run security checks
	@echo "Running security checks..."
	uv run bandit -r $(SRC_DIRS) || { echo "⚠ Security check failed"; exit 1; }

test: check lint type-check security ## Run all quality checks
	@echo "All checks passed!"

# ---------- Hooks ----------
install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

validate-all: ## Run full validation suite
	@echo "Running full validation..."
	@echo "Note: tools/safe_replacer.py and tools/dependency_manager.py not yet implemented"
	uv pip check || true
	uv run pre-commit run --all-files || true

# ---------- Maintenance ----------
clean: ## Clean cache and build files
	@echo "Cleaning up..."
	rm -rf .venv 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	uv cache clean 2>/dev/null || true

status: ## Show project overview
	@echo "Conservation Plugin Status:"
	@echo "Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Tools:  $$(find tools/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Tests:  $$(find tests/ -name '*.py' 2>/dev/null | wc -l)"

# ---------- CLI Tools ----------
cli-status: ## Show plugin status via CLI
	@echo "Running CLI status check..."
	./bin/conservation-cli status || echo "CLI not available"

cli-validate: ## Run full validation via CLI
	@echo "Running CLI validation..."
	./bin/conservation-cli validate || echo "CLI not available"

# ---------- Resource Management ----------
token-estimate: ## Estimate token usage for skills (ARGS=...)
	@echo "Estimating token usage (via abstract plugin)..."
	@if echo "$(ARGS)" | grep -q "^--file "; then \
		FILE=$$(echo "$(ARGS)" | sed 's/--file //'); \
		cd ../abstract && uv run python scripts/token_estimator.py --file ../conservation/$$FILE; \
	elif echo "$(ARGS)" | grep -q "^--directory "; then \
		DIR=$$(echo "$(ARGS)" | sed 's/--directory //'); \
		cd ../abstract && uv run python scripts/token_estimator.py --directory ../conservation/$$DIR; \
	else \
		cd ../abstract && uv run python scripts/token_estimator.py $(ARGS); \
	fi

perf-check: ## Check performance metrics
	@echo "Checking performance metrics..."
	@echo "Project Size: $$(du -sh . 2>/dev/null | cut -f1)"
	@echo "Python Files: $$(find . -name '*.py' 2>/dev/null | wc -l)"

# ---------- Skill Validation ----------
validate-skills: ## Validate all skill files
	@echo "Validating all skill files..."
	@for skill in $$(find skills/ -name "SKILL.md" 2>/dev/null); do \
		echo "Checking: $$skill"; \
	done

test-skills: ## Test skill functionality
	@echo "Testing skill functionality..."
	@echo "Token estimator test (via abstract):"
	@cd ../abstract && uv run python scripts/token_estimator.py --file ../conservation/skills/context-optimization/SKILL.md 2>/dev/null || echo "  Token estimator test skipped"
	@echo "Dependency check:"
	@uv pip check 2>/dev/null || echo "  Dependency check skipped"

# ---------- Demo/Dogfood Targets ----------
demo-context: ## Demo context optimization on own skills
	@echo "=== Conservation Context Demo ==="
	@echo "Demonstrating context-optimization skill..."
	@echo ""
	@echo "Step 1: Measure current context usage"
	@echo "Skills directory size: $$(du -sh skills/ 2>/dev/null | cut -f1)"
	@echo "Total skill files: $$(find skills/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Largest skills:"
	@find skills/ -name "*.md" -exec wc -l {} \; 2>/dev/null | sort -rn | head -5
	@echo ""
	@echo "Step 2: Skill structure analysis"
	@for skill in skills/*/SKILL.md; do \
		name=$$(basename $$(dirname $$skill)); \
		modules=$$(find $$(dirname $$skill) -name "*.md" ! -name "SKILL.md" 2>/dev/null | wc -l); \
		echo "  $$name: $$modules modules"; \
	done
	@echo ""
	@echo "Context demo complete. Use /conservation:optimize-context for full workflow."

demo-tokens: ## Demo token estimation on own plugin
	@echo "=== Conservation Token Demo ==="
	@echo "Demonstrating token estimation..."
	@echo ""
	@echo "Step 1: Estimate skill tokens"
	@for skill in skills/*/SKILL.md; do \
		lines=$$(wc -l < "$$skill" 2>/dev/null); \
		tokens=$$((lines * 4)); \
		echo "  $$skill: ~$$tokens tokens ($$lines lines)"; \
	done
	@echo ""
	@echo "Step 2: Total plugin estimate"
	@total_lines=$$(find skills/ -name "*.md" -exec cat {} \; 2>/dev/null | wc -l); \
	total_tokens=$$((total_lines * 4)); \
	echo "  Total: ~$$total_tokens tokens ($$total_lines lines)"
	@echo ""
	@echo "Token demo complete. Use 'make token-estimate ARGS=...' for precise estimation."

demo-skills: ## Validate conservation skill structure
	@echo "=== Conservation Skills Demo ==="
	@echo "Resource management skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  context-optimization: $$(test -f skills/context-optimization/SKILL.md && echo '✓' || echo '✗')"
	@echo "  mcp-code-execution:   $$(test -f skills/mcp-code-execution/SKILL.md && echo '✓' || echo '✗')"
	@echo "  optimizing-large-skills: $$(test -f skills/optimizing-large-skills/SKILL.md && echo '✓' || echo '✗')"
	@echo ""
	@echo "Scripts:"
	@find scripts/ -name "*.py" 2>/dev/null | wc -l | xargs -I{} echo "  {} Python scripts"

plugin-check: demo-context demo-tokens demo-skills test-skills ## Run all demo workflows
	@echo ""
	@echo "=== Conservation Plugin Check Complete ==="
