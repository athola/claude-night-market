# Attune Plugin Makefile
# Project initialization and workflow automation
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help dev-setup test-integration test-verbose \
        clean status debug-variables \
        demo-init demo-brainstorm demo-skills plugin-check

# Plugin-specific variables (must be before include)
SRC_DIRS := scripts tests
RUFF_TARGETS := scripts/ tests/
MYPY_TARGETS := scripts/
BANDIT_TARGETS := scripts/
COV_DIRS := scripts
PYTEST_TARGETS := tests/

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# ---------- Help ----------
help: ## Show this help message
	@echo "Attune Plugin - Make Targets"
	@echo "============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Setup ----------
dev-setup: ## Install development dependencies
	@echo "Installing development dependencies..."
	$(UV) sync --all-extras
	$(UV_RUN) pre-commit install || true

# ---------- Testing ----------
# Note: test, test-unit, test-coverage provided by python.mk include
# Override test-integration since it's not in shared includes
test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	$(PYTEST) $(PYTEST_TARGETS) -v -m integration

test-verbose: ## Run tests with verbose output
	@echo "Running tests with verbose output..."
	$(PYTEST) $(PYTEST_TARGETS) -vv --tb=short

# ---------- Maintenance ----------
clean: ## Clean build artifacts and cache
	@echo "Cleaning build artifacts..."
	rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Attune Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Agents:   $$(find agents/ -name '*.md' 2>/dev/null | wc -l)"
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

# ---------- Demo/Dogfood Targets ----------
demo-init: ## Demo project initialization workflow
	@echo "=== Attune Project Init Demo ==="
	@echo "Demonstrating project-init skill workflow..."
	@echo ""
	@echo "Step 1: Available project templates"
	@echo "  - CLI tool (cli-tool-example.md)"
	@echo "  - Data pipeline (data-pipeline-example.md)"
	@echo "  - Library (library-example.md)"
	@echo "  - Microservices (microservices-example.md)"
	@echo ""
	@echo "Step 2: Skill modules"
	@for module in skills/project-init/modules/*.md; do \
		name=$$(basename "$$module" .md); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no modules found)"
	@echo ""
	@echo "Step 3: Commands available"
	@echo "  /attune:init      - Initialize new project"
	@echo "  /attune:specify   - Create project specification"
	@echo "  /attune:plan      - Generate project plan"
	@echo ""
	@echo "Init demo complete. Use /attune:init to start a new project."

demo-brainstorm: ## Demo brainstorming workflow
	@echo "=== Attune Brainstorm Demo ==="
	@echo "Demonstrating project-brainstorming skill..."
	@echo ""
	@echo "Step 1: Brainstorming phases"
	@echo "  1. Problem definition"
	@echo "  2. Solution exploration"
	@echo "  3. Architecture decisions"
	@echo "  4. Implementation planning"
	@echo ""
	@echo "Step 2: Available agents"
	@for agent in agents/*.md; do \
		name=$$(basename "$$agent" .md); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no agents found)"
	@echo ""
	@echo "Step 3: Integration with other skills"
	@echo "  -> project-specification (output)"
	@echo "  -> project-planning (next step)"
	@echo "  -> project-execution (final step)"
	@echo ""
	@echo "Brainstorm demo complete. Use /attune:brainstorm to start ideation."

demo-skills: ## Validate attune skill structure
	@echo "=== Attune Skills Demo ==="
	@echo "Project workflow skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no skills found)"
	@echo ""
	@echo "Skill coverage:"
	@echo "  project-init:         $$(test -f skills/project-init/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  project-brainstorming: $$(test -f skills/project-brainstorming/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  project-specification: $$(test -f skills/project-specification/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  project-planning:     $$(test -f skills/project-planning/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  project-execution:    $$(test -f skills/project-execution/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  architecture-aware-init: $$(test -f skills/architecture-aware-init/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  makefile-generation:  $$(test -f skills/makefile-generation/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  precommit-setup:      $$(test -f skills/precommit-setup/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  workflow-setup:       $$(test -f skills/workflow-setup/SKILL.md && echo '[OK]' || echo '[X]')"

plugin-check: demo-init demo-brainstorm demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Attune Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Note: catch-all rule removed to allow included targets from python.mk to work
# The %:: double-colon rule was interfering with typecheck, lint, etc.
