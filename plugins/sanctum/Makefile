# Sanctum Plugin Makefile
# Git workflow management, commits, and PR preparation
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY:
.PHONY: ci-build ci-test clean debug-variables demo-commit demo-commit-msg demo-create-tag \
	demo-do-issue demo-fix-pr demo-fix-workflow demo-git-catchup demo-git-workspace demo-merge-docs \
	demo-pr demo-pr-prep demo-pr-review demo-prepare-pr demo-rename demo-resolve-threads demo-resume \
	demo-skills demo-update-dependencies demo-update-docs demo-update-plugins demo-update-readme \
	demo-update-tests demo-update-tutorial demo-update-version deps docs format help install \
	install-hooks lint plugin-check profile-test qa quick-check security status test test-all test-bdd \
	test-commit-msg test-cov test-create-tag test-do-issue test-fix-pr test-fix-workflow test-git \
	test-git-catchup test-integration test-merge-docs test-pr test-pr-review test-prepare-pr \
	test-rename test-resolve-threads test-resume test-unit test-update-dependencies test-update-docs \
	test-update-plugins test-update-readme test-update-tests test-update-tutorial test-update-version \
	type-check typecheck watch-test

# Plugin-specific variables
SRC_DIRS ?= src tests
RUFF_TARGETS := .
MYPY_TARGETS := src/
BANDIT_TARGETS := src/
COV_DIRS := src/sanctum
PYTEST_TARGETS := .
TEST_UNIT_ARGS := -m "unit or not integration"

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Prevent parallel execution for targets that share resources
.NOTPARALLEL: docs

# Default target
help: ## Show this help message
	@echo "Sanctum Plugin - Make Targets"
	@echo "=============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile

# ---------- Installation ----------
install: ## Install development dependencies
	uv sync --dev

deps: ## Sync dependencies
	uv sync

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST)

test-integration: ## Run only integration tests
	$(PYTEST) -m "integration"

test-all: ## Run all tests with detailed output
	$(PYTEST) -v --tb=short

test-cov: ## Run tests with coverage report
	$(PYTEST) --cov=src/sanctum --cov-report=term-missing --cov-report=html

test-bdd: ## Run BDD-style tests
	$(PYTEST) -m "bdd" -v

test-git: ## Run Git-related tests
	$(PYTEST) -m "git" -v

# ---------- Code Quality ----------
qa: lint type-check test-cov ## Run all quality assurance checks

# ---------- CI/CD ----------
ci-test: ## Run tests in CI mode
	$(PYTEST) --cov=src/sanctum --cov-report=xml --cov-report=term --junit-xml=junit.xml

ci-build: ## Build package for CI
	uv build

# ---------- Development Helpers ----------
watch-test: ## Watch for changes and run tests
	uv run pytest-watch -- tests/ || echo "pytest-watch not installed"

quick-check: ## Run quick lint and test checks
	@echo "Running quick checks..."
	$(RUFF) check . --quiet
	$(PYTEST) -x -q

profile-test: ## Profile test execution
	$(PYTEST) --profile --profile-svg || echo "pytest-profiling not installed"

docs: ## Generate documentation
	@echo "Documentation is in markdown files in the docs/ directory"

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -f .pre-commit-config.yaml ]; then \
		uv run pre-commit install; \
	else \
		echo "Create .pre-commit-config.yaml first"; \
	fi

# ---------- Maintenance ----------
clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache dist build security-report.json junit.xml 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Sanctum Plugin Status:"
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
demo-commit: ## Demo commit message generation workflow
	@echo "=== Sanctum Commit Demo ==="
	@echo "Demonstrating commit-messages skill workflow..."
	@echo ""
	@echo "Step 1: Gather context"
	@git status --short | head -10 || echo "(no changes)"
	@echo ""
	@echo "Step 2: Analyze changes"
	@git diff --stat HEAD 2>/dev/null | head -10 || echo "(no staged changes)"
	@echo ""
	@echo "Step 3: Generate commit message format"
	@echo "  Type: feat|fix|docs|style|refactor|test|chore"
	@echo "  Scope: (optional component)"
	@echo "  Subject: imperative mood, no period"
	@echo ""
	@echo "Example: feat(skills): add commit message generation"
	@echo ""
	@echo "Commit demo complete. Use /sanctum:commit-msg for full workflow."

demo-pr-prep: ## Demo PR preparation workflow
	@echo "=== Sanctum PR Prep Demo ==="
	@echo "Demonstrating pr-prep skill workflow..."
	@echo ""
	@echo "Step 1: Branch analysis"
	@git rev-parse --abbrev-ref HEAD
	@git log --oneline -5
	@echo ""
	@echo "Step 2: Change summary"
	@git diff --stat HEAD~3..HEAD 2>/dev/null | head -10 || git diff --stat HEAD~1..HEAD
	@echo ""
	@echo "Step 3: PR template structure"
	@echo "  ## Summary"
	@echo "  ## Changes"
	@echo "  ## Test Plan"
	@echo "  ## Checklist"
	@echo ""
	@echo "PR prep demo complete. Use /sanctum:pr for full workflow."

