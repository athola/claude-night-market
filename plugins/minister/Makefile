# Minister Plugin Makefile
# Project and initiative tracking for development workflows
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY:
.PHONY: benchmark ci clean debug-variables demo-close-issue demo-create-issue demo-initiatives \
	demo-skills demo-tracking demo-update-labels deps format help install-hooks lint mutation-test \
	plugin-check security status test test-bdd test-close-issue test-coverage test-create-issue \
	test-integration test-unit test-update-labels type-check typecheck

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests scripts
COV_DIRS := src/minister
MYPY_TARGETS := src/
BANDIT_TARGETS := src/
TEST_UNIT_TARGETS := tests/unit/
TEST_UNIT_ARGS := -v

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Default target
help: ## Show this help message
	@echo "Minister Plugin - Make Targets"
	@echo "==============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Dependencies ----------
deps: ## Install and sync dependencies
	uv sync

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST) tests/ -v

test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ -v

test-bdd: ## Run BDD scenario tests
	$(PYTEST) tests/bdd/ -v

# ---------- CI ----------
ci: lint type-check test ## Run CI pipeline
	@echo "CI pipeline completed!"

# ---------- Maintenance ----------
clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Minister Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Source:   $$(find src/ -name '*.py' 2>/dev/null | wc -l) Python files"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

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

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -f .pre-commit-config.yaml ]; then \
		uv run pre-commit install; \
	else \
		echo "No .pre-commit-config.yaml found"; \
	fi

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate src/minister --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks
	@if $(PYTEST) --benchmark-only --benchmark-sort=mean 2>/dev/null; then \
		echo "Benchmarks complete"; \
	else \
		echo "pytest-benchmark not installed (pip install pytest-benchmark)"; \
	fi

# ---------- Demo/Dogfood Targets ----------
demo-tracking: ## Demo project tracking on minister itself
	@echo "=== Minister Tracking Demo ==="
	@echo "Demonstrating project tracking capabilities..."
	@echo ""
	@echo "Step 1: Project metrics"
	@echo "Python files: $$(find src/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Test files: $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "Data files: $$(find data/ -type f 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 2: Project tracker check"
	@uv run python -c "from minister.project_tracker import *; print('ProjectTracker available')" 2>/dev/null || echo "  (project tracker not loaded)"
	@echo ""
	@echo "Tracking demo complete."

demo-initiatives: ## Demo initiative management
	@echo "=== Minister Initiatives Demo ==="
	@echo "Demonstrating initiative tracking..."
	@echo ""
	@echo "Step 1: Test structure"
	@echo "Unit tests: $$(find tests/unit -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "Integration tests: $$(find tests/integration -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "BDD scenarios: $$(find tests/bdd -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 2: Data directory"
	@ls data/ 2>/dev/null | head -5 || echo "  (no data files)"
	@echo ""
	@echo "Initiatives demo complete."

demo-skills: ## Validate minister skill structure
	@echo "=== Minister Skills Demo ==="
	@echo "Project management skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no skills found)"
	@echo ""
	@echo "Commands:"
	@find commands/ -name "*.md" 2>/dev/null | wc -l | xargs -I{} echo "  {} commands defined"

plugin-check: demo-tracking demo-initiatives demo-skills status ## Run all demo workflows
	@echo ""
	@echo "=== Minister Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

demo-create-issue: ## Demo create-issue command (LIVE)
	@echo "=== create-issue Demo (LIVE) ==="
	@echo ""
	@echo "Command: /create-issue"
	@echo "Plugin: minister"
	@echo ""
	@echo "This demonstrates create-issue usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /create-issue for full workflow."


demo-close-issue: ## Demo close-issue command (LIVE)
	@echo "=== close-issue Demo (LIVE) ==="
	@echo ""
	@echo "Command: /close-issue"
	@echo "Plugin: minister"
	@echo ""
	@echo "This demonstrates close-issue usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /close-issue for full workflow."


demo-update-labels: ## Demo update-labels command (LIVE)
	@echo "=== update-labels Demo (LIVE) ==="
	@echo ""
	@echo "Command: /update-labels"
	@echo "Plugin: minister"
	@echo ""
	@echo "This demonstrates update-labels usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /update-labels for full workflow."


demo-minister-commands: demo-create-issue demo-close-issue demo-update-labels ## Run all minister documented command demos
	@echo ""
	@echo "=== Minister All Commands Demo Complete ==="
	@echo "Ran 3 documented commands"
	@echo ""


test-create-issue: ## Test create-issue command workflow
	@echo "=== Testing create-issue workflow ==="
	@echo "Validating: /create-issue"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-close-issue: ## Test close-issue command workflow
	@echo "=== Testing close-issue workflow ==="
	@echo "Validating: /close-issue"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-update-labels: ## Test update-labels command workflow
	@echo "=== Testing update-labels workflow ==="
	@echo "Validating: /update-labels"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""




# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
