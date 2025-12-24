# Spec-Kit Plugin Makefile
# Specification writing and task planning workflows
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps test test-unit test-integration test-coverage test-quick lint format type-check typecheck \
        security clean status install-hooks ci validate-plugin demo-spec demo-tasks demo-skills plugin-check

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Plugin-specific variables
SRC_DIRS ?= skills commands agents
TEST_DIR ?= tests

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
	$(MAKE) -C $(TEST_DIR) test

test-unit: ## Run unit tests only
	$(MAKE) -C $(TEST_DIR) test-unit

test-integration: ## Run integration tests only
	$(MAKE) -C $(TEST_DIR) test-integration

test-coverage: ## Run tests with coverage report
	$(MAKE) -C $(TEST_DIR) test-coverage

test-quick: ## Run quick tests (skip slow)
	$(MAKE) -C $(TEST_DIR) test-quick

# ---------- Code Quality ----------
lint: ## Run linting checks
	@echo "Linting spec-kit..."
	@if [ -d $(TEST_DIR) ]; then $(MAKE) -C $(TEST_DIR) lint; fi

format: ## Format code
	@echo "Formatting spec-kit..."
	@if [ -d $(TEST_DIR) ]; then $(MAKE) -C $(TEST_DIR) format; fi

type-check: ## Run type checking
	@echo "Type checking not configured for spec-kit (markdown-based plugin)"

# Alias for backwards compatibility
typecheck: type-check

security: ## Run security checks
	@echo "Security checking not configured for spec-kit (markdown-based plugin)"

# ---------- Validation ----------
validate-plugin: ## Validate plugin structure
	@echo "Validating spec-kit plugin structure..."
	python3 $(ABSTRACT_DIR)/scripts/validate-plugin.py . || echo "Validation completed with warnings"

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
	@test -f skills/spec-writing/SKILL.md && echo "  ✓ spec-writing skill exists" || echo "  ✗ spec-writing skill missing"
	@head -10 skills/spec-writing/SKILL.md 2>/dev/null | grep -E '^(name|description):' || true
	@echo ""
	@echo "Spec demo complete. Use /spec-kit:speckit.specify for full workflow."

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
	@test -f skills/task-planning/SKILL.md && echo "  ✓ task-planning skill exists" || echo "  ✗ task-planning skill missing"
	@head -10 skills/task-planning/SKILL.md 2>/dev/null | grep -E '^(name|description):' || true
	@echo ""
	@echo "Step 3: Commands available"
	@ls commands/*.md 2>/dev/null | xargs -n1 basename | sed 's/.md//' | sed 's/^/  - /'
	@echo ""
	@echo "Task demo complete. Use /spec-kit:speckit.tasks for full workflow."

demo-skills: ## Validate spec-kit skill structure
	@echo "=== Spec-Kit Skills Demo ==="
	@echo "Specification skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  spec-writing:        $$(test -f skills/spec-writing/SKILL.md && echo '✓' || echo '✗')"
	@echo "  task-planning:       $$(test -f skills/task-planning/SKILL.md && echo '✓' || echo '✗')"
	@echo "  speckit-orchestrator: $$(test -f skills/speckit-orchestrator/SKILL.md && echo '✓' || echo '✗')"
	@echo ""
	@echo "Commands:"
	@find commands/ -name "*.md" 2>/dev/null | wc -l | xargs -I{} echo "  {} commands defined"

plugin-check: demo-spec demo-tasks demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Spec-Kit Plugin Check Complete ==="