demo-git-workspace: ## Demo git workspace review
	@echo "=== Sanctum Git Workspace Demo ==="
	@echo "Demonstrating git-workspace-review skill..."
	@echo ""
	@echo "Repository state:"
	@git status -sb
	@echo ""
	@echo "Recent activity:"
	@git log --oneline --since="1 week ago" | head -10 || git log --oneline -5
	@echo ""
	@echo "Branches:"
	@git branch -a | head -10
	@echo ""
	@echo "Git workspace demo complete. Use sanctum:git-workspace-review for full analysis."

demo-skills: ## Validate sanctum skill structure
	@echo "=== Sanctum Skills Demo ==="
	@echo "Git workflow skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  commit-messages:     $$(test -f skills/commit-messages/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  pr-prep:             $$(test -f skills/pr-prep/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  git-workspace-review: $$(test -f skills/git-workspace-review/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  doc-updates:         $$(test -f skills/doc-updates/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  version-updates:     $$(test -f skills/version-updates/SKILL.md && echo '[OK]' || echo '[X]')"

plugin-check: demo-commit demo-pr-prep demo-git-workspace demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Sanctum Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

demo-rename: ## Demo rename command (LIVE)
	@echo "=== rename Demo (LIVE) ==="
	@echo ""
	@echo "Command: /rename"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates rename usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /rename for full workflow."


demo-resume: ## Demo resume command (LIVE)
	@echo "=== resume Demo (LIVE) ==="
	@echo ""
	@echo "Command: /resume"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates resume usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /resume for full workflow."


demo-git-catchup: ## Demo git-catchup command (LIVE)
	@echo "=== git-catchup Demo (LIVE) ==="
	@echo ""
	@echo "Command: /git-catchup"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates git-catchup usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /git-catchup for full workflow."


demo-commit-msg: ## Demo commit-msg command (LIVE)
	@echo "=== commit-msg Demo (LIVE) ==="
	@echo ""
	@echo "Running commit-msg on sanctum plugin..."
	@echo ""
	git log --oneline -1 | head -1 || echo 'Commit-msg: Generates conventional commit messages' || echo "  [INFO] Tool execution completed"
	@echo ""
	@echo "Use /commit-msg for full workflow."


demo-do-issue: ## Demo do-issue command (LIVE)
	@echo "=== do-issue Demo (LIVE) ==="
	@echo ""
	@echo "Command: /do-issue"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates do-issue usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /do-issue for full workflow."


demo-fix-workflow: ## Demo fix-workflow command (LIVE)
	@echo "=== fix-workflow Demo (LIVE) ==="
	@echo ""
	@echo "Command: /fix-workflow"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates fix-workflow usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /fix-workflow for full workflow."


demo-fix-pr: ## Demo fix-pr command (LIVE)
	@echo "=== fix-pr Demo (LIVE) ==="
	@echo ""
	@echo "Command: /fix-pr"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates fix-pr usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /fix-pr for full workflow."


demo-pr: ## Demo pr command (LIVE)
	@echo "=== pr Demo (LIVE) ==="
	@echo ""
	@echo "Command: /pr"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates pr usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /pr for full workflow."


demo-update-docs: ## Demo update-docs command (LIVE)
	@echo "=== update-docs Demo (LIVE) ==="
	@echo ""
	@echo "Command: /update-docs"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates update-docs usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /update-docs for full workflow."


demo-update-readme: ## Demo update-readme command (LIVE)
	@echo "=== update-readme Demo (LIVE) ==="
	@echo ""
	@echo "Command: /update-readme"
	@echo "Plugin: sanctum"
	@echo ""
	@echo "This demonstrates update-readme usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /update-readme for full workflow."


demo-sanctum-commands: demo-rename demo-resume demo-git-catchup demo-commit-msg demo-do-issue demo-fix-workflow demo-fix-pr demo-pr demo-update-docs demo-update-readme ## Run all sanctum documented command demos
	@echo ""
	@echo "=== Sanctum All Commands Demo Complete ==="
	@echo "Ran 10 documented commands"
	@echo ""


test-rename: ## Test rename command workflow
	@echo "=== Testing rename workflow ==="
	@echo "Validating: /rename"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-resume: ## Test resume command workflow
	@echo "=== Testing resume workflow ==="
	@echo "Validating: /resume"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-git-catchup: ## Test git-catchup command workflow
	@echo "=== Testing git-catchup workflow ==="
	@echo "Validating: /git-catchup"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-commit-msg: ## Test commit-msg command workflow
	@echo "=== Testing commit-msg workflow ==="
	@echo "Validating: /commit-msg"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-do-issue: ## Test do-issue command workflow
	@echo "=== Testing do-issue workflow ==="
	@echo "Validating: /do-issue"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-fix-workflow: ## Test fix-workflow command workflow
	@echo "=== Testing fix-workflow workflow ==="
	@echo "Validating: /fix-workflow"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-fix-pr: ## Test fix-pr command workflow
	@echo "=== Testing fix-pr workflow ==="
	@echo "Validating: /fix-pr"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-pr: ## Test pr command workflow
	@echo "=== Testing pr workflow ==="
	@echo "Validating: /pr"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-update-docs: ## Test update-docs command workflow
	@echo "=== Testing update-docs workflow ==="
	@echo "Validating: /update-docs"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-update-readme: ## Test update-readme command workflow
	@echo "=== Testing update-readme workflow ==="
	@echo "Validating: /update-readme"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""




# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
