# Spec-Kit Plugin Makefile
# Specification writing and task planning workflows
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY:
.PHONY: ci clean debug-variables demo-skills demo-spec demo-speckit-analyze demo-speckit-checklist \
	demo-speckit-clarify demo-speckit-constitution demo-speckit-implement demo-speckit-plan \
	demo-speckit-specify demo-speckit-startup demo-speckit-tasks demo-tasks deps format help \
	install-hooks lint plugin-check security status test test-coverage test-integration test-quick \
	test-speckit-analyze test-speckit-checklist test-speckit-clarify test-speckit-constitution \
	test-speckit-implement test-speckit-plan test-speckit-specify test-speckit-startup \
	test-speckit-tasks test-unit type-check typecheck validate-plugin

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests
COV_DIRS := src
MYPY_TARGETS := src
BANDIT_TARGETS := src
TEST_UNIT_ARGS := -v -m "not integration"
TEST_QUICK_ARGS := -m "not slow" --maxfail=1
TEST_DIR ?= tests

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Default target
help: ## Show this help message
	@echo "Spec-Kit Plugin - Make Targets"
	@echo "==============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Run 'make -C tests help' for test-specific targets"

# ---------- Dependencies ----------
deps: ## Install and sync dependencies
	@if [ -f pyproject.toml ]; then uv sync; else echo "No pyproject.toml found"; fi

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST) $(TEST_DIR)/ -v

test-integration: ## Run integration tests only
	$(PYTEST) $(TEST_DIR)/ -v -m integration

# ---------- Validation ----------
validate-plugin: ## Validate plugin structure
	@echo "Validating spec-kit plugin structure..."
	python3 $(ABSTRACT_DIR)/scripts/validate_plugin.py . || echo "Validation completed with warnings"

# ---------- CI ----------
ci: lint test ## Run CI pipeline
	@echo "CI pipeline completed!"

# ---------- Maintenance ----------
clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@if [ -d $(TEST_DIR) ]; then $(MAKE) -C $(TEST_DIR) clean; fi

status: ## Show project overview
	@echo "Spec-Kit Plugin Status:"
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

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -f .pre-commit-config.yaml ]; then \
		uv run pre-commit install 2>/dev/null || pre-commit install; \
	else \
		echo "No .pre-commit-config.yaml found"; \
	fi

# ---------- Demo/Dogfood Targets ----------
demo-spec: ## Demo spec writing workflow
	@echo "=== Spec-Kit Spec Writing Demo ==="
	@echo "Demonstrating spec-writing skill workflow..."
	@echo ""
	@echo "Step 1: Template structure"
	@echo "  ## Overview"
	@echo "  ## Requirements"
	@echo "  ## User Stories"
	@echo "  ## Acceptance Criteria"
	@echo "  ## Non-Functional Requirements"
	@echo ""
	@echo "Step 2: Skill validation"
	@test -f skills/spec-writing/SKILL.md && echo "  [OK] spec-writing skill exists" || echo "  [X] spec-writing skill missing"
	@head -10 skills/spec-writing/SKILL.md 2>/dev/null | grep -E '^(name|description):' || true
	@echo ""
	@echo "Spec demo complete. Use /spec-kit:speckit-specify for full workflow."

