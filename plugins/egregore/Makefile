# Egregore Plugin Makefile
# Autonomous agent orchestrator

.PHONY: help deps fix check clean \
	status debug-variables plugin-check demo-skills demo-egregore demo-loop \
	test-egregore test-loop \
	lint format type-check typecheck security test-unit test

# Plugin-specific variables (must be before include)
SRC_DIRS := scripts tests
RUFF_TARGETS := scripts/ tests/
MYPY_TARGETS := scripts/
BANDIT_TARGETS := scripts/
COV_DIRS := scripts
PYTEST_TARGETS := tests/

ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Note: lint, format, type-check, typecheck, security, test-unit,
# test-coverage, test-quick are provided by python.mk

help: ## Show this help message
	@echo "Egregore Plugin - Make Targets"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

deps: ## Install dependencies
	$(UV) sync

fix: ## Auto-fix lint issues
	$(RUFF) check --fix $(RUFF_TARGETS)

test: ## Run tests
	$(PYTEST) $(PYTEST_TARGETS) -v --tb=short

check: lint type-check test ## Run all checks
	@echo "All checks passed!"

clean: ## Clean artifacts
	rm -rf .venv .uv-cache __pycache__ .mypy_cache .pytest_cache

status: ## Show project overview
	@echo "Egregore Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)"
	@echo "Agents:   $$(find agents/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "RUFF_TARGETS: $(RUFF_TARGETS)"
	@echo "MYPY_TARGETS: $(MYPY_TARGETS)"

demo-skills: ## Validate egregore skill structure
	@echo "=== Egregore Skills Demo ==="
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no skills found)"

demo-egregore: ## Demo egregore manifest and work items (LIVE)
	@echo "=== Egregore Orchestrator Demo (LIVE) ==="
	@echo ""
	@echo "Commands:"
	@for cmd in commands/*.md; do \
		name=$$(basename "$$cmd" .md); \
		echo "  /$$name"; \
	done
	@echo ""
	@echo "Agents:"
	@for agent in agents/*.md; do \
		name=$$(basename "$$agent" .md); \
		echo "  $$name"; \
	done 2>/dev/null || echo "  (none)"
	@echo ""
	@echo "Scripts:"
	@find scripts/ -name "*.py" 2>/dev/null | wc -l | xargs -I{} echo "  {} Python scripts"
	@echo ""
	@echo "Use /egregore:summon to start the orchestrator."

demo-loop: ## Demo egregore loop lifecycle (LIVE)
	@echo "=== Egregore Loop Demo (LIVE) ==="
	@echo ""
	@echo "Testing manifest loading..."
	$(UV_RUN) python -c "\
	import json, os; \
	path = '.egregore/manifest.json'; \
	exists = os.path.exists(path); \
	print(f'  Manifest: {\"found\" if exists else \"not found (expected in projects)\"}'); \
	" 2>/dev/null || echo "  Manifest check: skipped (no Python env)"
	@echo ""
	@echo "Test infrastructure:"
	@echo "  Tests: $$(find tests/ -name 'test_*.py' | wc -l) files"
	@echo "  Parallel: $$(grep -l 'parallel' tests/*.py 2>/dev/null | wc -l) test files"
	@echo ""
	@echo "Use /egregore:summon for autonomous operation."

test-egregore: ## Test egregore core functionality
	$(PYTEST) $(PYTEST_TARGETS) -v -k "manifest or specialist or scout" --tb=short

test-loop: ## Test egregore loop and parallel execution
	$(PYTEST) tests/test_parallel.py tests/test_manifest.py -v --tb=short

plugin-check: demo-skills demo-egregore demo-loop status ## Run all demo workflows
	@echo ""
	@echo "=== Egregore Plugin Check Complete ==="

Makefile.local:;
-include Makefile.local

%::
	@echo "Error: Unknown target '$$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
