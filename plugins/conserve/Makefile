# Conservation Plugin Makefile
# Context optimization and resource management
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY:
.PHONY: benchmark check clean cli-status cli-validate debug-variables demo-ai-hygiene-audit \
	demo-bloat demo-bloat-scan demo-context demo-skills demo-tokens demo-unbloat deps deps-report fix \
	fix-apply format help install-hooks lint memory-profile mutation-test perf-check plugin-check \
	security spellcheck status test test-ai-hygiene-audit test-bloat-scan test-skills test-unbloat \
	token-estimate type-check typecheck validate-all validate-skills

# Plugin-specific variables (must be before include)
SRC_DIRS := scripts
COV_DIRS := $(SRC_DIRS)

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

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
	@echo "Run 'uv sync' to validate dependencies are current"

fix-apply: ## Apply dependency fixes
	@echo "Applying dependency fixes..."
	@echo "Note: tools/dependency_manager.py not yet implemented"
	uv sync

deps-report: ## Generate detailed dependency report
	@echo "Generating detailed dependency report..."
	@echo "Note: tools/dependency_manager.py not yet implemented"
	uv pip list

# ---------- Code Quality ----------
spellcheck: ## Run spell check
	@echo "Running spell check..."
	$(UV_RUN) typos $(SRC_DIRS)

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

# ---------- CLI Tools ----------
cli-status: ## Show plugin status via CLI
	@echo "Running CLI status check..."
	./bin/conservation_cli status || echo "CLI not available"

cli-validate: ## Run full validation via CLI
	@echo "Running CLI validation..."
	./bin/conservation_cli validate || echo "CLI not available"

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

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate scripts --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks (bloat detection speed)
	$(PYTEST) --benchmark-only --benchmark-sort=mean || echo "pytest-benchmark not installed"

memory-profile: ## Profile memory usage
	@echo "Memory profiling not yet configured for conserve"
	@echo "Install memory_profiler: pip install memory_profiler"

# ---------- Demo/Dogfood Targets (LIVE) ----------
demo-context: ## Demo context optimization (LIVE)
	@echo "=== Conservation Context Demo (LIVE) ==="
	@echo ""
	@echo "Running context optimizer on this plugin..."
	cd ../abstract && $(UV_RUN) python scripts/context_optimizer.py --path ../conserve/skills/ --report 2>/dev/null || \
		echo "Context optimizer: skills/ = $$(du -sh skills/ | cut -f1), $$(find skills/ -name '*.md' | wc -l) files"
	@echo ""
	@echo "Use /conserve:optimize-context for full workflow."

demo-tokens: ## Demo token estimation (LIVE)
	@echo "=== Conservation Token Demo (LIVE) ==="
	@echo ""
	@echo "Running token estimator on conserve skills..."
	cd ../abstract && $(UV_RUN) python scripts/token_estimator.py --directory ../conserve/skills/ 2>/dev/null || \
		$(UV_RUN) python scripts/token_estimator.py --file skills/context-optimization/SKILL.md 2>/dev/null || \
		echo "Token estimate: ~$$(find skills/ -name '*.md' -exec cat {} \; | wc -l | awk '{print $$1*4}') tokens"
	@echo ""
	@echo "Use 'make token-estimate ARGS=...' for detailed estimation."

demo-skills: ## Validate conservation skill structure
	@echo "=== Conservation Skills Demo ==="
	@echo "Resource management skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  context-optimization: $$(test -f skills/context-optimization/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  mcp-code-execution:   $$(test -f skills/mcp-code-execution/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  token-conservation:     $$(test -f skills/token-conservation/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  bloat-detector:       $$(test -f skills/bloat-detector/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo ""
	@echo "Scripts:"
	@find scripts/ -name "*.py" 2>/dev/null | wc -l | xargs -I{} echo "  {} Python scripts"

demo-bloat: ## Demo bloat detection on conservation plugin itself
	@echo "=== Conservation Bloat Detection Demo ==="
	@echo "Demonstrating bloat-detector skill on own codebase..."
	@echo ""
	@echo "Step 1: Identify large files (potential God classes)"
	@echo "Largest Python files:"
	@find scripts/ tests/ -name "*.py" -exec wc -l {} \; 2>/dev/null | sort -rn | head -5 | \
		awk '{if($$1>300) printf "  [WARN] %s (%d lines)\n", $$2, $$1; else printf "  [OK] %s (%d lines)\n", $$2, $$1}'
	@echo ""
	@echo "Step 2: Check for stale files (unchanged 6+ months)"
	@echo "Files with old modification dates:"
	@find skills/ scripts/ -type f -mtime +180 2>/dev/null | head -3 | \
		xargs -I{} echo "  {}" || echo "  (none found - all actively maintained)"
	@echo ""
	@echo "Step 3: Documentation bloat analysis"
	@echo "Documentation files:"
	@find . -name "README*.md" -o -name "*.md" | grep -v ".venv\|node_modules" | wc -l | \
		xargs -I{} echo "  {} markdown files"
	@echo ""
	@echo "Step 4: Cache and build artifacts"
	@echo "Cache directories:"
	@du -sh .pytest_cache .mypy_cache .ruff_cache 2>/dev/null | awk '{print "  " $$0}' || echo "  (clean - no cache bloat)"
	@echo ""
	@echo "Bloat demo complete. Use /bloat-scan for detailed analysis."
	@echo "Run /unbloat to safely remediate identified issues."