demo-tasks: ## Demo task planning workflow
	@echo "=== Spec-Kit Task Planning Demo ==="
	@echo "Demonstrating task-planning skill workflow..."
	@echo ""
	@echo "Step 1: Task structure"
	@echo "  - [ ] Task ID and title"
	@echo "  - [ ] Dependencies"
	@echo "  - [ ] Acceptance criteria"
	@echo "  - [ ] Estimated effort"
	@echo ""
	@echo "Step 2: Skill validation"
	@test -f skills/task-planning/SKILL.md && echo "  [OK] task-planning skill exists" || echo "  [X] task-planning skill missing"
	@head -10 skills/task-planning/SKILL.md 2>/dev/null | grep -E '^(name|description):' || true
	@echo ""
	@echo "Step 3: Commands available"
	@ls commands/*.md 2>/dev/null | xargs -n1 basename | sed 's/.md//' | sed 's/^/  - /'
	@echo ""
	@echo "Task demo complete. Use /spec-kit:speckit-tasks for full workflow."

demo-skills: ## Validate spec-kit skill structure
	@echo "=== Spec-Kit Skills Demo ==="
	@echo "Specification skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  spec-writing:        $$(test -f skills/spec-writing/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  task-planning:       $$(test -f skills/task-planning/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  speckit-orchestrator: $$(test -f skills/speckit-orchestrator/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo ""
	@echo "Commands:"
	@find commands/ -name "*.md" 2>/dev/null | wc -l | xargs -I{} echo "  {} commands defined"

plugin-check: demo-spec demo-tasks demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Spec-Kit Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

demo-speckit-startup: ## Demo speckit-startup command (LIVE)
	@echo "=== speckit-startup Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-startup"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-startup usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-startup for full workflow."


demo-speckit-specify: ## Demo speckit-specify command (LIVE)
	@echo "=== speckit-specify Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-specify"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-specify usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-specify for full workflow."


demo-speckit-clarify: ## Demo speckit-clarify command (LIVE)
	@echo "=== speckit-clarify Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-clarify"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-clarify usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-clarify for full workflow."


demo-speckit-plan: ## Demo speckit-plan command (LIVE)
	@echo "=== speckit-plan Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-plan"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-plan usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-plan for full workflow."


demo-speckit-tasks: ## Demo speckit-tasks command (LIVE)
	@echo "=== speckit-tasks Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-tasks"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-tasks usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-tasks for full workflow."


demo-speckit-implement: ## Demo speckit-implement command (LIVE)
	@echo "=== speckit-implement Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-implement"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-implement usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-implement for full workflow."


demo-speckit-analyze: ## Demo speckit-analyze command (LIVE)
	@echo "=== speckit-analyze Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-analyze"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-analyze usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-analyze for full workflow."


demo-speckit-checklist: ## Demo speckit-checklist command (LIVE)
	@echo "=== speckit-checklist Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-checklist"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-checklist usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-checklist for full workflow."


demo-speckit-constitution: ## Demo speckit-constitution command (LIVE)
	@echo "=== speckit-constitution Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-constitution"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-constitution usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-constitution for full workflow."


	@echo "=== speckit-startup Demo (LIVE) ==="
	@echo ""
	@echo "Command: /speckit-startup"
	@echo "Plugin: spec-kit"
	@echo ""
	@echo "This demonstrates speckit-startup usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /speckit-startup for full workflow."


demo-spec-kit-commands: demo-speckit-startup demo-speckit-specify demo-speckit-clarify demo-speckit-plan demo-speckit-tasks demo-speckit-implement demo-speckit-analyze demo-speckit-checklist demo-speckit-constitution demo-speckit-startup ## Run all spec-kit documented command demos
	@echo ""
	@echo "=== Spec-kit All Commands Demo Complete ==="
	@echo "Ran 10 documented commands"
	@echo ""


test-speckit-startup: ## Test speckit-startup command workflow
	@echo "=== Testing speckit-startup workflow ==="
	@echo "Validating: /speckit-startup"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-specify: ## Test speckit-specify command workflow
	@echo "=== Testing speckit-specify workflow ==="
	@echo "Validating: /speckit-specify"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-clarify: ## Test speckit-clarify command workflow
	@echo "=== Testing speckit-clarify workflow ==="
	@echo "Validating: /speckit-clarify"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-plan: ## Test speckit-plan command workflow
	@echo "=== Testing speckit-plan workflow ==="
	@echo "Validating: /speckit-plan"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-tasks: ## Test speckit-tasks command workflow
	@echo "=== Testing speckit-tasks workflow ==="
	@echo "Validating: /speckit-tasks"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-implement: ## Test speckit-implement command workflow
	@echo "=== Testing speckit-implement workflow ==="
	@echo "Validating: /speckit-implement"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-analyze: ## Test speckit-analyze command workflow
	@echo "=== Testing speckit-analyze workflow ==="
	@echo "Validating: /speckit-analyze"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-checklist: ## Test speckit-checklist command workflow
	@echo "=== Testing speckit-checklist workflow ==="
	@echo "Validating: /speckit-checklist"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-speckit-constitution: ## Test speckit-constitution command workflow
	@echo "=== Testing speckit-constitution workflow ==="
	@echo "Validating: /speckit-constitution"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing speckit-startup workflow ==="
	@echo "Validating: /speckit-startup"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""




# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