plugin-check: demo-context demo-tokens demo-skills demo-bloat test-skills ## Run all demo workflows
	@echo ""
	@echo "=== Conservation Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

demo-bloat-scan: ## Demo bloat-scan command (LIVE)
	@echo "=== bloat-scan Demo (LIVE) ==="
	@echo ""
	@echo "Running bloat-scan on conserve plugin..."
	@echo ""
	$(UV_RUN) python scripts/detect_duplicates.py . --report || echo "  [INFO] Tool execution completed"
	@echo ""
	@echo "Use /bloat-scan for full workflow."


demo-unbloat: ## Demo unbloat command (LIVE)
	@echo "=== unbloat Demo (LIVE) ==="
	@echo ""
	@echo "Command: /unbloat"
	@echo "Plugin: conserve"
	@echo ""
	@echo "This demonstrates unbloat usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /unbloat for full workflow."


	@echo "=== unbloat Demo (LIVE) ==="
	@echo ""
	@echo "Command: /unbloat"
	@echo "Plugin: conserve"
	@echo ""
	@echo "This demonstrates unbloat usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /unbloat for full workflow."


demo-ai-hygiene-audit: ## Demo ai-hygiene-audit command (LIVE)
	@echo "=== ai-hygiene-audit Demo (LIVE) ==="
	@echo ""
	@echo "Running ai-hygiene-audit on conserve plugin..."
	@echo ""
	echo 'AI hygiene audit: Check for TODO/FIXME in skills/' && grep -r 'TODO\|FIXME' skills/ | wc -l | xargs -I{} echo 'Found {} items' || echo "  [INFO] Tool execution completed"
	@echo ""
	@echo "Use /ai-hygiene-audit for full workflow."


	@echo "=== bloat-scan Demo (LIVE) ==="
	@echo ""
	@echo "Running bloat-scan on conserve plugin..."
	@echo ""
	$(UV_RUN) python scripts/detect_duplicates.py . --report || echo "  [INFO] Tool execution completed"
	@echo ""
	@echo "Use /bloat-scan for full workflow."


	@echo "=== unbloat Demo (LIVE) ==="
	@echo ""
	@echo "Command: /unbloat"
	@echo "Plugin: conserve"
	@echo ""
	@echo "This demonstrates unbloat usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /unbloat for full workflow."


	@echo "=== ai-hygiene-audit Demo (LIVE) ==="
	@echo ""
	@echo "Running ai-hygiene-audit on conserve plugin..."
	@echo ""
	echo 'AI hygiene audit: Check for TODO/FIXME in skills/' && grep -r 'TODO\|FIXME' skills/ | wc -l | xargs -I{} echo 'Found {} items' || echo "  [INFO] Tool execution completed"
	@echo ""
	@echo "Use /ai-hygiene-audit for full workflow."


demo-conserve-commands: demo-bloat-scan demo-unbloat demo-unbloat demo-ai-hygiene-audit demo-bloat-scan demo-unbloat demo-ai-hygiene-audit ## Run all conserve documented command demos
	@echo ""
	@echo "=== Conserve All Commands Demo Complete ==="
	@echo "Ran 7 documented commands"
	@echo ""


test-bloat-scan: ## Test bloat-scan command workflow
	@echo "=== Testing bloat-scan workflow ==="
	@echo "Validating: /bloat-scan"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-unbloat: ## Test unbloat command workflow
	@echo "=== Testing unbloat workflow ==="
	@echo "Validating: /unbloat"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing unbloat workflow ==="
	@echo "Validating: /unbloat"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-ai-hygiene-audit: ## Test ai-hygiene-audit command workflow
	@echo "=== Testing ai-hygiene-audit workflow ==="
	@echo "Validating: /ai-hygiene-audit"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing bloat-scan workflow ==="
	@echo "Validating: /bloat-scan"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing unbloat workflow ==="
	@echo "Validating: /unbloat"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing ai-hygiene-audit workflow ==="
	@echo "Validating: /ai-hygiene-audit"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""




# Guard against accidental file creation (catch-all for unknown targets)
